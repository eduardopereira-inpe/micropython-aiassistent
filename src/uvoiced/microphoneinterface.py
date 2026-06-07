"""Interface contract for microphone implementations.

This module defines the minimal API expected by audio components that read
PCM16 chunks and expose background-activity state.
"""

class MicrophoneInterface:
    """Base interface for microphone adapters used by uvoiced.

    Concrete implementations must provide chunked PCM16 reads, a background
    activity flag, and resource cleanup.
    """


    @property    
    def is_above_background(self) -> bool:
        """Return whether the most recent audio chunk is above background.

        Returns:
            True when the latest captured chunk is above background threshold.

        Raises:
            NotImplementedError: Always raised by the interface base class.
        """

        raise NotImplementedError("is_above_background must be implemented")
    
    def read_pcm16(self, record_mode: bool = True) -> "memoryview | None":
        """Read and convert one chunk of audio to PCM16.

        Args:
            record_mode: Controls implementation-specific recording/debug mode.

        Returns:
            A memoryview with PCM16 bytes, or None when no data is available.

        Raises:
            NotImplementedError: Always raised by the interface base class.
        """

        raise NotImplementedError("read_pcm16 must be implemented")
    
    def close(self) -> None:
        """Release hardware/software resources held by the microphone.

        Raises:
            NotImplementedError: Always raised by the interface base class.
        """

        raise NotImplementedError("close must be implemented")
    

