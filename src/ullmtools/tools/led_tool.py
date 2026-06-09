from machine import Pin

from .base_tool import CallableTool


class TurnOnOffLedTool(CallableTool):

    NAME = "turn_onoff_led"

    _SCHEMA = {
        "type": "function",
        "function": {
            "name": "turn_onoff_led",
            "description": (
                "Liga ou desliga o LED "
                "conectado ao pino 23."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "value": {
                        "type": "integer",
                        "description": (
                            "0 para desligar "
                            "e 1 para ligar."
                        ),
                        "enum": [
                            0,
                            1
                        ]
                    }
                },
                "required": [
                    "value"
                ],
                "additionalProperties": False
            }
        }
    }

    def __init__(
        self,
        pin=23
    ):

        self.led = Pin(
            pin,
            Pin.OUT
        )

        self.led.value(0)

    def __call__(
        self,
        value
    ):

        value = int(value)

        self.led.value(value)

        if value == 1:
            return "LED ligado"

        return "LED desligado"
