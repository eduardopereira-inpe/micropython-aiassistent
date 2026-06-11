from machine import Pin, SPI
from udisplay.cyd import CYD
from udisplay.ili9341 import color565
import time

# -------------------------
# DISPLAY
# -------------------------

cyd = CYD(display_width=240, display_height=320, rotation=90)

display = cyd.display
display.clear(color565(0, 0, 0))

display.draw_text8x8(
    10,
    10,
    "Touch Test",
    color565(255, 255, 255)
)

# -------------------------
# TOUCH
# -------------------------

touch = cyd.touch

# -------------------------
# LOOP
# -------------------------

last_x = -1
last_y = -1

while True:

    pos = touch.get_touch()

    if pos:

        x, y = pos
        

        # evita redesenhar o mesmo ponto
        if abs(x - last_x) > 2 or abs(y - last_y) > 2:

            print("Touch:", x, y)

            display.fill_circle(
                x,
                y,
                3,
                color565(255, 0, 0)
            )

            last_x = x
            last_y = y

    time.sleep_ms(20)