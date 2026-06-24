import gc
import sys
import uselect
import asyncio

# Mantidas apenas as dependências da LLM e ferramentas
from ullmtools import OpenAI
from ullmtools import ChatService
from ullmtools.tools import (
    TurnOnOffLedTool,
    LocalTimeTool,
    LocalDateTimeTool,
    Scheduler,
    ScheduleEventTool,
    GetLatLonTool,
    GetWeatherTool
)
from udotenv.dotenv import load_dotenv
from connectivity.wifi import connect_to_wifi, WLAN

# Constante de controle de memória interna (ajuste se necessário)
MIN_MEM = 20000 
config = load_dotenv("env.txt")

API_KEY = config.get("API_KEY")
SSID = config.get("WIFI_SSID")
PASSWORD = config.get("WIFI_PASS")
API_OPENWEATHER = config.get("API_OPENWEATHER")

connect_to_wifi(ssid=SSID, password=PASSWORD, verbose=True)


ip, mascara, gateway, dns_antigo = WLAN.ifconfig()

# Forçamos a placa a usar o mesmo IP/Gateway, mas com o DNS público do Google (8.8.8.8)
WLAN.ifconfig((ip, mascara, gateway, '8.8.8.8'))

gc.collect()

# =========================================================
# Terminal Callback
# =========================================================

class TerminalCallback:
    """Callback simplificado para exibir a resposta em streaming no terminal"""
    def __init__(self):
        self.started_response = False

    def on_token(self, token):
        if not self.started_response:
            print("\nGPT: ", end="")
            self.started_response = True
        
        sys.stdout.write(str(token))
        # Força a atualização do terminal no MicroPython
        if hasattr(sys.stdout, "flush"):
            sys.stdout.flush()


# =========================================================
# Terminal Assistant Manager
# =========================================================

class TerminalAssistant:

    def __init__(self, api_key):
        if not api_key:
            raise ValueError("api_key não informada")

        self.api_key = api_key
        self.llm = None
        self.scheduler = None
        self.chat = None
        self.display_callback = None
        
        self.__start_llm()

    def __start_llm(self):
        self.llm = OpenAI(api_key=self.api_key)

        self.scheduler = Scheduler(tool_executor=self.llm.execute_tool)
        self.llm.set_scheduler(self.scheduler)

        # Instancia as ferramentas exatamente como antes
        tools_to_register = [
            ScheduleEventTool(self.scheduler),
            TurnOnOffLedTool(),
            LocalTimeTool(),
            LocalDateTimeTool(),
            GetLatLonTool(),
            GetWeatherTool()
        ]

        # Adaptação dinâmica para o 'ullmtools'
        for tool in tools_to_register:
            if not hasattr(tool, "name"):
                tool.name = getattr(tool, "NAME", tool.__class__.__name__)
            
            if not hasattr(tool, "schema"):
                tool.schema = getattr(tool, "_SCHEMA", {})
            
            if not hasattr(tool, "func"):
                tool.func = tool.__call__

            self.llm.register_tool(tool=tool)

        # Define o callback customizado para o terminal
        self.display_callback = TerminalCallback()

        self.chat = ChatService(
            llm=self.llm,
            callback=self.display_callback
        )

    async def ask_llm(self, question):
        gc.collect()

        # Monitoramento básico de memória no terminal
        for _ in range(3):
            if gc.mem_free() > MIN_MEM:
                break
            print("\n[Aviso]: Memória baixa, tentando limpar...")
            gc.collect()

        self.display_callback.started_response = False

        try:
            # Mantida a correção para get_tools_schema()
            result = await self.chat.ask(
                question=question,
                tools=self.llm.get_tools_schema() 
            )
            
            # Caso o streaming não printe o final da resposta
            response_text = result.get("response", "")
            if not self.display_callback.started_response:
                print(f"\nGPT: {response_text}")
            else:
                print() # Quebra de linha ao finalizar a resposta em streaming

        except Exception as e:
            print(f"\nErro: {e}")


# =========================================================
# Async Input & Main Loop
# =========================================================

async def async_input(prompt):
    print(prompt, end="")
    if hasattr(sys.stdout, "flush"):
        sys.stdout.flush()
        
    poller = uselect.poll()
    poller.register(sys.stdin, uselect.POLLIN)
    
    buffer = ""
    
    while True:
        if poller.poll(0):
            char = sys.stdin.read(1)
            
            if char == '\n' or char == '\r':
                print()  
                poller.unregister(sys.stdin)
                return buffer
            
            elif char == '\x08' or char == '\x7f':
                if len(buffer) > 0:
                    buffer = buffer[:-1]
                    sys.stdout.write('\b \b')
                    if hasattr(sys.stdout, "flush"):
                        sys.stdout.flush()
            
            else:
                buffer += char
                sys.stdout.write(char)
                if hasattr(sys.stdout, "flush"):
                    sys.stdout.flush()
        
        await asyncio.sleep(0.02)


async def main():
    
    print("Iniciando assistente de terminal...")
    assistant = TerminalAssistant(api_key=API_KEY)
    print("Assistente pronto! Digite 'sair' para encerrar.\n")
    
    while True:
        question = await async_input("USER: ")
        question = question.strip()
        
        if not question:
            continue
            
        if question.lower() in ["sair", "exit", "quit"]:
            print("Encerrando...")
            break
            
        await assistant.ask_llm(question)
        print("-" * 40)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nEncerrado pelo usuário.")