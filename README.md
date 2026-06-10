# MicroPython AI Assistant

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

## Current Repository Structure

```text
src/
  assistant/
    app/
    ui/
    utils/
    config.py
  connectivity/
    wifi.py
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

Copy required packages and examples to the device filesystem.

Example with `mpremote`:

```bash
mpremote connect auto fs cp -r src/assistant :/
mpremote connect auto fs cp -r src/connectivity :/
mpremote connect auto fs cp -r src/ubuzzer :/
mpremote connect auto fs cp -r src/udisplay :/
mpremote connect auto fs cp -r src/udotenv :/
mpremote connect auto fs cp -r src/ullmtools :/
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
- Chat flow: `ullmtools.core.chat.chat_service.ChatService`
- OpenAI clients: `ullmtools.core.apis.openai.OpenAI` and `ullmtools.core.apis.openaimtools.OpenAIMTools`
- Ollama client: `ullmtools.core.apis.ollama.Ollama`

## Tool Calling

Tools live in `src/ullmtools/tools`.

For full API, architecture, and examples, see:

- `src/ullmtools/README.md`
- `src/ullmtools/tools/README.md`

## Memory and Network Notes (ESP32)

The project includes mitigations for constrained RAM and unstable links:

- Diagnostics in transcription and chat clients.
- Retry strategy for transient socket failures.
- I2S mic buffer release before TLS-heavy operations.
- Streaming flow to reduce response buffering when possible.

If issues occur, inspect serial logs with prefixes such as:

- `[openaistream]`
- `[openai]`
- `[audio]`
- `[wifi]`

## Packaging (mip)

Current `manifest.py`:

```python
metadata(
    version="0.1.0",
    description="MicroPython assistant library",
)

package("assistant", base_path="./src")
```

To package additional modules, add entries in `manifest.py`, for example:

```python
package("ullmtools", base_path="./src")
package("uvoiced", base_path="./src")
```

## Status

The project is under active development with a reusable package-first layout and runnable examples for integration testing on embedded hardware.
