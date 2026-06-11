import uasyncio as asyncio

from machine import Pin, PWM

from .notes import notes


class BuzzerPlayer:
    """Async PWM buzzer player."""

    def __init__(
        self,
        buzzer_pin: int = 14,
        volume: int = 600,
    ) -> None:

        self.buzzer = PWM(Pin(buzzer_pin))

        self.volume = volume

        self.current_task = None

        self.stop()

    # =====================================================
    # Basic Controls
    # =====================================================

    def play_tone(self, frequency: int) -> None:

        self.buzzer.freq(frequency)

        self.buzzer.duty_u16(self.volume)

    def stop(self) -> None:

        self.buzzer.duty_u16(0)

    def deinit(self) -> None:

        self.stop()

        self.buzzer.deinit()

    # =====================================================
    # Helpers
    # =====================================================

    @staticmethod
    def calculate_duration(
        tempo: int,
        note_type: int
    ) -> float:

        whole_note = (60000 / tempo) * 4

        if note_type > 0:

            note_duration = whole_note // note_type

        else:

            # dotted note
            note_duration = whole_note // abs(note_type)

            note_duration *= 1.5

        return note_duration

    # =====================================================
    # Async Song Player
    # =====================================================

    async def play_async(
        self,
        song: list
    ) -> None:

        try:

            print(song[0])

            tempo = song[1]

            for index in range(2, len(song), 2):

                note = song[index]

                note_type = int(song[index + 1])

                note_duration = self.calculate_duration(
                    tempo,
                    note_type,
                )

                if note == "REST":

                    self.stop()

                else:

                    self.play_tone(
                        notes[note]
                    )

                # play note for 90%
                await asyncio.sleep_ms(
                    int(note_duration * 0.9)
                )

                # short pause
                self.stop()

                await asyncio.sleep_ms(
                    int(note_duration * 0.1)
                )

        except asyncio.CancelledError:

            self.stop()

            raise

        except Exception:

            self.stop()

            raise

        finally:

            self.stop()

    # =====================================================
    # Background Playback
    # =====================================================

    def play(
        self,
        song: list
    ) -> None:

        self.stop_song()

        self.current_task = asyncio.create_task(
            self.play_async(song)
        )

    def stop_song(self) -> None:

        if self.current_task:

            self.current_task.cancel()

            self.current_task = None

        self.stop()

    def is_playing(self) -> bool:

        if not self.current_task:
            return False

        return not self.current_task.done()


# =========================================================
# Example
# =========================================================

if __name__ == "__main__":

    from melodies import silent_night, star_trek_intro


    async def main():

        player = BuzzerPlayer()

        print("Background playback")

        player.play(star_trek_intro)

        while player.is_playing():

            print("playing...")

            await asyncio.sleep(1)

        print("done")

        await asyncio.sleep(1)

        print("Await playback")

        await player.play_async(silent_night)

        print("finished")


    asyncio.run(main())