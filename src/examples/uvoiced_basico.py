import uasyncio as asyncio

from connectivity import connect_to_wifi
from udotenv.dotenv import load_dotenv
from uvoiced import MicrophoneManager, WavRecorder, TranscriberClientManager

WAV_FILE = "test.wav"


async def record_wav(duration_seconds=4):
    mic_manager = MicrophoneManager(
        sample_rate=16000,
        mic_ibuf=16384,
        sck_pin=14,
        ws_pin=13,
        sd_pin=12,
        i2s_id=0,
        verbose=True,
    )

    recorder = WavRecorder(
        microphone_manager=mic_manager,
        wav_file_path=WAV_FILE,
        verbose=True,
    )

    try:
        await recorder.record(duration_seconds=duration_seconds)
    finally:
        mic_manager.release_mic()


def transcribe_wav(api_key):
    transcriber = TranscriberClientManager(
        api_key=api_key,
        verbose=True,
    )

    text = transcriber.transcribing(audio_file_path=WAV_FILE)

    if text:
        print("Transcricao:", text)
    else:
        print("Transcricao vazia.")


async def main():
    config = load_dotenv("env.txt")

    api_key = config.get("API_KEY")
    ssid = config.get("WIFI_SSID")
    password = config.get("WIFI_PASS")

    print("1) Gravando audio...")
    await record_wav(duration_seconds=4)
    print("Arquivo WAV salvo em:", WAV_FILE)

    if not api_key or api_key == "YOUR_OPENAI_API_KEY":
        print("2) API_KEY ausente. Transcricao ignorada.")
        return

    if not ssid or not password:
        print("2) WIFI_SSID/WIFI_PASS ausentes. Transcricao ignorada.")
        return

    print("2) Conectando ao Wi-Fi...")
    connect_to_wifi(ssid, password)

    print("3) Enviando WAV para transcricao...")
    transcribe_wav(api_key)


if __name__ == "__main__":
    asyncio.run(main())
