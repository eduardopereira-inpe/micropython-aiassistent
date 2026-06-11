from udisplay.cyd import CYD
from udisplay.ili9341 import color565
import uasyncio as asyncio

# =====================================================
# CORES
# =====================================================

BLACK = color565(0, 0, 0)
WHITE = color565(255, 255, 255)
BLUE  = color565(0, 100, 255)
RED   = color565(255, 0, 0)

# =====================================================
# CYD
# =====================================================

cyd = CYD(
    display_width=240,
    display_height=320,
    rotation=90
)

display = cyd.display

# =====================================================
# BUTTON
# =====================================================

class Button:

    def __init__(self, x, y, w, h, label):

        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.label = label

    def contains(self, px, py):

        return (
            self.x <= px < self.x + self.w and
            self.y <= py < self.y + self.h
        )

# =====================================================
# BUTTONS
# =====================================================

buttons = [

    Button(0,   60, 60, 50, "7"),
    Button(60,  60, 60, 50, "8"),
    Button(120, 60, 60, 50, "9"),
    Button(180, 60, 60, 50, "/"),

    Button(0,   110, 60, 50, "4"),
    Button(60,  110, 60, 50, "5"),
    Button(120, 110, 60, 50, "6"),
    Button(180, 110, 60, 50, "*"),

    Button(0,   160, 60, 50, "1"),
    Button(60,  160, 60, 50, "2"),
    Button(120, 160, 60, 50, "3"),
    Button(180, 160, 60, 50, "-"),

    Button(0,   210, 60, 50, "C"),
    Button(60,  210, 60, 50, "0"),
    Button(120, 210, 60, 50, "="),
    Button(180, 210, 60, 50, "+")
]

# =====================================================
# DISPLAY
# =====================================================

def draw_button(button, pressed=False):

    if pressed:
        bg = BLUE
        fg = WHITE
    else:
        bg = BLACK
        fg = WHITE

    display.fill_rectangle(
        button.x + 1,
        button.y + 1,
        button.w - 2,
        button.h - 2,
        bg
    )

    display.draw_rectangle(
        button.x,
        button.y,
        button.w,
        button.h,
        WHITE
    )

    tx = button.x + (button.w // 2) - 4
    ty = button.y + (button.h // 2) - 4

    display.draw_text8x8(
        tx,
        ty,
        button.label,
        fg
    )

def draw_ui():

    display.clear(BLACK)

    display.draw_rectangle(
        0,
        0,
        240,
        60,
        WHITE
    )

    for button in buttons:
        draw_button(button)

def update_display(text):

    display.fill_rectangle(
        2,
        2,
        236,
        56,
        BLACK
    )

    text = str(text)

    if len(text) > 28:
        text = text[-28:]

    display.draw_text8x8(
        5,
        25,
        text,
        WHITE
    )

# =====================================================
# CALCULATOR ENGINE
# =====================================================

expression = ""

def process_key(key):

    global expression

    if key == "C":

        expression = ""

    elif key == "=":

        try:

            result = eval(expression)

            if isinstance(result, float):

                if result.is_integer():
                    result = int(result)

            expression = str(result)

        except Exception:

            expression = "ERROR"

    else:

        if expression == "ERROR":
            expression = ""

        expression += key

    return expression

# =====================================================
# BUTTON EFFECT
# =====================================================

async def flash_button(button):

    draw_button(button, True)

    await asyncio.sleep_ms(100)

    draw_button(button, False)

# =====================================================
# TOUCH TASK
# =====================================================

async def calculator_task():

    global expression

    expression = ""

    update_display("0")

    while True:

        x, y = await cyd.wait_touch()


        for button in buttons:

            if button.contains(x, y):

                asyncio.create_task(
                    flash_button(button)
                )

                value = process_key(
                    button.label
                )

                update_display(value)

                break

# =====================================================
# MAIN
# =====================================================

async def main():

    draw_ui()

    await calculator_task()

asyncio.run(main())