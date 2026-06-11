import uasyncio as asyncio

from assistant.app.application import (
    AssistantApplication
)


async def main():

    app = AssistantApplication()

    await app.run()


if __name__ == "__main__":
    asyncio.run(main())

