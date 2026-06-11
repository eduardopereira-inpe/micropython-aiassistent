from time import gmtime

from .base_tool import CallableTool


class LocalTimeTool(CallableTool):

    NAME = "get_local_time"

    UTC_OFFSET = -3

    _SCHEMA = {
        "type": "function",
        "function": {
            "name": "get_local_time",
            "description": (
                "Retorna a hora local atual "
                "no formato HH:MM:SS."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            }
        }
    }

    def __call__(self):

        utc = gmtime()

        hour = (
            utc[3] + self.UTC_OFFSET
        ) % 24

        return (
            "{:02d}:{:02d}:{:02d}".format(
                hour,
                utc[4],
                utc[5]
            )
        )
