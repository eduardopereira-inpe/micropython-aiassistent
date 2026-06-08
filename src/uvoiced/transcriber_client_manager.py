"""Transcription manager built on top of OpenAIStreamClient.

This module provides a retry-enabled manager that uploads WAV files and
extracts the ``text`` field from the transcription HTTP response.
"""

import re
import gc
import time

from .stream_client import OpenAIStreamClient
from .transcriber_client_manger_interface import TranscriberClientManagerInterface

class TranscriberClientManager(TranscriberClientManagerInterface):
    """Manage OpenAI transcription requests with retry logic.

    The manager creates stream clients, sends audio files, and parses the
    resulting response payload to return only the transcription text.
    """

    _NAME = "TranscriberClientManager"

    def __init__(self, api_key: str, verbose: bool = False) -> None:
        """Initialize the transcriber manager.

        Args:
            api_key: OpenAI API key used to authenticate requests.
            verbose: Enables diagnostic logging when True.
        """

        self.api_key = api_key
        self.verbose = verbose
        self._client = None
        self._attempts = 2

    def _log(self, msg) -> None:
        if self.verbose:
            print(msg)

    def create_client(self) -> None:
        """Create and store a new OpenAI stream client instance."""

        self._client = OpenAIStreamClient(
            api_key=self.api_key
        )

    def transcribing(self, audio_file_path: str) -> str:
        """Transcribe an audio file and return recognized text.

        The method retries the full request flow on transient failure:
        connect, upload, and response read.

        Args:
            audio_file_path: Path to the WAV file to be transcribed.

        Returns:
            The transcription text when present, otherwise an empty string.

        Raises:
            Exception: If transcription fails after all retry attempts.
        """

        if self._client is None:
            self.create_client()

        last_error = None

        for attempt in range(2):

            client = OpenAIStreamClient(
                api_key=self.api_key
            )

            try:

                self._log(
                    f"[{self._NAME}] transcribe_attempt={attempt + 1}"
                )

                client.connect()

                client.send_wav_file(
                    audio_file_path
                )

                response = (
                    client.read_response()
                )

                match = re.search(
                    r'"text"\s*:\s*"([^"]*)"',
                    response
                )

                if match:
                    return match.group(1)

                return ""

            except Exception as error:

                last_error = error

                self._log(
                    f"[{self._NAME}] transcribe_error attempt={attempt + 1}, error={error}"
                )

                gc.collect()

                if attempt == 0:

                    sleep_ms = getattr(
                        time,
                        "sleep_ms",
                        None
                    )

                    try:

                        if sleep_ms:
                            sleep_ms(250)
                        else:
                            time.sleep(0.25)

                    except Exception:
                        time.sleep(0.25)

                    continue

                raise

            finally:

                try:
                    client.close()
                except Exception:
                    pass

                gc.collect()

        if last_error:
            raise last_error

        raise Exception(
            "Transcription failed"
        )
        
