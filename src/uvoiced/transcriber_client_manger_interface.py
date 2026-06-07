class TranscriberClientManagerInterface:
    _NAME = "TranscriberClientManager"

    def __init__(self, api_key, verbose=False):
        self.api_key = api_key
        self.verbose = verbose
        self._client = None
        self._attempts = 2

    def create_client(self):
        raise NotImplementedError("create_client() must be implemented by subclass")
    
    def transcribing(self, audio_file_path: str) -> str:
        raise NotImplementedError("transcribe() must be implemented by subclass")