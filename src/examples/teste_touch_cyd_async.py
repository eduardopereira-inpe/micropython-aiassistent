from udisplay.cyd import CYD
from udisplay.ili9341 import color565
import uasyncio as asyncio

cyd = CYD(
    display_width=240,
    display_height=320,
    rotation=90
)

display = cyd.display

display.clear(color565(0, 0, 0))

display.draw_text8x8(
    10,
    10,
    "Touch Test",
    color565(255, 255, 255)
)

async def touch_loop():

    last_x = -100
    last_y = -100

    while True:

        x, y = await cyd.touch.wait_touch()

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

asyncio.run(touch_loop())