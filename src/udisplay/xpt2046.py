# MIT License
#
# Copyright (c) 2026 micropython-assistant contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""XPT2046 touch controller driver.

This module provides the :class:`Touch` class used to read resistive touch
coordinates from an XPT2046 controller over SPI in MicroPython.

The class supports two operating modes:

- Polling mode, where coordinates are read on demand via :meth:`get_touch`.
- Interrupt-assisted mode, where an IRQ pin triggers an internal async task
  that captures touch events and optionally invokes a callback.

It also includes calibration and normalization helpers to map raw ADC values
to display pixel coordinates.
"""

from micropython import const
from machine import Pin
import uasyncio as asyncio

class Touch:
    """Read and normalize touch data from an XPT2046 controller.

    The class wraps low-level SPI commands, applies calibration limits,
    filters noisy samples, and returns display-space coordinates.

    Args:
        spi: Configured SPI instance used to communicate with the controller.
        cs: Chip-select pin object for the touch controller.
        int_pin: Optional interrupt pin connected to T_IRQ.
        int_handler: Optional callback called as ``int_handler(x, y)`` after a
            valid touch is detected in interrupt-assisted mode.
        width: Target display width in pixels.
        height: Target display height in pixels.
        x_min: Minimum valid raw X value from calibration.
        x_max: Maximum valid raw X value from calibration.
        y_min: Minimum valid raw Y value from calibration.
        y_max: Maximum valid raw Y value from calibration.
    """

    GET_X = const(0xD0)
    GET_Y = const(0x90)

    def __init__(
            self,
            spi,
            cs,
            int_pin=None,
            int_handler=None,
            width=240,
            height=320,
            x_min=100,
            x_max=1962,
            y_min=100,
            y_max=1900):

        self.spi = spi

        self.cs = cs
        self.cs.init(Pin.OUT, value=1)

        self.rx_buf = bytearray(3)
        self.tx_buf = bytearray(3)

        self.width = width
        self.height = height

        self.x_min = x_min
        self.x_max = x_max

        self.y_min = y_min
        self.y_max = y_max

        self.x_multiplier = width / (x_max - x_min)
        self.x_add = -x_min * self.x_multiplier

        self.y_multiplier = height / (y_max - y_min)
        self.y_add = -y_min * self.y_multiplier

        self.int_handler = int_handler

        self._last_touch = None

        self._irq_flag = False
        self._event = asyncio.Event()

        if int_pin is not None:

            self.int_pin = int_pin
            self.int_pin.init(Pin.IN)

            self.int_pin.irq(
                trigger=Pin.IRQ_FALLING,
                handler=self._irq
            )

            asyncio.create_task(
                self._touch_task()
            )

    #################################################################
    # IRQ
    #################################################################

    def _irq(self, pin):
        """Set an IRQ flag from the hardware interrupt service routine.

        Args:
            pin: Interrupt source pin (unused, provided by MicroPython IRQ API).
        """
        self._irq_flag = True

    #################################################################
    # Async background task
    #################################################################

    async def _touch_task(self):

        while True:

            if self._irq_flag:

                self._irq_flag = False

                pos = self.get_touch()

                if pos is not None:

                    self._last_touch = pos

                    self._event.set()

                    if self.int_handler:
                        try:
                            self.int_handler(*pos)
                        except Exception as e:
                            print(e)

            await asyncio.sleep_ms(10)

    #################################################################
    # Async API
    #################################################################

    async def wait_touch(self):
        """Wait for the next touch event captured by interrupt mode.

        Returns:
            tuple[int, int] | None: Last valid normalized ``(x, y)`` touch
            position.
        """

        await self._event.wait()

        self._event.clear()

        return self._last_touch

    #################################################################
    # Calibration
    #################################################################

    def normalize(self, x, y):
        """Convert raw controller coordinates to display pixel coordinates.

        Args:
            x: Raw X reading from the touch controller.
            y: Raw Y reading from the touch controller.

        Returns:
            tuple[int, int]: Normalized ``(x, y)`` in display coordinates.
        """

        x = int(
            self.x_multiplier * x +
            self.x_add
        )

        y = int(
            self.y_multiplier * y +
            self.y_add
        )

        return x, y

    #################################################################
    # Raw Touch
    #################################################################

    def raw_touch(self):
        """Read one raw touch sample and validate it against calibration bounds.

        Returns:
            tuple[int, int] | None: Raw ``(x, y)`` if both values are inside the
            configured calibration range; otherwise ``None``.
        """

        x = self.send_command(self.GET_X)
        y = self.send_command(self.GET_Y)

        if (
            self.x_min <= x <= self.x_max and
            self.y_min <= y <= self.y_max
        ):
            return (x, y)

        return None

    #################################################################
    # Noise Filter
    #################################################################

    def get_touch(self, samples=5):
        """Read multiple samples, reject outliers, and return normalized touch.

        Args:
            samples: Number of raw samples to read for filtering. Must be at
                least 3 for outlier trimming to be effective.

        Returns:
            tuple[int, int] | None: Filtered and normalized ``(x, y)`` position,
            or ``None`` when a valid touch could not be obtained.
        """

        xs = []
        ys = []

        for _ in range(samples):

            value = self.raw_touch()

            if value is None:
                return None

            xs.append(value[0])
            ys.append(value[1])

        xs.sort()
        ys.sort()

        xs = xs[1:-1]
        ys = ys[1:-1]

        mean_x = sum(xs) // len(xs)
        mean_y = sum(ys) // len(ys)

        return self.normalize(
            mean_x,
            mean_y
        )

    #################################################################
    # SPI
    #################################################################

    def send_command(self, command):
        """Send a 1-byte command and return the 12-bit ADC response.

        Args:
            command: XPT2046 command byte.

        Returns:
            int: Raw 12-bit conversion result.
        """

        self.tx_buf[0] = command

        self.cs(0)

        self.spi.write_readinto(
            self.tx_buf,
            self.rx_buf
        )

        self.cs(1)

        return (
            (self.rx_buf[1] << 4) |
            (self.rx_buf[2] >> 4)
        )