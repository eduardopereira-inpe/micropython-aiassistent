import uasyncio as asyncio
import time


class Scheduler:

    def __init__(
        self,
        tool_executor
    ):

        self._tasks = []

        self._tool_executor = (
            tool_executor
        )

    def schedule_tool(
        self,
        tool_name,
        delay_seconds,
        arguments=None
    ):

        if arguments is None:
            arguments = {}

        self._tasks.append({

            "execute_at":
                time.time() +
                delay_seconds,

            "tool_name":
                tool_name,

            "arguments":
                arguments
        })

        return True

    async def run(self):

        while True:

            now = time.time()

            for task in self._tasks[:]:

                if (
                    now >=
                    task["execute_at"]
                ):

                    try:

                        self._tool_executor(
                            task[
                                "tool_name"
                            ],
                            task[
                                "arguments"
                            ]
                        )

                    except Exception as e:

                        print(
                            "[scheduler]",
                            e
                        )

                    self._tasks.remove(
                        task
                    )

            await asyncio.sleep(1)

    def list_tasks(self):

        return self._tasks