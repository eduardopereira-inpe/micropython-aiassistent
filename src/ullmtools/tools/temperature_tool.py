from .base_tool import CallableTool


class GetTemperatureTool(CallableTool):

    NAME = "get_temperature"

    _SCHEMA = {
        "type": "function",
        "function": {
            "name": "get_temperature",
            "description": (
                "Retorna a temperatura atual "
                "de uma cidade"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": (
                            "Nome da cidade"
                        )
                    }
                },
                "required": [
                    "city"
                ]
            }
        }
    }

    def __call__(
        self,
        city
    ):

        return (
            "28 graus Celsius em {}".format(
                city
            )
        )
