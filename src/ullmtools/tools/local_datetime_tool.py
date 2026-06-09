import time

from .base_tool import CallableTool


class LocalDateTimeTool(CallableTool):

    NAME = "get_local_datetime"

    UTC_OFFSET_SECONDS = -3 * 3600

    _SCHEMA = {
        "type": "function",
        "function": {
            "name": "get_local_datetime",
            "description": (
                "Retorna a data e hora "
                "local atual."
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

        now = (
            time.time()
            + self.UTC_OFFSET_SECONDS
        )

        t = time.localtime(now)

        return (
            "{:04d}-{:02d}-{:02d} "
            "{:02d}:{:02d}:{:02d}"
        ).format(
            t[0],
            t[1],
            t[2],
            t[3],
            t[4],
            t[5]
        )
