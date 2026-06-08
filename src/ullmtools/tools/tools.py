from machine import Pin
from time import gmtime
import gc
import network

import time


import urequests
import ujson

# --------------------------------------------------
# Tools
# --------------------------------------------------


# --------------------------------------------------
# Get latitude and longitude from IP
# --------------------------------------------------

def get_lat_lon_from_my_ip() -> dict:
    wlan = network.WLAN(network.STA_IF)


    msg = {
            'Public IP': None,
            'Latitude': None,
            'Longitude': None,
            "Error":"Unknown error"
            }
    

    if not wlan.isconnected():
        msg = {
            'Public IP': None,
            'Latitude': None,
            'Longitude': None,
            "Error":"Device not connected to the internet"
            }
    
        return msg

    response = None

    try:
        response = urequests.get("http://ip-api.com/json")
        data = response.json()

        if data.get("status") == "success":

            public_ip = data.get("query")
            lat = data.get("lat")
            lon = data.get("lon")

            msg = {
                'Public IP': public_ip,
                'Latitude': lat,
                'Longitude': lon,
                "Error": None
            }            
            
 

    except Exception as e:
        msg = {
            'Public IP': None,
            'Latitude': None,
            'Longitude': None,
            "Error": f"Could not retrieve geolocation: {e}"
            }
            

    finally:
        if response:
            response.close()           

        gc.collect()

    return msg


def get_lat_lon() -> str:
    lat_lon = get_lat_lon_from_my_ip()
    return ujson.dumps(lat_lon)


# --------------------------------------------------
# Get Weather from Latitude and Longitude
# --------------------------------------------------


def get_weather() -> str:

    lat_lon = get_lat_lon_from_my_ip()

    latitude, longitude = lat_lon['Latitude'], lat_lon['Longitude']

    if latitude is None or longitude is None:
        return ujson.dumps({
            "success": False,
            "error": lat_lon.get("Error", "Unknown error")
        })

    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}"
        f"&longitude={longitude}"
        f"&current_weather=true"
    )

    # print(f"[Weather] {url}")

    response = None

    try:
        response = urequests.get(url)

        if response.status_code != 200:
            return ujson.dumps({
                "success": False,
                "error": f"HTTP {response.status_code}"
            })

        data = response.json()
        current = data["current_weather"]

        result = {
            "success": True,
            "temperature": current.get("temperature"),
            "wind_speed": current.get("windspeed"),
            "wind_direction": current.get("winddirection"),
            "weather_code": current.get("weathercode"),
            "time": current.get("time")
        }

        # print(f"[Weather] {result}")

        return ujson.dumps(result)

    except Exception as e:
        return ujson.dumps({
            "success": False,
            "error": str(e)
        })

    finally:
        if response:
            response.close()






# --------------------------------------------------
# Get local datetime and time
# --------------------------------------------------
UTC_OFFSET = -3


UTC_OFFSET_SECONDS = -3 * 3600


def get_local_datetime():

    now = (
        time()
        + UTC_OFFSET_SECONDS
    )

    t = localtime(now)

    return (
        "{:04d}-{:02d}-{:02d} "
        "{:02d}:{:02d}:{:02d}"
    ).format(
        t[0],
        t[1],
        t[2],
        t[3],
        t[4],
        t[5]
    )



# --------------------------------------------------
# Get local  time
# --------------------------------------------------
def get_local_time():

    utc = gmtime()

    hour = (
        utc[3] + UTC_OFFSET
    ) % 24

    return (
        "{:02d}:{:02d}:{:02d}".format(
            hour,
            utc[4],
            utc[5]
        )
    )

# --------------------------------------------------
# LED Control
# --------------------------------------------------
led = Pin(
    23,
    Pin.OUT
)

led.value(0)

def turn_onoff_led(value):

    value = int(value)

    led.value(value)

    if value == 1:
        return "LED ligado"

    return "LED desligado"
    
# --------------------------------------------------
# Get temperature
# --------------------------------------------------

def get_temperature(city):

    return (
        "28 graus Celsius em {}".format(
            city
        )
    )


class DisplayMessageTool:

    def __init__(
        self,
        ui, 
        player
    ):

        self.ui = ui
        self.player = player

    def __call__(
        self,
        message
    ):

        self.ui.set_response(
            message
        )

        self.player.play(
                [
                    'Star Trek intro',
                    80,
                    'NOTE_D4',
                    '-8',
                    'NOTE_G4',
                    '16',
                    'NOTE_C5',
                    '-4',
                    'NOTE_B4',
                    '8',
                    'NOTE_G4',
                    '-16',
                    'NOTE_E4',
                    '-16',
                    'NOTE_A4',
                    '-16',
                    'NOTE_D5',
                    '2'
                ]
            )
        return (
            "Mensagem exibida."
        )
