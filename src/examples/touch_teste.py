from machine import Pin, SPI
from udisplay.ili9341 import Display, color565
from udisplay.xpt2046 import Touch
import time

# -------------------------
# DISPLAY
# -------------------------

display_spi = SPI(
    1,
    baudrate=40000000,
    sck=Pin(14),
    mosi=Pin(13),
    miso=Pin(12)
)

# Backlight
Pin(21, Pin.OUT).value(1)

display = Display(
    display_spi,
    cs=Pin(15, Pin.OUT),
    dc=Pin(2, Pin.OUT),
    rst=Pin(27, Pin.OUT),
    width=240,
    height=320,
    rotation=90
)

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

touch_spi = SPI(
    2,
    baudrate=1000000,
    sck=Pin(25),
    mosi=Pin(32),
    miso=Pin(39)
)

touch = Touch(
    touch_spi,
    cs=Pin(33, Pin.OUT),
    width=240,
    height=320
)

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