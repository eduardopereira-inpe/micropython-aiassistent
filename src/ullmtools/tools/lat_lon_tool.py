import gc
import network
import urequests
import ujson

from .base_tool import CallableTool


def get_lat_lon_from_my_ip() -> dict:
    wlan = network.WLAN(network.STA_IF)

    msg = {
        "Public IP": None,
        "Latitude": None,
        "Longitude": None,
        "Error": "Unknown error"
    }

    if not wlan.isconnected():
        return {
            "Public IP": None,
            "Latitude": None,
            "Longitude": None,
            "Error": "Device not connected to the internet"
        }

    response = None

    try:
        response = urequests.get("http://ip-api.com/json")
        data = response.json()

        if data.get("status") == "success":
            msg = {
                "Public IP": data.get("query"),
                "Latitude": data.get("lat"),
                "Longitude": data.get("lon"),
                "Error": None
            }

    except Exception as e:
        msg = {
            "Public IP": None,
            "Latitude": None,
            "Longitude": None,
            "Error": "Could not retrieve geolocation: {}".format(e)
        }

    finally:
        if response:
            response.close()

        gc.collect()

    return msg


class GetLatLonTool(CallableTool):

    NAME = "get_lat_lon"

    _SCHEMA = {
        "type": "function",
        "function": {
            "name": "get_lat_lon",
            "description": (
                "Retorna a latitude e longitude "
                "baseadas no endereco IP."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            }
        }
    }

    def __call__(self):
        lat_lon = get_lat_lon_from_my_ip()
        return ujson.dumps(lat_lon)
