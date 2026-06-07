"""Voice activity detection utilities for MicroPython audio capture.

This module provides a lightweight detector that samples microphone
background activity and reports whether sound remains above threshold.
"""

import utime

from .microphonemanager import MicrophoneManager

class VoiceActivityDetector:
    """Detect voice activity using rolling background-noise samples.

    The detector computes a mean ratio over a fixed number of short reads and
    keeps detection state active for a timeout window to smooth transitions.
    """

    _NMEAN = 5
    _MEAN_THRESHOLD = 0.5
    _NAME = "VoiceActivityDetector"
    _SOUND_TIMEOUT_MS = 1000

    def __init__(
            self, 
            audio_manager: MicrophoneManager, 
            noise_threshold: int = 70, 
            verbose: bool = False
        ) -> None:
        """Initialize the voice activity detector.

        Args:
            audio_manager: Microphone manager that provides the active input.
            noise_threshold: Reserved threshold parameter for compatibility.
            verbose: Enables diagnostic logging when True.
        """

        self.audio_manager = audio_manager
        self.noise_threshold = noise_threshold
        self._is_above_background = False
        self.verbose = verbose

        self._is_sound_detected = False
        self._last_sound_time = utime.ticks_ms()

    @property
    def is_above_background(self) -> bool:
        """Return whether sound is currently considered detected.

        Returns:
            True when the detector is in active sound state, otherwise False.
        """

        return self._is_sound_detected
  

    def _background_noise_ratio(self) -> bool:
        """Read one microphone chunk and return background activity state.

        Returns:
            True when the microphone chunk is above background threshold.

        Raises:
            Exception: If the microphone is unavailable.
        """

        mic = self.audio_manager.microphone
        if mic is None:
            raise Exception("Microphone unavailable")
        mic.read_pcm16(record_mode=False)
        return mic.is_above_background        
        

    async def run(self) -> bool:
        """Process activity samples and update detection state.

        Returns:
            True when sound is detected, otherwise False.

        Raises:
            Exception: If the microphone is unavailable.
        """

        mic = self.audio_manager.microphone

        if mic is None:
            raise Exception("Microphone unavailable")
                   
        sound_samp = sum([
            self._background_noise_ratio() 
            for _ in range(self._NMEAN)
        ]) / self._NMEAN

        if self.verbose:
            print(f"[{self._NAME}] Sample Background: {sound_samp}")

        is_above = True if sound_samp > self._MEAN_THRESHOLD else False

        current_time = utime.ticks_ms()

        if is_above:

            self._is_sound_detected = True
            self._last_sound_time = current_time

        else:

            elapsed = utime.ticks_diff(
                current_time,
                self._last_sound_time
            )

            if elapsed > self._SOUND_TIMEOUT_MS:
                self._is_sound_detected = False

        if self.verbose:
            print(
                f"[{self._NAME}] is_above_background ="
                f"{self._is_sound_detected}"
            )

        return self._is_sound_detected