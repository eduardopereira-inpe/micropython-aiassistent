import ujson
import urequests

from .base_tool import CallableTool
from .lat_lon_tool import get_lat_lon_from_my_ip


class GetWeatherTool(CallableTool):

    NAME = "get_weather"

    _SCHEMA = {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": (
                "Retorna informacoes meteorologicas atuais "
                "da localizacao do dispositivo."
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

        latitude = lat_lon["Latitude"]
        longitude = lat_lon["Longitude"]

        if latitude is None or longitude is None:
            return ujson.dumps({
                "success": False,
                "error": lat_lon.get("Error", "Unknown error")
            })

        url = (
            "https://api.open-meteo.com/v1/forecast"
            "?latitude={}"
            "&longitude={}"
            "&current_weather=true"
        ).format(latitude, longitude)

        response = None

        try:
            response = urequests.get(url)

            if response.status_code != 200:
                return ujson.dumps({
                    "success": False,
                    "error": "HTTP {}".format(response.status_code)
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

            return ujson.dumps(result)

        except Exception as e:
            return ujson.dumps({
                "success": False,
                "error": str(e)
            })

        finally:
            if response:
                response.close()
