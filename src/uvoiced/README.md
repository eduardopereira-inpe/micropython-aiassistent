# uvoiced

MicroPython library for audio capture with INMP441 (I2S), WAV recording, and simple voice activity detection (VAD) on ESP32 boards.

This package is designed for memory-constrained hardware and limited CPU, keeping the audio capture hot path conservative.

## Features

- Mono I2S capture with INMP441.
- PCM16 little-endian conversion.
- WAV header generation.
- Microphone instance lifecycle management (create/release).
- Voice activity detection based on mean background-noise samples.
- Ready-to-use WAV recorder.

## Package structure

- `inmp441.py`: INMP441 microphone driver.
- `microphoneinterface.py`: base interface for microphone implementations.
- `microphonemanager.py`: microphone lifecycle manager.
- `voice_activity_detector.py`: voice activity detector.
- `record_wav.py`: high-level WAV recorder.
- `wavheader.py`: WAV header utilities.
- `__init__.py`: public exports.

## Public API

Main import:

```python
from uvoiced import (
    INMP441,
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
- `WavHeader.generate(sample_rate, pcm_size)`: returns a WAV header as bytes.
- `write_wav_header(file, sample_rate, pcm_size)`: writes a WAV header to an open file.

## Quick example: record WAV

```python
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

try:
    recorder.record(duration_seconds=5)
finally:
    manager.release_mic()
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
            detected = await vad.is_sound_detected()
            print("sound_detected:", detected)
            await asyncio.sleep_ms(50)
    finally:
        manager.release_mic()

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

## License

Apache-2.0.
