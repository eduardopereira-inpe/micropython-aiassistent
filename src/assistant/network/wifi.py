import gc
import network
import re
import time
import ntptime

import urequests
import ujson

def _log(msg, verbose):
    if verbose is True:
        print(msg)
# =========================================================
# WiFi
# =========================================================

def get_lat_lon_from_ip(verbose=True):

    wlan = network.WLAN(network.STA_IF)

    if not wlan.isconnected():
        _log("WiFi não conectado", verbose)
        return None

    ip_info = wlan.ifconfig()
    local_ip = ip_info[0]

    _log(f"Local IP Address: {local_ip}", verbose)

    response = None

    try:
        response = urequests.get("http://ip-api.com/json")
        data = response.json()

        if data.get("status") == "success":

            public_ip = data.get("query")
            lat = data.get("lat")
            lon = data.get("lon")

            _log(f"Public IP: {public_ip}", verbose)
            _log(f"Latitude: {lat}", verbose)
            _log(f"Longitude: {lon}", verbose)

            return [lat, lon]

        _log(
            f"Geolocation API failed: {data.get('message')}",
            verbose
        )

    except Exception as e:
        _log(f"Could not retrieve geolocation: {e}", verbose)

    finally:
        if response:
            response.close()

        gc.collect()

    return None

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
        
        try:        
            ntptime.settime()
            print("Local time after synchronization：%s" %str(time.localtime()))
            print(time.gmtime())
            print(time.time())
        except Exception as error:
            print(f"[wifi] NTPTime sinc fail: {error}")
            
        


        return True

    print("\nFalha no WiFi")

    return False

    
        
    

if __name__ == "__main__":
    
    SSID_REDE = "NOTE-646635 1412"
    SENHA_REDE = "798-y6N1"
#     SSID_REDE = "RedeGamer"
#     SENHA_REDE = "Vick0508"
    
    print(f"Conectando na rede: {SSID_REDE}")
    conectar_wifi(
        SSID_REDE,
        SENHA_REDE
    )
    
    get_lat_lon_from_ip()
    
 

    