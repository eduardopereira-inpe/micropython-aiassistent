from connectivity import connect_to_wifi
from assistant.utils.asyncinput import async_input
import gc
from udotenv.dotenv import load_dotenv
from ullmtools.core.apis.openaimtools import OpenAIMTools

from ullmtools.tools import ( 
    TurnOnOffLedTool,
    GetWeatherTool, 
    Scheduler,
    ScheduleEventTool,
)

try:
    import uasyncio as asyncio  # type: ignore
except ImportError:
    import asyncio

config = load_dotenv("env.txt")

API_KEY = config.get("API_KEY")
SSID = config.get("WIFI_SSID")
PASSWORD = config.get("WIFI_PASS")

print(f"Conectando na rede: {SSID}")
connect_to_wifi(
    SSID,
    PASSWORD
)


async def main():

    if API_KEY == "YOUR_OPENAI_API_KEY":
        print("Defina API_KEY no exemplo antes de executar.")
        return
    
    systemprompt = (
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

    llm = OpenAIMTools(
        api_key=API_KEY,
        model="gpt-4o-mini",
        verbose=True,
    )


    scheduler = Scheduler(
            tool_executor=
                llm.execute_tool
        )

    llm.set_scheduler(
            scheduler
        )

    schedule_event_tool = ScheduleEventTool(
            scheduler,
            verbose=True
        )

    get_weather = GetWeatherTool()
    turn_onoff_led = TurnOnOffLedTool(pin=23)


    llm.register_tool(tool=schedule_event_tool)

    llm.register_tool(tool=get_weather)

    llm.register_tool(tool=turn_onoff_led)


    asyncio.create_task(
            scheduler.run()
        )

    
    while True:
        user_input = await async_input("Input Text > ")

        if not user_input:
            await asyncio.sleep(0)
            continue

        response = llm.chat(
            prompt=user_input,
            system_prompt=systemprompt,
            tools=llm.get_tools_schema()
        )
        gc.collect()


        print("Resposta final:")
        print(response["response"])

        await asyncio.sleep(0)



asyncio.run(main())


