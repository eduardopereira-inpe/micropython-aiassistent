from .base_tool import CallableTool


class DisplayMessageTool(CallableTool):

    NAME = "show_message"

    _SCHEMA = {
        "type": "function",
        "function": {
            "name": "show_message",
            "description": (
                "Exibe uma mensagem "
                "no display."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string"
                    }
                },
                "required": [
                    "message"
                ],
                "additionalProperties": False
            }
        }
    }

    def __init__(
        self,
        ui,
        player
    ):

        self.ui = ui
        self.player = player

    def __call__(
        self,
        message
    ):

        self.ui.set_response(
            message
        )

        self.player.play(
            [
                "Star Trek intro",
                80,
                "NOTE_D4",
                "-8",
                "NOTE_G4",
                "16",
                "NOTE_C5",
                "-4",
                "NOTE_B4",
                "8",
                "NOTE_G4",
                "-16",
                "NOTE_E4",
                "-16",
                "NOTE_A4",
                "-16",
                "NOTE_D5",
                "2"
            ]
        )

        return "Mensagem exibida."
