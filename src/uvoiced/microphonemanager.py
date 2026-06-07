
import gc
from .inmp441 import INMP441


class MicrophoneManager:
    _NAME = "MicrophoneManager"

    def __init__(self, 
                 sample_rate=16000, 
                 mic_ibuf=16384,
                 verbose=False
                 ):
        self.sample_rate = sample_rate
        self.mic_ibuf = mic_ibuf
        self._microphone = None
        self.verbose = verbose

    @property
    def microphone(self):
        self._ensure_mic()
        return self._microphone

    def _ensure_mic(self):
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

    def release_mic(self):
        if self._microphone is None:
            return

        try:
            self._microphone.close()
        except Exception:
            if self.verbose:
                print(f"[{self._NAME}] Failed to close microphone")

        self._microphone = None
        gc.collect()

    