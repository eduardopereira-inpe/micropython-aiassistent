import math
import uasyncio as asyncio

from machine import Pin, SoftI2C
from assistant.display.ssd1306 import SSD1306_I2C


class EmotionDisplay:

    WIDTH = 128
    HEIGHT = 64

    FACE_CENTER_Y = 22
    TEXT_Y = 54

    MAX_MESSAGE_SIZE = 120
    TEXT_SCROLL_STEP = 2
    FRAME_DELAY_MS = 30

    def __init__(self, scl_pin=22, sda_pin=21):

        self.i2c = SoftI2C(
            scl=Pin(scl_pin),
            sda=Pin(sda_pin)
        )

        self.oled = SSD1306_I2C(
            self.WIDTH,
            self.HEIGHT,
            self.i2c
        )

        self.current_emotion = "idle"

        self.message = ""
        self.scroll_x = self.WIDTH
        self.message_cycle_done = True
        self.loop_message = False

        self.running = True

        self.blink_counter = 0
        self.z_offset = 0

        # animação global
        self.anim_frame = 0

        # thinking
        self.think_frame = 0

    # =====================================================
    # Public API
    # =====================================================

    def set_emotion(self, emotion):
        self.current_emotion = emotion

    def idle(self):
        self.set_emotion("idle")

    def think(self):
        self.set_emotion("thinking")

    def talk(self):
        self.set_emotion("happy")

    def error(self):
        self.set_emotion("sad")

    def sleep(self):
        self.set_emotion("sleepy")

    def set_message(self, message):

        trimmed = message[-self.MAX_MESSAGE_SIZE:]

        if trimmed != self.message:
            self.message = trimmed
            self.scroll_x = self.WIDTH
            self.message_cycle_done = False

    def append_message(self, text):
        self.set_message(self.message + text)

    def clear_message(self):
        self.message = ""
        self.scroll_x = self.WIDTH
        self.message_cycle_done = True

    async def wait_message_cycle(self):

        while not self.message_cycle_done:
            await asyncio.sleep_ms(20)

    def stop(self):
        self.running = False

    # =====================================================
    # Animation Helpers
    # =====================================================

    def face_offset_y(self):
        return int(math.sin(self.anim_frame * 0.08) * 2)

    def pupil_offset_x(self):
        return int(math.sin(self.anim_frame * 0.03) * 2)

    # =====================================================
    # Drawing Helpers
    # =====================================================

    def fill_circle(self, x0, y0, r, color):

        for y in range(-r, r + 1):
            for x in range(-r, r + 1):

                if x * x + y * y <= r * r:
                    self.oled.pixel(x0 + x, y0 + y, color)

    def draw_arc(self, x0, y0, r, start_angle, end_angle, color):

        for a in range(start_angle, end_angle):

            angle = math.radians(a)

            x = int(x0 + r * math.cos(angle))
            y = int(y0 + r * math.sin(angle))

            self.oled.pixel(x, y, color)

    # =====================================================
    # Faces
    # =====================================================

    def draw_idle(self):

        offset = self.face_offset_y()
        look_x = self.pupil_offset_x()

        blink_phase = self.blink_counter

        # aberto
        if blink_phase < 120:

            self.fill_circle(
                40,
                self.FACE_CENTER_Y + offset,
                12,
                1
            )

            self.fill_circle(
                88,
                self.FACE_CENTER_Y + offset,
                12,
                1
            )

            self.fill_circle(
                40 + look_x,
                self.FACE_CENTER_Y + offset,
                4,
                0
            )

            self.fill_circle(
                88 + look_x,
                self.FACE_CENTER_Y + offset,
                4,
                0
            )

        # semi fechado
        elif blink_phase < 124:

            self.oled.fill_rect(
                28,
                self.FACE_CENTER_Y - 3 + offset,
                24,
                6,
                1
            )

            self.oled.fill_rect(
                76,
                self.FACE_CENTER_Y - 3 + offset,
                24,
                6,
                1
            )

        # fechado
        elif blink_phase < 128:

            self.oled.hline(
                28,
                self.FACE_CENTER_Y + offset,
                24,
                1
            )

            self.oled.hline(
                76,
                self.FACE_CENTER_Y + offset,
                24,
                1
            )

        # semi fechado abrindo
        elif blink_phase < 132:

            self.oled.fill_rect(
                28,
                self.FACE_CENTER_Y - 3 + offset,
                24,
                6,
                1
            )

            self.oled.fill_rect(
                76,
                self.FACE_CENTER_Y - 3 + offset,
                24,
                6,
                1
            )

        else:
            self.blink_counter = 0

        self.draw_arc(
            64,
            42 + offset,
            10,
            0,
            180,
            1
        )

        self.blink_counter += 1

    def draw_happy(self):

        offset = self.face_offset_y()
        look_x = self.pupil_offset_x()

        self.fill_circle(
            40,
            self.FACE_CENTER_Y + offset,
            15,
            1
        )

        self.fill_circle(
            88,
            self.FACE_CENTER_Y + offset,
            15,
            1
        )

        self.fill_circle(
            40 + look_x,
            self.FACE_CENTER_Y + offset,
            5,
            0
        )

        self.fill_circle(
            88 + look_x,
            self.FACE_CENTER_Y + offset,
            5,
            0
        )

        mouth_size = 6 + int(
            abs(math.sin(self.anim_frame * 0.25)) * 5
        )

        self.draw_arc(
            64,
            42 + offset,
            mouth_size,
            0,
            180,
            1
        )

    def draw_sad(self):

        offset = self.face_offset_y()

        self.fill_circle(
            40,
            self.FACE_CENTER_Y + 4 + offset,
            12,
            1
        )

        self.fill_circle(
            88,
            self.FACE_CENTER_Y + 4 + offset,
            12,
            1
        )

        self.fill_circle(
            40,
            self.FACE_CENTER_Y + 8 + offset,
            4,
            0
        )

        self.fill_circle(
            88,
            self.FACE_CENTER_Y + 8 + offset,
            4,
            0
        )

        self.draw_arc(
            64,
            46 + offset,
            10,
            180,
            360,
            1
        )

    def draw_angry(self):

        offset = self.face_offset_y()

        self.fill_circle(
            40,
            self.FACE_CENTER_Y + offset,
            12,
            1
        )

        self.fill_circle(
            88,
            self.FACE_CENTER_Y + offset,
            12,
            1
        )

        self.fill_circle(
            40,
            self.FACE_CENTER_Y - 4 + offset,
            5,
            0
        )

        self.fill_circle(
            88,
            self.FACE_CENTER_Y - 4 + offset,
            5,
            0
        )

        self.oled.line(
            28,
            12 + offset,
            52,
            18 + offset,
            1
        )

        self.oled.line(
            76,
            18 + offset,
            100,
            12 + offset,
            1
        )

        self.oled.hline(
            54,
            42 + offset,
            20,
            1
        )

    def draw_surprised(self):

        offset = self.face_offset_y()

        self.fill_circle(
            40,
            self.FACE_CENTER_Y + offset,
            18,
            1
        )

        self.fill_circle(
            88,
            self.FACE_CENTER_Y + offset,
            18,
            1
        )

        self.fill_circle(
            40,
            self.FACE_CENTER_Y + offset,
            6,
            0
        )

        self.fill_circle(
            88,
            self.FACE_CENTER_Y + offset,
            6,
            0
        )

        mouth_size = 4 + int(
            abs(math.sin(self.anim_frame * 0.2)) * 2
        )

        self.oled.rect(
            64 - mouth_size,
            40 + offset,
            mouth_size * 2,
            mouth_size * 2,
            1
        )

    def draw_thinking(self):

        offset = self.face_offset_y()

        self.oled.line(
            28,
            self.FACE_CENTER_Y + offset,
            52,
            self.FACE_CENTER_Y + offset,
            1
        )

        self.oled.line(
            76,
            self.FACE_CENTER_Y + offset,
            100,
            self.FACE_CENTER_Y + offset,
            1
        )

        self.oled.line(
            58,
            42 + offset,
            70,
            42 + offset,
            1
        )

        phase = (self.think_frame // 10) % 4

        if phase >= 1:
            self.fill_circle(95, 16, 1, 1)

        if phase >= 2:
            self.fill_circle(103, 10, 2, 1)

        if phase >= 3:
            self.fill_circle(113, 4, 3, 1)

        self.think_frame += 1

    def draw_sleepy(self):

        offset = self.face_offset_y()

        self.oled.hline(
            28,
            self.FACE_CENTER_Y + offset,
            24,
            1
        )

        self.oled.hline(
            76,
            self.FACE_CENTER_Y + offset,
            24,
            1
        )

        mouth_y = 42 + int(
            math.sin(self.anim_frame * 0.12)
        )

        self.oled.hline(
            54,
            mouth_y + offset,
            20,
            1
        )

        z1 = self.z_offset
        z2 = (self.z_offset + 10) % 24

        self.oled.text(
            "Z",
            100,
            20 - z1,
            1
        )

        self.oled.text(
            "z",
            108,
            20 - z2,
            1
        )

        self.z_offset += 1

        if self.z_offset > 24:
            self.z_offset = 0

    # =====================================================
    # Text Renderer
    # =====================================================

    def draw_message(self):

        if not self.message:
            return

        self.oled.text(
            self.message,
            self.scroll_x,
            self.TEXT_Y,
            1
        )

        if self.message_cycle_done and not self.loop_message:
            return

        self.scroll_x -= self.TEXT_SCROLL_STEP

        text_width = len(self.message) * 8

        if self.scroll_x < -text_width:

            self.message_cycle_done = True

            if self.loop_message:
                self.scroll_x = self.WIDTH
                self.message_cycle_done = False
            else:
                self.scroll_x = 0

    # =====================================================
    # Main Renderer
    # =====================================================

    def render(self):

        self.oled.fill(0)

        if self.current_emotion == "idle":
            self.draw_idle()

        elif self.current_emotion == "happy":
            self.draw_happy()

        elif self.current_emotion == "sad":
            self.draw_sad()

        elif self.current_emotion == "angry":
            self.draw_angry()

        elif self.current_emotion == "surprised":
            self.draw_surprised()

        elif self.current_emotion == "thinking":
            self.draw_thinking()

        elif self.current_emotion == "sleepy":
            self.draw_sleepy()

        self.draw_message()

        self.oled.show()

        self.anim_frame += 1

    # =====================================================
    # Async Loop
    # =====================================================

    async def run(self):

        while self.running:

            self.render()

            await asyncio.sleep_ms(
                self.FRAME_DELAY_MS
            )


if __name__ == "__main__":

    async def main():

        display = EmotionDisplay()

        asyncio.create_task(
            display.run()
        )

        display.set_message(
            "Emotion Display Ready"
        )

        while True:

            display.idle()
            await asyncio.sleep(5)

            display.talk()
            display.set_message(
                "Hello Human"
            )
            await asyncio.sleep(5)

            display.think()
            display.set_message(
                "Thinking..."
            )
            await asyncio.sleep(5)

            display.error()
            display.set_message(
                "Connection Error"
            )
            await asyncio.sleep(5)

            display.sleep()
            display.set_message(
                "Sleep Mode"
            )
            await asyncio.sleep(5)

    asyncio.run(main())