# --------------------------------------------------
# Tools
# --------------------------------------------------

def get_temperature(city):

    return (
        "28 degrees Celsius in {}".format(
            city
        )
    )


GET_TEMPERATURE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_temperature",
        "description": (
            "Returns the current temperature "
            "for a city"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": (
                        "City name"
                    )
                }
            },
            "required": [
                "city"
            ]
        }
    }
}