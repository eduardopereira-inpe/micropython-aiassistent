import re
import gc
import time

from .stream_client import OpenAIStreamClient
from .transcriber_client_manger_interface import TranscriberClientManagerInterface

class TranscriberClientManager(TranscriberClientManagerInterface):
    _NAME = "TranscriberClientManager"

    def __init__(self, api_key, verbose=False):

        self.api_key = api_key
        self.verbose = verbose
        self._client = None
        self._attempts = 2

    def create_client(self):

        self._client = OpenAIStreamClient(
            api_key=self.api_key
        )

    def transcribing(self, audio_file_path):

        if self._client is None:
            self.create_client()

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
                    audio_file_path
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
        
