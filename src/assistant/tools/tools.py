# --------------------------------------------------
# Tools
# --------------------------------------------------

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