"""
Wi-Fi connectivity helpers for MicroPython ESP32.

This module intentionally creates the WLAN singleton during application
startup (boot time) instead of creating a new network.WLAN() instance
whenever a connection is requested.

Background:
On memory-constrained ESP32 devices running graphical interfaces
(for example CYD/Cheap Yellow Display applications using cydgui,
framebuffers, asyncio, and virtual keyboards), heap fragmentation
may occur during normal execution.

```
Even when gc.mem_free() reports sufficient free memory, the ESP32
Wi-Fi driver may require large contiguous memory blocks during
WLAN object creation. If the heap is fragmented, creating a new
network.WLAN(network.STA_IF) instance can fail with:

    RuntimeError: Wifi Unknown Error 0x0101

Initializing the WLAN instance during boot ensures that the Wi-Fi
driver allocates its internal resources before the heap becomes
fragmented, significantly improving reliability.
```

Implementation:
- Create the WLAN singleton once during startup.
- Reuse the same instance throughout the application lifecycle.
- Enable or disable the interface as needed.
- Never recreate the WLAN object during runtime.

Example:
WLAN = network.WLAN(network.STA_IF)
WLAN.active(False)

```
# Later...
WLAN.active(True)
WLAN.connect(ssid, password)
```

"""

import gc
import network
import ntptime
import time

# Singleton Wi-Fi interface.

#

# The WLAN object is intentionally allocated during module initialization

# to avoid runtime allocation failures caused by heap fragmentation.

WLAN = network.WLAN(network.STA_IF)
WLAN.active(False)

def _log(message, verbose):
    """Print a message when verbose mode is enabled.

    Args:
        message: Message to print.
        verbose: Whether logging is enabled.
    """
    if verbose:
        print(message)


def connect_to_wifi(ssid, password, verbose=True):
    """Connect to a Wi-Fi network.
    The function reuses the global WLAN singleton created during boot.
    This avoids creating additional WLAN instances and reduces the risk
    of memory-related Wi-Fi initialization failures.

    Args:
        ssid: Wi-Fi network name.
        password: Wi-Fi password.
        verbose: Enables diagnostic logging when True.

    Returns:
        True if the connection was established successfully, otherwise
        False.
    """
    gc.collect()

    _log("Free memory: {}".format(gc.mem_free()), verbose)
    _log("Allocated memory: {}".format(gc.mem_alloc()), verbose)

    if not WLAN.active():
        WLAN.active(True)
        time.sleep_ms(200)

    if WLAN.isconnected():
        _log("Wi-Fi already connected.", verbose)
        return True

    _log("Connecting to: {}".format(ssid), verbose)

    try:
        WLAN.connect(ssid, password)
    except Exception as error:
        _log("Failed to start connection: {}".format(error), verbose)
        return False

    attempts = 0

    while not WLAN.isconnected() and attempts < 10:
        time.sleep(1)
        attempts += 1
        _log(".", verbose)

    if WLAN.isconnected():

        _log("Wi-Fi connected.", verbose)
        _log(WLAN.ifconfig(), verbose)

        try:
            ntptime.settime()
            _log(
                "Time synchronized: {}".format(time.localtime()),
                verbose,
            )
        except Exception as error:
            _log(
                "[wifi] NTP synchronization failed: {}".format(error),
                verbose,
            )

        return True

    _log("Wi-Fi connection failed.", verbose)
    return False


