import gc
import uasyncio as asyncio
import utime

from assistant.config import (
    API_KEY,
    SSID,
    PASSWORD
)

from assistant.network.wifi import (
    conectar_wifi
)

from assistant.display.emotion_display import (
    EmotionDisplay
)

from assistant.llm.openai import (
    OpenAI
)

from assistant.buzzer.player import (
    BuzzerPlayer
)

from assistant.ui.ui import (
    AssistantUI
)

from assistant.audio.service import (
    AudioService
)

from assistant.chat.service import (
    ChatService
)

from assistant.tools.tools import (
    get_temperature,
    GET_TEMPERATURE_SCHEMA
)



# --------------------------------------------------
# Application
# --------------------------------------------------

class AssistantApplication:

    def __init__(self):

        self.display = (
            EmotionDisplay()
        )

        self.sleep_time = 50

        self._state = "idle"

        self._current_time = (
            utime.time()
        )

        self.ui = AssistantUI(
            self.display
        )

        self.player = BuzzerPlayer(
            buzzer_pin=14,
            volume=600
        )

        self.llm = OpenAI(
            api_key=API_KEY
        )

        # ------------------------------
        # Register Tools
        # ------------------------------

        self.llm.register_tool(
            name="get_temperature",
            func=get_temperature,
            schema=GET_TEMPERATURE_SCHEMA
        )

        self.audio = AudioService(
            api_key=API_KEY,
            ui=self.ui
        )

        self.chat = ChatService(
            llm=self.llm,
            ui=self.ui,
            player=self.player,
            display=self.display
        )

    async def initialize(self):

        await self.ui.start()

        self.ui.startup()

        await asyncio.sleep(1)

        self.ui.connecting_wifi()

        await asyncio.sleep(1)

        conectar_wifi(
            SSID,
            PASSWORD
        )

        self.ui.idle()

    async def run(self):

        await self.initialize()

        while True:

            try:

                question = (
                    await self.audio.listen()
                )

                if not question:

                    await asyncio.sleep_ms(
                        0
                    )

                    if (
                        utime.time()
                        - self._current_time
                        > self.sleep_time
                    ):

                        self.ui.sleep()

                        self._state = (
                            "sleep"
                        )

                    continue

                if (
                    self._state
                    == "sleep"
                ):

                    self.ui.idle()

                    self._state = (
                        "idle"
                    )

                    self._current_time = (
                        utime.time()
                    )

                gc.collect()

                await self.chat.ask(
                    question,
                    tools=self.llm.get_tools_schema()
                )

                self.audio.is_sound_detected = (
                    False
                )

                gc.collect()

            except KeyboardInterrupt:

                print(
                    "\nEncerrando..."
                )

                break

            except Exception as error:

                print(
                    "Erro:",
                    error
                )

                self.ui.error(
                    "Erro na requisicao"
                )

                await asyncio.sleep(
                    2
                )

                gc.collect()

        self.shutdown()

    def shutdown(self):

        try:
            self.display.sleep()
        except:
            pass

        try:
            self.player.stop_song()
        except:
            pass

        try:
            self.ui.stop()
        except:
            pass