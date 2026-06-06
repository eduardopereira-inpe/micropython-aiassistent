import uasyncio as asyncio

try:
    import ujson as json
except ImportError:
    import json


class AssistantUI:

    DEFAULT_MESSAGES = {
        "startup": "Assistente iniciado",
        "connecting_wifi": "Conectando WiFi...",
        "idle": "Pergunte Algo!",
        "listening": "Escutando...",
        "recording": "Gravando...",
        "transcribing": "Transcrevendo...",
        "thinking": "Pensando..."
    }

    def __init__(
        self,
        display,
        messages_path="src/assistant/ui/messages.json",
        language="pt-BR"
    ):

        self.display = display
        self.messages = self._load_messages(
            messages_path,
            language
        )

    def _load_messages(
        self,
        messages_path,
        language
    ):

        try:

            with open(messages_path, "r") as f:
                content = json.loads(f.read())

            if (
                isinstance(content, dict) and
                language in content and
                isinstance(content[language], dict)
            ):
                language_messages = content[language]

            elif isinstance(content, dict):
                language_messages = content

            else:
                language_messages = {}

        except Exception:

            language_messages = {}

        return language_messages

    def _message(self, key):

        return self.messages.get(
            key,
            self.DEFAULT_MESSAGES.get(key, "")
        )

    async def start(self):

        asyncio.create_task(
            self.display.run()
        )

    async def wait_message_cycle(self):

        await self.display.wait_message_cycle()

    def startup(self):

        self.display.idle()
        self.display.scroll_x = 0
        self.display.message = self._message("startup")
        

    def connecting_wifi(self):

        self.display.think()
        self.display.scroll_x = 0
        self.display.message = self._message("connecting_wifi")
        

    def idle(self):

        self.display.idle()
        self.display.scroll_x = 0
        self.display.set_message("")

    def listening(self):

        self.display.think()
        self.display.scroll_x = 0
        self.display.message = self._message("listening")
        

    def recording(self):

        self.display.think()
        self.display.scroll_x = 0
        self.display.message = self._message("recording")
        

    def transcribing(self):

        self.display.think()
        self.display.scroll_x = 0
        self.display.message = self._message("transcribing")
        

    def thinking(self):

        self.display.think()
        self.display.scroll_x = 0
        self.display.message = self._message("thinking")
        

    def sleep(self):

        self.display.sleep()
        self.display.set_message(
            self._message("")
        )

    def error(self, message):

        self.display.error()
        self.display.set_message(
            message
        )

    def set_response(self, message):

        self.display.idle()
        self.display.set_message(
            message
        )

    def stop(self):

        self.display.stop()