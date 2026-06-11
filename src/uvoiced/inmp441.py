# SPDX-License-Identifier: Apache-2.0

"""
I2S microphone capture utilities for the INMP441 on MicroPython.

Target hardware
---------------
- Board: NodeMCU with ESP32-WROOM
- Runtime: MicroPython
- Microphone: INMP441 over I2S

Hardware and runtime limitations
--------------------------------
- This target is an older and resource-constrained ESP32 board.
- CPU time, RAM, and I/O throughput are limited compared to desktop Python
    or newer microcontrollers.
- In this environment, the audio capture loop is timing-sensitive. Small
    structural changes in the hot path may change the behavior even when the
    high-level logic looks equivalent.
- Extra method calls, additional allocations, repeated buffer conversions, or
    partial-read recovery logic inside the per-sample path can introduce audible
    artifacts such as robotic voice, chopped audio, echo-like effects, or faster
    playback.

Experiment notes
----------------
- The original implementation produced the most reliable audio on this board.
- Attempts to "clean up" or optimize the per-sample loop changed the runtime
    characteristics enough to degrade the recording quality.
- Refactorings that added helper calls inside the sample-processing loop, or
    changed how raw I2S bytes were rebuilt into samples, caused regressions even
    when the mathematical intent remained the same.
- For this reason, `read_pcm16` should be treated as a hardware-validated hot
    path. Prefer conservative changes and validate on the physical device after
    every modification.

Maintenance guidance
--------------------
- Prefer readability improvements around the hot path rather than inside it.
- Avoid changing buffer strategy, sample conversion order, or I2S read timing
    unless the change is backed by device testing.
- If experimentation is needed, keep a known-good version available for quick
    rollback.
"""

import array
import struct
import time
from machine import I2S, Pin


from .microphoneinterface import MicrophoneInterface

class INMP441(MicrophoneInterface):
    """Capture mono audio from an INMP441 microphone over I2S.

    This implementation is tuned for MicroPython running on an older
    NodeMCU ESP32-WROOM board. The `read_pcm16` method is timing-sensitive
    and should be changed conservatively.

    Args:
        sample_rate: Target I2S sample rate in Hz.
        sck_pin: GPIO used for the I2S serial clock.
        ws_pin: GPIO used for the I2S word select signal.
        sd_pin: GPIO used for the I2S serial data line.
        i2s_id: MicroPython I2S peripheral identifier.
        ibuf: Internal I2S driver buffer size in bytes.
        noise_threshold: RMS threshold used to flag audio above the
            background level.
        offset: Offset applied while updating the DC estimate.

    Attributes:
        sample_rate: Configured I2S sample rate in Hz.
        noise_threshold: RMS threshold for background detection.
        offset: Offset applied during DC compensation.
    """

    _MAX_SIGNAL_LEVEL = 1000
    _GAIN_COMPENSATION_BITS = 16

    def __init__(
        self,
        sample_rate=16000,
        sck_pin=32,
        ws_pin=25,
        sd_pin=33,
        i2s_id=0,
        ibuf=65536,
        noise_threshold=70,
        offset=240
    ):
        self.sample_rate = sample_rate
        self.noise_threshold = noise_threshold
        self.offset = offset
        self._is_above_background = False

        self.audio_in = I2S(
            i2s_id,
            sck=Pin(sck_pin),
            ws=Pin(ws_pin),
            sd=Pin(sd_pin),
            mode=I2S.RX,
            bits=32,
            format=I2S.MONO,
            rate=sample_rate,
            ibuf=ibuf,
        )

        # Raw bytes from I2S (4096 bytes = 1024 samples of 32-bit each)
        self.raw_buffer = bytearray(4096)

        # Converted PCM16 output (2048 bytes = 1024 samples of 16-bit each)
        self.pcm_buffer = bytearray(2048)

        self._dc_estimate = 0

    @property
    def is_above_background(self):
        """Return whether the latest chunk is above the background threshold.

        Returns:
            bool: True when the last processed chunk exceeded the configured
                noise threshold and stayed below the maximum signal guard.
        """
        return self._is_above_background

    def read_pcm16(self, record_mode=True):
        """Read one I2S chunk and convert it to PCM16 little-endian audio.

        The method reads raw I2S samples, converts them to signed 16-bit PCM,
        updates the background-noise state, and returns a view over the shared
        PCM buffer.

        Args:
            record_mode: When False, prints the current volume estimate for
                debugging.

        Returns:
            memoryview | None: A view containing the converted PCM16 bytes, or
                None when no bytes were read from the I2S device.
        """
        bytes_read = self.audio_in.readinto(self.raw_buffer)

        if bytes_read <= 0:
            return None

        samples = array.array("i", self.raw_buffer)
        idx = 0
        sum_sq = 0
        sample_count = len(samples)

        for sample in samples:
            value = sample >> self._GAIN_COMPENSATION_BITS

            if value > 32767:
                value = 32767
            elif value < -32768:
                value = -32768

            self._dc_estimate += (
                value - self._dc_estimate + self.offset
            ) >> 8

            filtered = value - self._dc_estimate
            sum_sq += filtered * filtered

            self.pcm_buffer[idx] = filtered & 0xFF
            self.pcm_buffer[idx + 1] = (filtered >> 8) & 0xFF
            idx += 2

        if sample_count > 0:
            rms = (sum_sq / sample_count) ** 0.5
            current_volume = int(rms)

            if not record_mode:
                print(
                    f"[audio] Calculating volume... Volume = {current_volume}"
                )

            if (
                current_volume > self.noise_threshold and
                current_volume < self._MAX_SIGNAL_LEVEL
            ):
                self._is_above_background = True
            else:
                self._is_above_background = False
        else:
            self._is_above_background = False
            
        
#         median_val = calculate_median(filtered_samples)
#         print(f"[MIC] median: {median_val}")


        return memoryview(self.pcm_buffer)[:idx]

    def close(self):
        """Release the underlying I2S peripheral."""
        self.audio_in.deinit()

