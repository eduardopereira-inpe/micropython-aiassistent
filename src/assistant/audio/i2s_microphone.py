import array
import struct
import time
from machine import I2S, Pin


class INMP441Microphone:

    def __init__(
        self,
        sample_rate=16000,
        sck_pin=32,
        ws_pin=25,
        sd_pin=33,
        i2s_id=0,
        ibuf=65536,
        noise_threshold=120, 
    ):
        self.sample_rate = sample_rate
        self.noise_threshold = noise_threshold
        self._is_above_background = False 

        self.audio_in = I2S(
            i2s_id,
            sck=Pin(sck_pin),
            ws=Pin(ws_pin),
            sd=Pin(sd_pin),
            mode=I2S.RX,
            bits=32,
            format=I2S.MONO,
            rate=sample_rate,
            ibuf=ibuf,
        )

        # Buffer bruto vindo do I2S (1024 bytes = 256 amostras de 32-bit)
        self.raw_buffer = bytearray(4096)
        # Buffer PCM16 convertido (512 bytes = 256 amostras de 16-bit)
        self.pcm_buffer = bytearray(2048)

    @property
    def is_above_background(self):
        return self._is_above_background

    def read_pcm16(self, record_mode=True):
        n = self.audio_in.readinto(self.raw_buffer)
        if n <= 0:
            return None

        samples = array.array("i", self.raw_buffer)
        idx = 0

        # Variáveis para calcular a média do volume nesta leitura
        sum_amplitude = 0
        num_samples = len(samples)

        for s in samples:
            # INMP441: 24-bit alinhado à esquerda em frame 32-bit
            val = s >> 16

            # Clipping para 16 bits
            if val > 32767:
                val = 32767
            elif val < -32768:
                val = -32768

            # Somando o valor absoluto para cálculo de volume
            # (evita cancelamento negativo)
            sum_amplitude += abs(val)

            # Little endian para o PCM buffer
            self.pcm_buffer[idx] = val & 0xFF
            self.pcm_buffer[idx + 1] = (val >> 8) & 0xFF
            idx += 2
            
            
        
            # Calcula o nível médio de som deste chunk
        if num_samples > 0:
            current_volume = sum_amplitude / num_samples
            if not record_mode:
                print(f"[audio] Calculating volume... Volume = {current_volume}")
            # Atualiza a variável booleana baseada no limiar (threshold)
            if current_volume > self.noise_threshold and current_volume < 300:
                self._is_above_background = True
        else:
            self._is_above_background = False


        return memoryview(self.pcm_buffer)[:idx]

    def close(self):
        self.audio_in.deinit()


def write_wav_header(
    file,
    sample_rate,
    pcm_size
):

    byte_rate = sample_rate * 2
    block_align = 2

    file.write(b"RIFF")
    file.write(struct.pack("<I", pcm_size + 36))
    file.write(b"WAVE")

    file.write(b"fmt ")
    file.write(struct.pack("<I", 16))
    file.write(struct.pack("<H", 1))
    file.write(struct.pack("<H", 1))

    file.write(struct.pack("<I", sample_rate))

    file.write(struct.pack("<I", byte_rate))

    file.write(struct.pack("<H", block_align))
    file.write(struct.pack("<H", 16))

    file.write(b"data")

    file.write(struct.pack("<I", pcm_size))


if __name__ == "__main__":

    SAMPLE_RATE = 16000
    RECORD_SECONDS = 5

    OUTPUT_FILE = "test.wav"

    mic = INMP441Microphone(

        sample_rate=SAMPLE_RATE,

        sck_pin=32,
        ws_pin=25,
        sd_pin=33
    )

    print("Recording...")

    total_pcm_bytes = 0

    with open(OUTPUT_FILE, "wb") as f:

        # pula cabeçalho WAV
        f.seek(44)

        start = time.time()

        while (
            time.time() - start <
            RECORD_SECONDS
        ):

            chunk = mic.read_pcm16()

            if chunk:

                written = f.write(chunk)

                total_pcm_bytes += written

        # volta para escrever cabeçalho WAV
        f.seek(0)

        write_wav_header(
            file=f,
            sample_rate=SAMPLE_RATE,
            pcm_size=total_pcm_bytes
        )

    mic.close()

    print("Done.")

    print("PCM bytes:", total_pcm_bytes)

    print("Saved:", OUTPUT_FILE)