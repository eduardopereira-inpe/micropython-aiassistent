"""Interface contract for transcription client managers.

This module defines the expected API for classes that create transcription
clients and perform audio-to-text requests.
"""

class TranscriberClientManagerInterface:
    """Base interface for transcription client manager implementations.

    Subclasses must implement client creation and transcription execution.
    """

    _NAME = "TranscriberClientManager"

    def __init__(self, api_key: str, verbose: bool = False) -> None:
        """Initialize common transcription manager configuration.

        Args:
            api_key: API key used by concrete transcription clients.
            verbose: Enables diagnostic logging when True.
        """

        self.api_key = api_key
        self.verbose = verbose
        self._client = None
        self._attempts = 2

    def create_client(self) -> None:
        """Create an internal transcription client instance.

        Raises:
            NotImplementedError: Always raised by the interface base class.
        """

        raise NotImplementedError("create_client() must be implemented by subclass")
    
    def transcribing(self, audio_file_path: str) -> str:
        """Transcribe an audio file and return the recognized text.

        Args:
            audio_file_path: Path to the audio file to transcribe.

        Returns:
            Transcribed text from the remote transcription service.

        Raises:
            NotImplementedError: Always raised by the interface base class.
        """

        raise NotImplementedError("transcribe() must be implemented by subclass")