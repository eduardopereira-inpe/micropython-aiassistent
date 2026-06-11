# MicroPython AI Assistant

<<<<<<< HEAD
A reusable voice assistant framework for ESP32-class boards running MicroPython.

Repository: https://github.com/eduardopereira-inpe/micropython-aiassistent

This project captures audio from an INMP441 microphone, transcribes it with OpenAI, generates a chat response, and renders status/output on an SSD1306 OLED display, with optional buzzer feedback.

## Highlights

- Library-first architecture under `src/assistant`
- Reusable audio/transcription toolkit under `src/uvoiced`
- Domain-oriented package organization (`assistant.llm`, `assistant.display`, etc.)
- Runnable example under `src/examples`
- UI messages externalized in `assistant/ui/messages.json`
- Network and memory diagnostics for constrained MicroPython devices
- Built-in tool-calling support for LLM function execution
- `manifest.py` ready for `mip` packaging workflows
=======
A modular voice assistant framework for ESP32-class boards running MicroPython.

Repository: https://github.com/eduardopereira-inpe/micropython-aiassistent

The project captures audio from an INMP441 microphone, transcribes speech, generates an LLM response, and renders status/output on an SSD1306 OLED display, with optional buzzer feedback and callable runtime tools.

## Highlights

- Modular package layout for reuse across projects.
- Assistant orchestration in `src/assistant`.
- Reusable LLM + tool-calling package in `src/ullmtools`.
- Reusable voice/audio toolkit in `src/uvoiced`.
- Reusable hardware helpers in `src/udisplay`, `src/ubuzzer`, and `src/connectivity`.
- Runnable examples in `src/examples`.
- `manifest.py` included for `mip` packaging.
>>>>>>> c506c1ca3c3608909265889c535259ca9fb35f8d

## Current Repository Structure

```text
src/
  assistant/
    app/
<<<<<<< HEAD
      __init__.py
      application.py
    buzzer/
      __init__.py
      melodies.py
      notes.py
      player.py
    chat/
      __init__.py
      service.py
    display/
      __init__.py
      display_callback.py
      emotion_display.py
      ssd1306.py
    llm/
      __init__.py
      interface.py
      ollama.py
      openai.py
    network/
      __init__.py
      wifi.py
    tools/
      __init__.py
      README.md
      schedule_event.py
      scheduler.py
      schemas.py
      tools.py
=======
>>>>>>> c506c1ca3c3608909265889c535259ca9fb35f8d
    ui/
    utils/
<<<<<<< HEAD
      __init__.py
      asyncinput.py
      dotenv.py
  uvoiced/
    __init__.py
    audio_service.py
    inmp441.py
    microphoneinterface.py
    microphonemanager.py
    stream_client.py
    transcriber_client_manager.py
    transcriber_client_manger_interface.py
    voice_activity_detector.py
    wav_recorder.py
    wavheader.py
=======
    config.py
  connectivity/
    wifi.py
>>>>>>> c506c1ca3c3608909265889c535259ca9fb35f8d
  examples/
    main.py
    samplellm.py
    exemplo_server.py
  ubuzzer/
    melodies.py
    notes.py
    player.py
  udisplay/
    display_callback.py
    emotion_display.py
    ssd1306.py
  udotenv/
    dotenv.py
  ullmtools/
    core/
    tools/
    README.md
  uvoiced/
    audio_service.py
    inmp441.py
    microphoneinterface.py
    microphonemanager.py
    stream_client.py
    transcriber_client_manager.py
    transcriber_client_manger_interface.py
    voice_activity_detector.py
    wav_recorder.py
    wavheader.py

images/
manifest.py
README.md
```

## Hardware

- ESP32 board running MicroPython
- INMP441 I2S microphone
- SSD1306 OLED display (I2C)
- Push button
- Optional passive buzzer

### Circuit Example

[![Circuit Example](./images/circuit_example.jpeg)](./images/circuit_example.jpeg)

### Connection Diagram

[![Connection Diagram](./images/circuit_diagram_example.png)](./images/circuit_diagram_example.png)

### Demo Video

[![Watch the video](https://www.youtube.com/shorts/SIbHdoIIevs)](https://www.youtube.com/shorts/SIbHdoIIevs)

https://github.com/user-attachments/assets/03c58044-3934-4cdb-bfd8-762c81a9f5d3

## Usage Example

```python
import uasyncio as asyncio

from assistant.app.application import AssistantApplication


async def main():
    app = AssistantApplication()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
```

## Software Requirements

MicroPython firmware/modules compatible with:

- `uasyncio`
- `urequests`
- `ujson`
- `machine`
- `network`
- `ssl`
- `socket`

## Setup

### 1) Clone the repository

```bash
git clone https://github.com/eduardopereira-inpe/micropython-aiassistent.git
cd micropython-aiassistent
```

### 2) Create `env.txt` on the device

Create an `env.txt` file at the device root:

```text
API_KEY=your_openai_api_key
WIFI_SSID=your_wifi_name
WIFI_PASS=your_wifi_password
```

`assistant.config` reads this file and exposes:

- `API_KEY`
- `SSID`
- `PASSWORD`

Note: Wi-Fi connection is attempted by `assistant.config` on import.

### 3) Deploy to the board

<<<<<<< HEAD
Copy `src/assistant`, `src/uvoiced`, and `src/examples` to the device filesystem.
=======
Copy required packages and examples to the device filesystem.
>>>>>>> c506c1ca3c3608909265889c535259ca9fb35f8d

Example with `mpremote`:

```bash
mpremote connect auto fs cp -r src/assistant :/
<<<<<<< HEAD
=======
mpremote connect auto fs cp -r src/connectivity :/
mpremote connect auto fs cp -r src/ubuzzer :/
mpremote connect auto fs cp -r src/udisplay :/
mpremote connect auto fs cp -r src/udotenv :/
mpremote connect auto fs cp -r src/ullmtools :/
>>>>>>> c506c1ca3c3608909265889c535259ca9fb35f8d
mpremote connect auto fs cp -r src/uvoiced :/
mpremote connect auto fs cp -r src/examples :/
mpremote connect auto fs cp env.txt :/
```

## Running

### Main assistant application

```bash
mpremote connect auto run src/examples/main.py
```

### LLM + tools sample

```bash
mpremote connect auto run src/examples/samplellm.py
```

## Core Entry Points

- App orchestrator: `assistant.app.application.AssistantApplication`
- UI controller: `assistant.ui.ui.AssistantUI`
- Audio flow: `uvoiced.audio_service.AudioService`
<<<<<<< HEAD
- Chat flow: `assistant.chat.service.ChatService`
- OpenAI chat client: `assistant.llm.openai.OpenAI`
- OpenAI stream transcription client: `uvoiced.stream_client.OpenAIStreamClient`
=======
- Chat flow: `ullmtools.core.chat.chat_service.ChatService`
- OpenAI clients: `ullmtools.core.apis.openai.OpenAI` and `ullmtools.core.apis.openaimtools.OpenAIMTools`
- Ollama client: `ullmtools.core.apis.ollama.Ollama`
>>>>>>> c506c1ca3c3608909265889c535259ca9fb35f8d

## Tool Calling

Tools live in `src/ullmtools/tools`.

For full API, architecture, and examples, see:

<<<<<<< HEAD
1. Create one file per tool in `src/ullmtools/tools/*_tool.py`.
2. Implement one class callable (`__call__`) inheriting from `CallableTool`.
3. Keep `NAME` and `_SCHEMA["function"]["name"]` aligned.
4. Define parameters with `type`, `properties`, and `required`.
5. Keep return payloads compact to respect MicroPython memory constraints.
6. Register instances in `AssistantApplication` with `self.llm.register_tool(tool=my_tool)`.
7. Use `tools=self.llm.get_tools_schema()` in chat calls.

### Minimal example

```python
from ullmtools.tools.base_tool import CallableTool


class GetTemperatureTool(CallableTool):
  NAME = "get_temperature"
  _SCHEMA = {
    "type": "function",
    "function": {
      "name": "get_temperature",
      "description": "Returns the current temperature for a city",
      "parameters": {
        "type": "object",
        "properties": {
          "city": {
            "type": "string",
            "description": "City name"
          }
        },
        "required": ["city"],
        "additionalProperties": False
      }
    }
  }

  def __call__(self, city):
    return "28 degrees Celsius in {}".format(city)
```

### Tool documentation

Detailed documentation for available tools and the creation pattern:

- `src/assistant/tools/README.md`
- `src/ullmtools/tools/README.md`

## Import Convention

Use absolute package imports for internal modules:

```python
from assistant.display.emotion_display import EmotionDisplay
from assistant.llm.openai import OpenAI
from assistant.connectivity.wifi import conectar_wifi
from uvoiced.audio_service import AudioService
```
=======
- `src/ullmtools/README.md`
- `src/ullmtools/tools/README.md`
>>>>>>> c506c1ca3c3608909265889c535259ca9fb35f8d

## Memory and Network Notes (ESP32)

The project includes mitigations for constrained RAM and unstable links:

<<<<<<< HEAD
- Tests were executed with only 142.6 KB of free RAM.
- Running scripts and libraries occupied about 20 KB of RAM (162.6 KB - 142.6 KB).
- TLS/post diagnostics in transcription and chat clients
- Retry strategy for transient socket failures
- I2S mic buffer release before TLS-heavy operations
- Streaming mode that avoids accumulating full chat response in RAM

If issues occur, inspect serial logs with these prefixes:
=======
- Diagnostics in transcription and chat clients.
- Retry strategy for transient socket failures.
- I2S mic buffer release before TLS-heavy operations.
- Streaming flow to reduce response buffering when possible.

If issues occur, inspect serial logs with prefixes such as:
>>>>>>> c506c1ca3c3608909265889c535259ca9fb35f8d

- `[openaistream]`
- `[openai]`
- `[audio]`
- `[wifi]`

Note: audio capture and transcription internals were extracted to `src/uvoiced` for reuse across projects.

## Packaging (mip)

Current `manifest.py`:

```python
metadata(
    version="0.1.0",
    description="MicroPython assistant library",
)

package("assistant", base_path="./src")
```

<<<<<<< HEAD
To package `uvoiced` through `mip` as well, add:

```python
=======
To package additional modules, add entries in `manifest.py`, for example:

```python
package("ullmtools", base_path="./src")
>>>>>>> c506c1ca3c3608909265889c535259ca9fb35f8d
package("uvoiced", base_path="./src")
```

## Status

The project is under active development with a reusable package-first layout and runnable examples for integration testing on embedded hardware.
