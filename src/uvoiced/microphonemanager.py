"""Microphone lifecycle manager for INMP441-based audio capture.

This module centralizes lazy microphone creation and safe resource release
to reduce memory pressure on constrained MicroPython devices.
"""

import gc
from .inmp441 import INMP441


class MicrophoneManager:
    """Manage creation and release of a shared INMP441 microphone instance.

    The manager lazily initializes the microphone on first access and keeps a
    single reusable instance until explicitly released.
    """

    _NAME = "MicrophoneManager"

    def __init__(
        self,
        sample_rate: int = 16000,
        mic_ibuf: int = 16384,
        verbose: bool = False
    ) -> None:
        """Initialize microphone manager configuration.

        Args:
            sample_rate: Audio sample rate in Hz used by INMP441.
            mic_ibuf: Internal I2S buffer size in bytes.
            verbose: Enables debug logging when True.
        """

        self.sample_rate = sample_rate
        self.mic_ibuf = mic_ibuf
        self._microphone = None
        self.verbose = verbose

    def _log(self, msg) -> None:
        if self.verbose:
            print(msg)

    @property
    def microphone(self) -> INMP441:
        """Return a ready-to-use microphone instance.

        Creates the microphone lazily on first access.

        Returns:
            An initialized INMP441 instance.
        """

        self._ensure_mic()

        if self._microphone is None:
            raise RuntimeError("Microphone initialization failed")

        return self._microphone

    def _ensure_mic(self) -> None:
        """Ensure the internal microphone instance is initialized."""

        if self._microphone is not None:
            return

        self._microphone = INMP441(
            sample_rate=self.sample_rate,
            sck_pin=32,
            ws_pin=25,
            sd_pin=33,
            i2s_id=0,
            ibuf=self.mic_ibuf
        )

    def release_mic(self) -> None:
        """Release the active microphone instance and reclaim memory.

        This method is safe to call when no microphone instance exists.
        """

        if self._microphone is None:
            return

        try:
            self._microphone.close()
        except Exception:
            self._log(f"[{self._NAME}] Failed to close microphone")

        self._microphone = None
        gc.collect()

    