"""WAV recording helper for INMP441 microphone streams.

This module provides a high-level recorder that captures PCM16 chunks from an
active microphone and writes a valid WAV file header after recording.
"""

import time
from .microphonemanager import MicrophoneManager
from .wavheader import write_wav_header

class WavRecorder:
    """Record audio from a managed microphone into a WAV file."""

    _NAME = "WavRecorder"
    
    def __init__(
        self,
        microphone_manager: MicrophoneManager,
        wav_file_path: str,
        verbose: bool = False
    ) -> None:
        """Initialize recorder settings.

        Args:
            microphone_manager: Manager that provides the active microphone.
            wav_file_path: Destination WAV file path.
            verbose: Enables diagnostic logging when True.
        """

        self.microphone_manager = microphone_manager
        self.wav_file_path = wav_file_path
        self.verbose = verbose

    def _log(self, msg):
        if self.verbose:
            print(msg)

    async def record(self, duration_seconds: float) -> None:
        """Record microphone audio for a fixed duration.

        The method writes PCM payload first, then rewinds the file and writes
        a proper WAV header with final payload size.

        Args:
            duration_seconds: Recording duration in seconds.

        Raises:
            Exception: If the microphone is unavailable.
        """

        mic = self.microphone_manager.microphone

        if mic is None:
            raise Exception("Microphone unavailable")

        total_pcm_bytes = 0

        with open(self.wav_file_path, "wb") as f:

            self._log(
                f"[{self._NAME}] Recording to {self.wav_file_path}"
                f"for {duration_seconds} seconds..."
            )

            f.seek(44)

            start = time.time()

            while (
                time.time() - start <
                duration_seconds
            ):

                chunk = mic.read_pcm16()

                if chunk:

                    total_pcm_bytes += (
                        f.write(chunk)
                    )

            f.seek(0)

            write_wav_header(
                file=f,
                sample_rate=self.microphone_manager.sample_rate,
                pcm_size=total_pcm_bytes
            )