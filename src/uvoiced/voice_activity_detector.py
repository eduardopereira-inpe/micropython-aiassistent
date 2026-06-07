import utime

from .microphonemanager import MicrophoneManager

class VoiceActivityDetector:

    _NMEAN = 5
    _MEAN_THRESHOLD = 0.5
    _NAME = "VoiceActivityDetector"
    _SOUND_TIMEOUT_MS = 1000

    def __init__(
            self, 
            audio_manager: MicrophoneManager, 
            noise_threshold: int = 70, 
            verbose: bool = False
        ):

        self.audio_manager = audio_manager
        self.noise_threshold = noise_threshold
        self._is_above_background = False
        self.verbose = verbose

        self._is_sound_detected = False
        self._last_sound_time = utime.ticks_ms()

    @property
    def is_above_background(self):
        return self._is_sound_detected
  

    def _background_noise_ratio(self):
        mic = self.audio_manager.microphone
        if mic is None:
            raise Exception("Microphone unavailable")
        mic.read_pcm16(record_mode=False)
        return mic.is_above_background        
        

    async def run(self):
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