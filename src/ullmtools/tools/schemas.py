# --------------------------------------------------
# Get latitude and longitude from IP
# --------------------------------------------------

GET_LAT_LON_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_lat_lon",
        "description": (
            "Retorna a latitude e longitude "
            "baseadas no endereço IP."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False
        }
    }
}

# --------------------------------------------------
# Get Weather from Latitude and Longitude
# --------------------------------------------------

GET_WEATHER_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": (    
            "Retorna informações meteorológicas atuais "
            "da localização do dispositivo, "
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False
        }
    }
}

# --------------------------------------------------
# Get local datetime and time Schema
# --------------------------------------------------

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


# --------------------------------------------------
# Get local Time Schema
# --------------------------------------------------

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


# --------------------------------------------------
# LED Control Schema
# --------------------------------------------------
   
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

# --------------------------------------------------
# Get Temperature Schema
# --------------------------------------------------

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

# --------------------------------------------------
# Schedule Event Schema
# --------------------------------------------------

SCHEDULE_EVENT_SCHEMA = {
    "type": "function",
    "function": {

        "name":
            "schedule_event",

        "description":
            (
                "Agenda a execucao "
                "de uma ferramenta "
                "no futuro."
            ),

        "parameters": {

            "type": "object",

            "properties": {

                "delay_seconds": {

                    "type":
                        "integer",

                    "description":
                        (
                            "Tempo de espera "
                            "em segundos."
                        )
                },

                "tool_name": {

                    "type":
                        "string",

                    "description":
                        (
                            "Nome exato da "
                            "ferramenta."
                        )
                },

                "arguments": {

                    "type":
                        "object",

                    "description":
                        (
                            "Argumentos da "
                            "ferramenta."
                        )
                }
            },

            "required": [
                "delay_seconds",
                "tool_name"
            ],

            "additionalProperties":
                False
        }
    }
}

# --------------------------------------------------
# Show Message Schema
# --------------------------------------------------

SHOW_MESSAGE_SCHEMA = {
    "type": "function",
    "function": {

        "name":
            "show_message",

        "description":
            (
                "Exibe uma mensagem "
                "no display."
            ),

        "parameters": {

            "type":
                "object",

            "properties": {

                "message": {

                    "type":
                        "string"
                }
            },

            "required": [
                "message"
            ],

            "additionalProperties":
                False
        }
    }
}