try:
    import uasyncio as asyncio
except ImportError:
    import asyncio


from connectivity import connect_to_wifi
from udotenv.dotenv import load_dotenv

from ullmtools.core.apis.openaimtools import OpenAIMTools

from ullmtools.tools import (
    TurnOnOffLedTool,
    GetWeatherTool,
    Scheduler,
    ScheduleEventTool,
)

from .webservice import WebService
        



async def main():

    config = load_dotenv("env.txt")
    api_key = config.get("API_KEY")
    ssid = config.get("WIFI_SSID")
    password = config.get("WIFI_PASS")

    print("Conectando na rede:", ssid)

    connect_to_wifi(ssid, password)


    llm = OpenAIMTools(
            api_key=api_key,
            model="gpt-4o-mini",
            verbose=True
        )

    scheduler = Scheduler(
            tool_executor=llm.execute_tool
        )
    
    system_prompt = (
            "Voce e um mini assistente para um display OLED 128x64. "
            "Sua resposta sera exibida em uma unica linha com texto corrido. "
            "Responda de forma curta, clara e natural. "
            "Nao use acentuacao. "
            "Nao use markdown. "
            "Nao use emojis. "
            "Nao use listas. "
            "Use no maximo uma frase curta. "      
            "\nAo agendar uma ferramenta utilize exatamente"
            "o nome registrado na lista de tools."
            "Exemplo: turn_onoff_led\n"
            "Nao utilize prefixos como:"
            "\n functions."
            "\n tools."
            "\n assistant."
        )
        


    schedule_tool = ScheduleEventTool(
            self.scheduler,
            verbose=True
        )

    weather_tool = GetWeatherTool()

    led_tool = TurnOnOffLedTool(
            pin=23
        )

    llm.register_tool(tool=schedule_tool)
    llm.register_tool(tool=weather_tool)
    llm.register_tool(tool=led_tool)

    app = WebService()

    await app.run(
        llm=llm, 
        scheduler=scheduler, 
        system_prompt=system_prompt
    )