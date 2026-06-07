"""OpenAI audio transcription client for MicroPython.

This module provides :class:`OpenAIStreamClient`, a minimal HTTPS client that
uploads a local WAV file to the OpenAI ``/v1/audio/transcriptions`` endpoint
using ``multipart/form-data`` and returns the raw HTTP response text.

Requirements:
    - A valid OpenAI API key.
    - Network access to ``api.openai.com:443``.
    - A readable WAV file on the device filesystem.

Typical usage::

    API_KEY = "YOUR_OPENAI_API_KEY"
    client = OpenAIStreamClient(api_key=API_KEY)

    print("Connecting...")
    client.connect()

    print("Uploading WAV...")
    client.send_wav_file("test.wav")

    print("Reading response...")
    response = client.read_response()
    print(response)

    client.close()

Notes:
    - ``read_response()`` returns the full HTTP response as a decoded string.
    - The default transcription model is ``gpt-4o-mini-transcribe``.
"""

import gc
import os
import socket
import ssl

class OpenAIStreamClient:
    """Minimal HTTPS client for OpenAI audio transcription uploads.

    This client sends a local WAV file to OpenAI using multipart/form-data and
    reads back the full HTTP response body as a string.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini-transcribe"
    ) -> None:
        """Initialize the streaming transcription client.

        Args:
            api_key: OpenAI API key used for request authorization.
            model: Transcription model name sent in the multipart payload.
        """

        self.api_key = api_key
        self.model = model

        self.host = "api.openai.com"
        self.port = 443

        self.boundary = "----esp32mic"

        self.sock = None

    def _debug_mem(self, stage: str) -> None:
        """Print memory diagnostics when available.

        Args:
            stage: Human-readable label describing the current execution step.
        """

        try:
            print(
                "[openaistream]",
                stage,
                "mem_free=",
                gc.mem_free(),
                "mem_alloc=",
                gc.mem_alloc()
            )
        except Exception:
            print("[openaistream]", stage, "mem_unavailable")

    def _sleep_ms(self, milliseconds: int) -> None:
        """Sleep for a given number of milliseconds.

        Tries ``utime.sleep_ms`` first and falls back to ``time.sleep``.

        Args:
            milliseconds: Delay duration in milliseconds.
        """

        try:
            import utime
            utime.sleep_ms(milliseconds)
            return
        except Exception:
            pass

        try:
            import time
            time.sleep(milliseconds / 1000)
        except Exception:
            pass

    def connect(self) -> None:
        """Open a TLS connection to the OpenAI API host.

        The method resolves DNS, establishes TCP, and upgrades to TLS.
        It includes fallback paths for constrained MicroPython TLS behavior.

        Raises:
            OSError: If TCP/TLS connection setup fails.
            Exception: Propagates unexpected connection errors.
        """

        gc.collect()
        self._debug_mem("connect_start")

        addr = socket.getaddrinfo(
            self.host,
            self.port
        )[0][-1]

        print("[openaistream] resolved_addr=", addr)
        self._debug_mem("after_dns")

        sock = socket.socket()

        self._debug_mem("socket_created")

        sock.connect(addr)

        self._debug_mem("tcp_connected")

        # Try to reduce fragmentation right before TLS handshake,
        # which is the highest-memory step in this flow.
        gc.collect()
        self._debug_mem("before_tls")

        try:

            self.sock = ssl.wrap_socket(
                sock,
                server_hostname=self.host
            )

        except OSError as tls_error:

            # Fallback for low-memory situations: retry TLS without SNI.
            if len(tls_error.args) > 0 and tls_error.args[0] == 12:

                print("[openaistream] tls_enomem_retry_no_sni")
                self._debug_mem("tls_enomem")

                try:
                    sock.close()
                except Exception:
                    pass

                gc.collect()
                self._debug_mem("before_tls_retry")

                sock = socket.socket()
                sock.connect(addr)

                self.sock = ssl.wrap_socket(sock)

            else:
                raise

        except TypeError:

            # Compatibility path for ports that do not support
            # server_hostname in ssl.wrap_socket.
            self.sock = ssl.wrap_socket(sock)

        self._debug_mem("tls_ready")
        print("[openaistream] connect_done")

    def send_wav_file(
        self,
        filename: str
    ) -> None:
        """Upload a WAV file using multipart/form-data.

        Args:
            filename: Path to a local WAV file.

        Raises:
            OSError: If socket write operations fail during upload.
            Exception: Propagates file and runtime errors.
        """

        if self.sock is None:
            raise RuntimeError("Socket is not connected. Call connect() first.")

        sock = self.sock

        self._debug_mem("send_start")

        wav_size = os.stat(filename)[6]

        print("[openaistream] wav_size=", wav_size)

        # multipart start
        part1 = (
            "--" + self.boundary + "\r\n"
            'Content-Disposition: form-data; '
            'name="file"; filename="audio.wav"\r\n'
            "Content-Type: audio/wav\r\n\r\n"
        ).encode()

        # multipart end
        part2 = (
            "\r\n--" + self.boundary + "\r\n"
            'Content-Disposition: form-data; name="model"\r\n\r\n'
            + self.model +
            "\r\n--" + self.boundary + "--\r\n"
        ).encode()

        # exact HTTP body size
        content_length = (
            len(part1) +
            wav_size +
            len(part2)
        )

        print(
            "[openaistream] multipart_bytes start=",
            len(part1),
            "end=",
            len(part2),
            "content_length=",
            content_length
        )

        self._debug_mem("headers_build")

        headers = (
            "POST /v1/audio/transcriptions HTTP/1.1\r\n"
            "Host: api.openai.com\r\n"
            "Authorization: Bearer {}\r\n"
            "Content-Type: multipart/form-data; boundary={}\r\n"
            "Content-Length: {}\r\n"
            "Connection: close\r\n\r\n"
        ).format(
            self.api_key,
            self.boundary,
            content_length
        )

        print("[openaistream] sending_headers")

        try:
            sock.write(headers.encode())
        except OSError as error:
            print("[openaistream] write_error stage=headers error=", error)
            self._debug_mem("write_error_headers")
            raise

        self._debug_mem("headers_sent")

        print("[openaistream] sending_multipart_start")

        try:
            sock.write(part1)
        except OSError as error:
            print("[openaistream] write_error stage=part1 error=", error)
            self._debug_mem("write_error_part1")
            raise

        self._debug_mem("multipart_start_sent")

        print("[openaistream] sending_wav_chunks")

        chunk_count = 0
        sent_bytes = 0

        with open(filename, "rb") as f:

            while True:

                chunk = f.read(1024)

                if not chunk:
                    break

                try:
                    sock.write(chunk)
                except OSError as error:
                    print(
                        "[openaistream] write_error stage=wav_chunk",
                        "chunk=",
                        chunk_count + 1,
                        "sent_bytes=",
                        sent_bytes,
                        "error=",
                        error
                    )
                    self._debug_mem("write_error_wav")
                    raise

                chunk_count += 1
                sent_bytes += len(chunk)

                if chunk_count % 10 == 0:
                    print(
                        "[openaistream] chunks=",
                        chunk_count,
                        "sent_bytes=",
                        sent_bytes
                    )
                    self._debug_mem(
                        "wav_upload_" + str(chunk_count)
                    )

        print("[openaistream] wav_upload_done bytes=", sent_bytes)
        self._debug_mem("before_multipart_end")

        print("[openaistream] sending_multipart_end")

        try:
            sock.write(part2)
        except OSError as error:
            print("[openaistream] write_error stage=part2 error=", error)
            self._debug_mem("write_error_part2")
            raise

        self._debug_mem("send_done")

    def read_response(self) -> str:
        """Read and decode the full HTTP response from the server.

        Returns:
            The decoded HTTP response text.
        """

        if self.sock is None:
            raise RuntimeError("Socket is not connected. Call connect() first.")

        sock = self.sock

        self._debug_mem("read_start")

        response = b""
        read_chunks = 0

        while True:

            try:

                data = sock.read(1024)

                if not data:
                    break

                response += data
                read_chunks += 1

                if read_chunks % 10 == 0:
                    print(
                        "[openaistream] read_chunks=",
                        read_chunks,
                        "response_bytes=",
                        len(response)
                    )
                    self._debug_mem(
                        "read_chunks_" + str(read_chunks)
                    )

            except OSError as e:

                print("[openaistream] socket_read_error:", e)
                self._debug_mem("read_socket_error")

                break

        print("[openaistream] read_done bytes=", len(response))
        self._debug_mem("read_end")

        return response.decode()

    def close(self) -> None:
        """Close the underlying socket and free memory resources."""

        if self.sock:
            self._debug_mem("close_start")
            self.sock.close()
            self.sock = None
            gc.collect()
            print("[openaistream] socket_closed")