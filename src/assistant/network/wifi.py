import gc
import network
import re
import time
import ntptime


# =========================================================
# WiFi
# =========================================================

def conectar_wifi(ssid, password):

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():

        print(f"Conectando em: {ssid}")

        wlan.connect(ssid, password)

        tentativas = 0

        while not wlan.isconnected() and tentativas < 10:
            time.sleep(1)
            tentativas += 1
            print(".", end="")

    if wlan.isconnected():

        print("\nWiFi conectado")
        print(wlan.ifconfig())
        time.sleep(1)
        
        ntptime.settime()
        print("Local time after synchronization：%s" %str(time.localtime()))
        print(time.gmtime())
        print(time.time())


        return True

    print("\nFalha no WiFi")

    return False


if __name__ == "__main__":
    
    SSID_REDE = "NOTE-646635 1412"
    SENHA_REDE = "798-y6N1"
    SSID_REDE = "RedeGamer"
    SENHA_REDE = "Vick0508"
    
    print(f"Conectando na rede: {SSID_REDE}")
    conectar_wifi(
        SSID_REDE,
        SENHA_REDE
    )

    