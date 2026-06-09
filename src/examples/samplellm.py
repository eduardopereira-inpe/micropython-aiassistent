from assistant.network.wifi import conectar_wifi
from assistant.config import (
    API_KEY,
    SSID,
    PASSWORD
)
from ullmtools.core.apis.openaimtools import OpenAIMTools

from ullmtools.tools import ( 
    turn_onoff_led, 
    TURN_ONOFF_LED_SCHEMA,
    get_weather,
    GET_WEATHER_SCHEMA
)

try:
    import uasyncio as asyncio  # type: ignore
except ImportError:
    import asyncio


print(f"Conectando na rede: {SSID}")
conectar_wifi(
    SSID,
    PASSWORD
)


async def main():

    if API_KEY == "YOUR_OPENAI_API_KEY":
        print("Defina API_KEY no exemplo antes de executar.")
        return

    llm = OpenAIMTools(
        api_key=API_KEY,
        model="gpt-4o-mini",
        verbose=True
    )


    llm.register_tool(
        name="get_weather",
        func=get_weather,
        schema=GET_WEATHER_SCHEMA
    )

    llm.register_tool(
        name="turn_onoff_led",
        func=turn_onoff_led,
        schema=TURN_ONOFF_LED_SCHEMA
    )

    
    while True:
        user_input = input("Input Text > ")        

        response = llm.chat(
            prompt=user_input,
            tools=llm.get_tools_schema()
        )

        print("Resposta final:")
        print(response["response"])



asyncio.run(main())


