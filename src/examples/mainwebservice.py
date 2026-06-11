from assistant.app.webapp import main

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

if __name__ == "__main__":
    asyncio.run(main())