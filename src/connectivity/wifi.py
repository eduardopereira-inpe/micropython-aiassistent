import network
import time
import ntptime


def _log(msg, verbose):
    if verbose is True:
        print(msg)
# =========================================================
# WiFi
# =========================================================

def connect_to_wifi(ssid, password, verbose=True):

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():

        _log(f"Conectando em: {ssid}", verbose)

        wlan.connect(ssid, password)

        tentativas = 0

        while not wlan.isconnected() and tentativas < 10:
            time.sleep(1)
            tentativas += 1
            _log(".", verbose)

    if wlan.isconnected():

        _log("\nWiFi conectado", verbose)
        _log(wlan.ifconfig(), verbose)
        time.sleep(1)
        
        try:        
            ntptime.settime()
            _log("Local time after synchronization：%s" %str(time.localtime()), verbose)
            _log(time.gmtime(), verbose)
            _log(time.time(), verbose)
        except Exception as error:
            _log(f"[wifi] NTPTime sinc fail: {error}", verbose)

        return True

    _log("\nFalha no WiFi", verbose)

    return False