"""Audio capture and transcription service for the assistant.

This module coordinates voice activity detection, WAV recording, and
OpenAI-based transcription for constrained MicroPython devices.
"""
import uasyncio as asyncio

from machine import Pin
import uos

from uvoiced import (
    VoiceActivityDetector,
    MicrophoneManager,
    WavRecorder
)


from .transcriber_client_manager import (
    TranscriberClientManager
)

USE_SOUND_DETECTED = True

class AudioServiceUIState:
    """UI-oriented states used by AudioService during the audio flow."""

    IDLE = 1
    LISTENING = 2
    TRANSCRIBING = 3

class AudioService:
    """High-level audio pipeline for wake detection, recording, and ASR.

    The service is responsible for:
    - Monitoring sound activity and/or button input.
    - Recording microphone audio into a WAV file.
    - Sending the recorded file to the transcription client.
    - Exposing state transitions for UI synchronization.
    """

    _NAME = "AudioService"

    def __init__(
        self,
        api_key: str,
        button_pin: int = 4,
        record_seconds: float = 5,
        output_file: str = "test.wav",
        mic_ibuf: int = 16384,
        sample_rate=16000 // 2, 
        sck_pin: int = 32,
        ws_pin: int = 25,
        sd_pin: int = 33,
        i2s_id: int = 0,
        delete_wav_after_transcription: bool = True,
        verbose: bool = False
    ) -> None:
        """Initialize the audio service dependencies and runtime state.

        Args:
            api_key: OpenAI API key used by the transcription client.
            button_pin: GPIO pin used as manual recording trigger.
            record_seconds: Recording duration in seconds.
            output_file: Path to the temporary WAV output file.
            mic_ibuf: Internal microphone buffer size in bytes.
            sample_rate: Audio capture sample rate in Hz used by the microphone manager.
            sck_pin: I2S serial clock (SCK/BCLK) pin.
            ws_pin: I2S word select (WS/LRCLK) pin.
            sd_pin: I2S serial data input pin.
            i2s_id: I2S peripheral id.
            delete_wav_after_transcription: Whether to delete the WAV file after transcription.
            verbose: Enables diagnostic logging when True.
        """

        self.api_key = api_key

        self.verbose = verbose
        self.delete_wav_after_transcription = delete_wav_after_transcription

        self.microphone_manager = MicrophoneManager(
            sample_rate=sample_rate, 
            verbose=verbose,
            mic_ibuf=mic_ibuf,
            sck_pin=sck_pin,
            ws_pin=ws_pin,
            sd_pin=sd_pin,
            i2s_id=i2s_id,
        )

        self.voice_activity_detector = VoiceActivityDetector(
            audio_manager=self.microphone_manager,
            noise_threshold=100,
            verbose=verbose
        )

        self.wav_recorder = WavRecorder(
            microphone_manager=self.microphone_manager,
            wav_file_path=output_file,
            verbose=verbose
        )

        self.transcriber_client_manager = TranscriberClientManager(
            api_key=api_key,
            verbose=verbose
        )

        self.record_seconds = record_seconds
        self.output_file = output_file
        
        self.button = Pin(
            button_pin,
            Pin.IN,
            Pin.PULL_UP
        )

        self.audio_service_state = AudioServiceUIState.IDLE

    def _log(self, msg):
        if self.verbose:
            print(msg)


    def _transcribe_wav(self) -> str:
        """Transcribe the previously recorded WAV file.

        Uses a retry strategy with up to two attempts to handle transient
        network/socket failures.

        Returns:
            The transcribed text. Returns an empty string when no text is
            present in the response payload.

        Raises:
            Exception: If transcription fails after all retry attempts.
        """
        self.audio_service_state = AudioServiceUIState.TRANSCRIBING
        text = self.transcriber_client_manager.transcribing(
            audio_file_path=self.output_file
        )

        return text

        
    
    async def transcribing(self) -> "str | None":
        """Execute asynchronous transcription flow.

        The method transitions the service to the transcribing state,
        executes WAV transcription, and returns recognized text when
        available.

        Returns:
            The transcribed text when available, otherwise None.
        """

        self._log(f"[{self._NAME}] Starting async transcription")

        if self.audio_service_state != AudioServiceUIState.TRANSCRIBING:
            self.audio_service_state = AudioServiceUIState.TRANSCRIBING
            text = self._transcribe_wav()

            await asyncio.sleep_ms(10)            

            self._log(f"[{self._NAME}] Texto gerado: {text} {text == ''}")

            if text:
                self.audio_service_state = AudioServiceUIState.IDLE
                if self.delete_wav_after_transcription:
                    try:
                        uos.remove(self.output_file)
                        await asyncio.sleep_ms(10)
                    except Exception as e:
                        self._log(f"[{self._NAME}] Failed to delete WAV file: {e}")

                return text


    async def listen(self) -> bool:
        """Listen for wake conditions and record audio when triggered.

        Trigger conditions:
        - Voice activity detector reports background threshold exceeded.
        - Manual button press is detected.

        Returns:
            True when audio was recorded, otherwise False.
        """

        await self.voice_activity_detector.run()
        
        is_button_pressed = self.button.value() == 0

        self._log(f"[{self._NAME}] is_button_pressed = {is_button_pressed}")

        if (self.voice_activity_detector.is_above_background and USE_SOUND_DETECTED) or is_button_pressed:   

            self.audio_service_state = AudioServiceUIState.LISTENING

            await asyncio.sleep_ms(10)

            await self.wav_recorder.record(
                duration_seconds=self.record_seconds
            )

            self.microphone_manager.release_mic()

            self.audio_service_state = AudioServiceUIState.IDLE

            await asyncio.sleep_ms(10)
            return True  

        self.audio_service_state = AudioServiceUIState.IDLE
        return False
          

        
   