# ullmtools

A lightweight MicroPython-oriented package to connect LLM backends (OpenAI and Ollama) with callable tools for embedded assistants.

The package is designed for constrained devices and simple orchestration:
- Unified chat interface for different LLM providers.
- Function/tool calling support.
- Built-in tools for time, LED control, display output, geolocation, weather, and task scheduling.
- Async scheduler integration for delayed tool execution.

## Package Structure

```text
ullmtools/
  __init__.py
  core/
    apis/
      llminterface.py
      openai.py
      openaimtools.py
      ollama.py
    chat/
      chat_service.py
  tools/
    base_tool.py
    local_time_tool.py
    local_datetime_tool.py
    led_tool.py
    display_message_tool.py
    temperature_tool.py
    lat_lon_tool.py
    weather_tool.py
    schedule_event_tool.py
    scheduler.py
```

## Main Components

### 1. LLM Interface Layer

`LLMInterface` (in `core/apis/llminterface.py`) is the base abstraction that provides:
- Message history management.
- Tool registry (`register_tool`).
- Tool execution (`execute_tool`).
- Tool schema aggregation (`get_tools_schema`).

Concrete providers:
- `OpenAI`: basic OpenAI chat + optional tool handling.
- `OpenAIMTools`: OpenAI client specialized for iterative tool-calling rounds.
- `Ollama`: local Ollama endpoint support (with optional streaming).

### 2. Chat Service

`ChatService` (in `core/chat/chat_service.py`) is a thin async layer that:
- Builds a system prompt.
- Invokes `llm.chat(...)`.
- Streams or forwards response tokens using a callback.

### 3. Tool Layer

All tools inherit from `CallableTool` (`tools/base_tool.py`) and expose:
- `NAME`: canonical tool name.
- `_SCHEMA`: OpenAI-compatible function schema.
- `__call__(...)`: runtime execution logic.

## Public Imports

From package root (`ullmtools`):
- `OpenAI`
- `Ollama`
- `ChatService`
- `LocalDateTimeTool`
- `LocalTimeTool`
- `TurnOnOffLedTool`
- `GetTemperatureTool`
- `DisplayMessageTool`
- `Scheduler`
- `ScheduleEventTool`
- `create_schedule_event_tool`
- `GetLatLonTool`
- `GetWeatherTool`

Note: `OpenAIMTools` is available via `ullmtools.core.apis.openaimtools`.

## Quick Start

### OpenAI with Tool Calling

```python
import uasyncio as asyncio

from ullmtools.core.apis.openaimtools import OpenAIMTools
from ullmtools.tools import (
    Scheduler,
    ScheduleEventTool,
    TurnOnOffLedTool,
    GetWeatherTool,
)


async def main():
    llm = OpenAIMTools(
        api_key="YOUR_OPENAI_KEY",
        model="gpt-4o-mini",
        verbose=True,
    )

    scheduler = Scheduler(tool_executor=llm.execute_tool)
    llm.set_scheduler(scheduler)

    llm.register_tool(tool=ScheduleEventTool(scheduler))
    llm.register_tool(tool=GetWeatherTool())
    llm.register_tool(tool=TurnOnOffLedTool(pin=23))

    asyncio.create_task(scheduler.run())

    result = llm.chat(
        prompt="Turn on the LED in 10 seconds and tell me the weather.",
        system_prompt="You are a concise embedded assistant.",
        tools=llm.get_tools_schema(),
    )

    print(result["response"])


asyncio.run(main())
```

### Ollama Example

```python
from ullmtools import Ollama

llm = Ollama(
    url="http://192.168.137.1",
    port="11434",
    model="gemma4:e2b",
)

result = llm.chat(
    prompt="Say hello in one short sentence.",
    stream=False,
)

print(result["response"])
```

## Built-in Tools

- `get_local_time`: returns local time as `HH:MM:SS`.
- `get_local_datetime`: returns local date-time as `YYYY-MM-DD HH:MM:SS`.
- `turn_onoff_led(value)`: controls GPIO LED state (`0` or `1`).
- `show_message(message)`: updates UI message and plays a notification melody.
- `get_temperature(city)`: returns a fixed sample temperature string.
- `get_lat_lon()`: estimates latitude/longitude using public IP.
- `get_weather()`: fetches current weather from Open-Meteo based on IP location.
- `schedule_event(delay_seconds, tool_name, arguments=None)`: schedules a tool execution.

## Scheduler

`Scheduler` executes deferred tool calls in an async loop (`run`).

Typical integration:
1. Create scheduler with `tool_executor=llm.execute_tool`.
2. Register `ScheduleEventTool(scheduler)` in the LLM tool registry.
3. Start loop with `asyncio.create_task(scheduler.run())`.

## Creating a New Tool

1. Add a new `*_tool.py` file under `tools/`.
2. Create one class inheriting from `CallableTool`.
3. Keep `NAME` identical to `_SCHEMA["function"]["name"]`.
4. Implement `__call__(...)` with compact return payloads.
5. Export the class in `tools/__init__.py`.
6. Register an instance with `llm.register_tool(tool=my_tool)`.

## Runtime Notes

- Target environment is MicroPython (`ujson`, `urequests`, `uasyncio`, `machine`).
- Network-dependent tools require active Wi-Fi connectivity.
- Geolocation and weather tools rely on external HTTP APIs.
- Memory usage is important on embedded hardware; keep tool outputs concise.

## Limitations

- `GetTemperatureTool` currently returns a static mock value.
- Time/date tools use fixed UTC offset constants.
- Some tool descriptions are currently written in Portuguese in schema metadata.

## License

Follow the same license and distribution terms as the parent project.
