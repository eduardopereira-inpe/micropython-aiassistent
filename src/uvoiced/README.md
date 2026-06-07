# uvoiced

MicroPython toolkit for audio capture and transcription on ESP32 boards.

It includes INMP441 I2S capture, WAV recording, voice activity detection (VAD), and a lightweight OpenAI transcription client designed for memory-constrained MicroPython targets.

## Features

- Mono I2S capture with INMP441.
- PCM16 little-endian conversion.
- WAV header generation.
- Microphone instance lifecycle management (create/release).
- Voice activity detection based on mean background-noise samples.
- Ready-to-use WAV recorder.
- OpenAI audio transcription client over HTTPS.
- High-level audio service that orchestrates detect -> record -> transcribe.

## Package structure

- `inmp441.py`: INMP441 microphone driver.
- `microphoneinterface.py`: base interface for microphone implementations.
- `microphonemanager.py`: microphone lifecycle manager.
- `voice_activity_detector.py`: voice activity detector.
- `wav_recorder.py`: high-level WAV recorder.
- `wavheader.py`: WAV header utilities.
- `stream_client.py`: low-level OpenAI multipart upload client.
- `transcriber_client_manger_interface.py`: transcription manager contract.
- `transcriber_client_manager.py`: retry-enabled transcription manager.
- `audio_service.py`: high-level async audio workflow.
- `__init__.py`: public exports.

## Public API

Main import:

```python
from uvoiced import (
    AudioService,
    AudioServiceUIState,
    INMP441,
    OpenAIStreamClient,
    TranscriberClientManager,
    TranscriberClientManagerInterface,
    write_wav_header,
    WavHeader,
    MicrophoneManager,
    VoiceActivityDetector,
    WavRecorder,
)
```

### Classes and functions

- `INMP441`: raw audio capture and PCM16 conversion.
- `MicrophoneManager`: lazy initialization and safe microphone release.
- `VoiceActivityDetector`: checks whether voice/sound is above background.
- `WavRecorder`: records PCM audio into a WAV file.
- `OpenAIStreamClient`: uploads WAV files and reads transcription HTTP responses.
- `TranscriberClientManager`: wraps retries and extracts text from response payload.
- `AudioService`: high-level async flow for listening, recording, and transcribing.
- `WavHeader.generate(sample_rate, pcm_size)`: returns a WAV header as bytes.
- `write_wav_header(file, sample_rate, pcm_size)`: writes a WAV header to an open file.

## Quick example: record WAV

```python
import uasyncio as asyncio
from uvoiced import MicrophoneManager, WavRecorder

manager = MicrophoneManager(
    sample_rate=16000,
    mic_ibuf=16384,
    verbose=True,
)

recorder = WavRecorder(
    microphone_manager=manager,
    wav_file_path="test.wav",
    verbose=True,
)

async def main():
    try:
        await recorder.record(duration_seconds=5)
    finally:
        manager.release_mic()

asyncio.run(main())
```

## Quick example: detect voice activity

```python
import uasyncio as asyncio
from uvoiced import MicrophoneManager, VoiceActivityDetector

manager = MicrophoneManager(sample_rate=16000, mic_ibuf=16384)
vad = VoiceActivityDetector(audio_manager=manager, verbose=True)

async def main():
    try:
        while True:
            detected = await vad.run()
            print("sound_detected:", detected)
            await asyncio.sleep_ms(50)
    finally:
        manager.release_mic()

asyncio.run(main())
```

## Quick example: transcribe a WAV file

```python
from uvoiced import TranscriberClientManager

API_KEY = "YOUR_OPENAI_API_KEY"

manager = TranscriberClientManager(api_key=API_KEY, verbose=True)
text = manager.transcribing(audio_file_path="test.wav")

print("transcript:", text)
```

## Quick example: high-level audio service

```python
import uasyncio as asyncio
from uvoiced import AudioService

API_KEY = "YOUR_OPENAI_API_KEY"

audio = AudioService(
    api_key=API_KEY,
    record_seconds=5,
    output_file="test.wav",
    verbose=True,
)

async def main():
    while True:
        recorded = await audio.listen()
        if recorded:
            text = await audio.transcribing()
            if text:
                print("transcript:", text)
        await asyncio.sleep_ms(10)

asyncio.run(main())
```

## Default pins (NodeMCU ESP32-WROOM)

The current default configuration uses:

- `sck_pin=32`
- `ws_pin=25`
- `sd_pin=33`
- `i2s_id=0`

## Requirements

- MicroPython with `machine.I2S` support.
- INMP441 microphone connected over I2S.
- Filesystem enabled for writing `*.wav` files.

## Performance notes

- The `read_pcm16` method is timing-sensitive on older ESP32 boards.
- Changes in the inner processing loop can degrade audio quality.
- Avoid extra allocations and aggressive refactoring in the capture hot path.
- Prefer releasing the microphone (`MicrophoneManager.release_mic`) after recording before starting TLS-heavy network operations.

## License

Apache-2.0.
