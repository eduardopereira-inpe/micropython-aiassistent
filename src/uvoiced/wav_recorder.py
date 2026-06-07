import time
from .microphonemanager import MicrophoneManager
from .wavheader import write_wav_header

class WavRecorder:
    _NAME = "WavRecorder"
    
    def __init__(self, 
                 microphone_manager: MicrophoneManager, 
                 wav_file_path: str,
                 verbose: bool = False
                 ):
        self.microphone_manager = microphone_manager
        self.wav_file_path = wav_file_path
        self.verbose = verbose

    async def record(self, duration_seconds: float):

        mic = self.microphone_manager.microphone

        if mic is None:
            raise Exception("Microphone unavailable")

        total_pcm_bytes = 0

        with open(self.wav_file_path, "wb") as f:

            if self.verbose:
                print(
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