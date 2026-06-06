from machine import Pin
from time import gmtime
# --------------------------------------------------
# Tools
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

GET_LOCAL_DATETIME_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_local_datetime",
        "description": (
            "Retorna a data e hora "
            "local atual."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False
        }
    }
}

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

GET_LOCAL_TIME_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_local_time",
        "description": (
            "Retorna a hora local atual "
            "no formato HH:MM:SS."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False
        }
    }
}

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
    
    
TURN_ONOFF_LED_SCHEMA = {
    "type": "function",
    "function": {
        "name": "turn_onoff_led",
        "description": (
            "Liga ou desliga o LED "
            "conectado ao pino 23."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "value": {
                    "type": "integer",
                    "description": (
                        "0 para desligar "
                        "e 1 para ligar."
                    ),
                    "enum": [
                        0,
                        1
                    ]
                }
            },
            "required": [
                "value"
            ],
            "additionalProperties": False
        }
    }
}

def get_temperature(city):

    return (
        "28 graus Celsius em {}".format(
            city
        )
    )

GET_TEMPERATURE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_temperature",
        "description": (
            "Retorna a temperatura atual "
            "de uma cidade"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": (
                        "Nome da cidade"
                    )
                }
            },
            "required": [
                "city"
            ]
        }
    }
}