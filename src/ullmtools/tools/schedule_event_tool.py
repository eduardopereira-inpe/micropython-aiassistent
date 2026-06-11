from .base_tool import CallableTool


class ScheduleEventTool(CallableTool):

    NAME = "schedule_event"

    _SCHEMA = {
        "type": "function",
        "function": {
            "name": "schedule_event",
            "description": (
                "Agenda a execucao "
                "de uma ferramenta "
                "no futuro."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "delay_seconds": {
                        "type": "integer",
                        "description": "Tempo de espera em segundos."
                    },
                    "tool_name": {
                        "type": "string",
                        "description": "Nome exato da ferramenta."
                    },
                    "arguments": {
                        "type": "object",
                        "description": "Argumentos da ferramenta."
                    }
                },
                "required": [
                    "delay_seconds",
                    "tool_name"
                ],
                "additionalProperties": False
            }
        }
    }

    def __init__(
        self,
        scheduler, 
        verbose=False
    ):

        self.scheduler = scheduler
        self.verbose = verbose

    def _log(self, message):

        if self.verbose:
            print(message)

    def __call__(
        self,
        delay_seconds,
        tool_name,
        arguments=None
    ):

        self.scheduler.schedule_tool(
            tool_name,
            delay_seconds,
            arguments
        )
        self._log(f"[{self.NAME}] Tarefa agendada para : {tool_name}")

        return "Evento agendado."


def create_schedule_event_tool(
    scheduler
):
    return ScheduleEventTool(
        scheduler
    )
