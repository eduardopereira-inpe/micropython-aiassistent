import gc
import re
import time
import uasyncio as asyncio
import utime
from enum import Enum, auto

from machine import Pin

from uvoiced import (
    VoiceActivityDetector,
    MicrophoneManager,
    WavRecorder
)

from assistant.audio.config import (
    SAMPLE_RATE
)

from assistant.llm.stream_client import (
    OpenAIStreamClient
)

USE_SOUND_DETECTED = True

class AudioServiceUIState(Enum):
    IDLE = 1
    LISTENING = 2
    TRANSCRIBING = 3

class AudioService:

    _NAME = "AudioService"

    def __init__(
        self,
        api_key,
        button_pin=4,
        record_seconds=5,
        output_file="test.wav",
        mic_ibuf=16384,
        verbose=False
    ):

        self.api_key = api_key

        self.verbose = verbose

        self.microphone_manager = MicrophoneManager(
            sample_rate=SAMPLE_RATE, 
            verbose=verbose,
            mic_ibuf=mic_ibuf
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

        self.record_seconds = record_seconds
        self.output_file = output_file
        
        self.button = Pin(
            button_pin,
            Pin.IN,
            Pin.PULL_UP
        )

        self.ui_state = AudioServiceUIState.IDLE

    def transcribe_wav(self):

        gc.collect()

        self.ui_state = AudioServiceUIState.TRANSCRIBING

        last_error = None

        for attempt in range(2):

            client = OpenAIStreamClient(
                api_key=self.api_key
            )

            try:

                print(
                    f"[{self._NAME}] transcribe_attempt={attempt + 1}"
                )

                client.connect()

                client.send_wav_file(
                    self.output_file
                )

                response = (
                    client.read_response()
                )

                match = re.search(
                    r'"text"\s*:\s*"([^"]*)"',
                    response
                )

                if match:
                    return match.group(1)

                return ""

            except Exception as error:

                last_error = error

                if self.verbose:

                    print(
                        f"[{self._NAME}] transcribe_error attempt={attempt + 1}, error={error}"
                    )

                gc.collect()

                if attempt == 0:

                    sleep_ms = getattr(
                        time,
                        "sleep_ms",
                        None
                    )

                    try:

                        if sleep_ms:
                            sleep_ms(250)
                        else:
                            time.sleep(0.25)

                    except Exception:
                        time.sleep(0.25)

                    continue

                raise

            finally:

                try:
                    client.close()
                except Exception:
                    pass

                gc.collect()

        if last_error:
            raise last_error

        raise Exception(
            "Transcription failed"
        )

    async def listen(self):

        await self.voice_activity_detector.run()
        
        is_button_pressed = self.button.value() == 0

        if self.verbose:
            print(f"[{self._NAME}] is_button_pressed = {is_button_pressed}")

        if (self.voice_activity_detector.is_above_background and USE_SOUND_DETECTED) or is_button_pressed:   

            self.ui_state = AudioServiceUIState.LISTENING

            await asyncio.sleep_ms(10)

            await self.wav_recorder.record(
                duration_seconds=self.record_seconds
            )

            self.microphone_manager.release_mic()

            text = self.transcribe_wav()

            self.ui_state = AudioServiceUIState.IDLE

            if self.verbose:            
                print(f"[{self._NAME}] Texto gerado: {text} {text == ''}")

            if text:
                return text

        return None