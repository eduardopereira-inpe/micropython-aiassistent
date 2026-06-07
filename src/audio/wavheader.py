# SPDX-License-Identifier: Apache-2.0

import struct


class WavHeader:
    """Utility class for generating PCM WAV headers."""

    @staticmethod
    def generate(
        sample_rate,
        pcm_size
    ):
        """Generate a WAV header as bytes.

        Args:
            sample_rate: Audio sample rate in Hz.
            pcm_size: PCM payload size in bytes.

        Returns:
            bytes: A valid 44-byte PCM WAV header.
        """

        byte_rate = sample_rate * 2
        block_align = 2

        header = b""

        header += b"RIFF"
        header += struct.pack("<I", pcm_size + 36)
        header += b"WAVE"

        header += b"fmt "
        header += struct.pack("<I", 16)
        header += struct.pack("<H", 1)
        header += struct.pack("<H", 1)

        header += struct.pack("<I", sample_rate)

        header += struct.pack("<I", byte_rate)

        header += struct.pack("<H", block_align)
        header += struct.pack("<H", 16)

        header += b"data"

        header += struct.pack("<I", pcm_size)

        return header


def write_wav_header(
    file,
    sample_rate,
    pcm_size
):
    """Write a PCM WAV header to an already opened file.

    Args:
        file: File-like object opened in binary write mode.
        sample_rate: Audio sample rate in Hz.
        pcm_size: PCM payload size in bytes.
    """

    byte_rate = sample_rate * 2
    block_align = 2

    file.write(b"RIFF")
    file.write(struct.pack("<I", pcm_size + 36))
    file.write(b"WAVE")

    file.write(b"fmt ")
    file.write(struct.pack("<I", 16))
    file.write(struct.pack("<H", 1))
    file.write(struct.pack("<H", 1))

    file.write(struct.pack("<I", sample_rate))

    file.write(struct.pack("<I", byte_rate))

    file.write(struct.pack("<H", block_align))
    file.write(struct.pack("<H", 16))

    file.write(b"data")

    file.write(struct.pack("<I", pcm_size))
