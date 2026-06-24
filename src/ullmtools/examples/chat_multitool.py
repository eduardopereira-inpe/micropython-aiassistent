import gc
# Executa uma coleta inicial agressiva antes de qualquer import pesado
gc.threshold(gc.mem_free() // 4)
gc.collect()

import sys
import uselect
import asyncio
from machine import Pin, SPI

# Imports de Conectividade e Variáveis de Ambiente
from udotenv.dotenv import load_dotenv
from connectivity.wifi import connect_to_wifi, WLAN

# Imports do Driver do Display através do __init__.py da pasta driver
from driver import TFTTouch, Colors

# Imports da LLM e Ferramentas
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

# =========================================================
# Configuração de Ambiente e Rede
# =========================================================
MIN_MEM = 25000  # Aumentado o limite de segurança devido ao display
config = load_dotenv("env.txt")

API_KEY = config.get("API_KEY")
SSID = config.get("WIFI_SSID")
PASSWORD = config.get("WIFI_PASS")
API_OPENWEATHER = config.get("API_OPENWEATHER")

# Conexão Wi-Fi
connect_to_wifi(ssid=SSID, password=PASSWORD, verbose=True)

# Forçar DNS público do Google (8.8.8.8)
ip, mascara, gateway, dns_antigo = WLAN.ifconfig()
WLAN.ifconfig((ip, mascara, gateway, '8.8.8.8'))

del config, ip, mascara, gateway, dns_antigo  # Remove variáveis não usadas da RAM
gc.collect()

# =========================================================
# Gerenciador do Display Otimizado para Baixa Memória
# =========================================================
class DisplayTerminal:
    """Classe focada em desenhar com o menor consumo de RAM possível"""
    def __init__(self, display):
        self.display = display
        self.cursor_x = 0
        self.cursor_y = 0
        self.max_x = display.width   
        self.max_y = display.height  
        self.line_height = 10        
        self.clear_screen()

    def clear_screen(self):
        """Limpa a tela usando o método nativo sem alocar buffers"""
        self.display.clear(0) # 0 = Preto
        self.cursor_x = 0
        self.cursor_y = 0
        gc.collect()

    def write_str(self, text, color):
        """Escreve o texto quebrando linhas sem duplicar strings na RAM"""
        if not text:
            return

        # Processamento caractere por caractere evita a criação de sub-arrays pesados na Heap
        for char in text:
            if char == '\n' or char == '\r':
                self.new_line()
                continue
                
            # Verifica estouro da borda horizontal (cada caractere tem 8 pixels de largura)
            if self.cursor_x + 8 > self.max_x:
                self.new_line()

            # Desenha o caractere individualmente para poupar a criação de FrameBuffers longos
            self.display.draw_text8x8(self.cursor_x, self.cursor_y, char, color, background=0)
            self.cursor_x += 8

    def new_line(self):
        """Avança o cursor vertical. Se atingir o fim da tela, limpa e recomeça topo."""
        self.cursor_x = 0
        self.cursor_y += self.line_height
        
        if self.cursor_y + self.line_height > self.max_y:
            self.clear_screen()


# =========================================================
# Terminal Callback
# =========================================================
class TerminalCallback:
    def __init__(self, display_terminal):
        self.dt = display_terminal
        self.started_response = False

    def on_token(self, token):
        token_str = str(token)
        
        if not self.started_response:
            print("\nGPT: ", end="")
            self.dt.new_line()
            self.dt.write_str("GPT: ", 0x07E0) # Verde Nativo
            self.started_response = True
        
        sys.stdout.write(token_str)
        if hasattr(sys.stdout, "flush"):
            sys.stdout.flush()
            
        self.dt.write_str(token_str, 0xFFFF) # Branco
        
        # Coleta de lixo periódica durante o recebimento de tokens
        if gc.mem_free() < MIN_MEM:
            gc.collect()


# =========================================================
# Terminal Assistant Manager
# =========================================================
class TerminalAssistant:
    def __init__(self, api_key, display_terminal):
        if not api_key:
            raise ValueError("api_key não informada")

        self.api_key = api_key
        self.dt = display_terminal
        self.llm = None
        self.scheduler = None
        self.chat = None
        self.display_callback = None
        
        self.__start_llm()

    def __start_llm(self):
        self.llm = OpenAI(api_key=self.api_key)
        self.scheduler = Scheduler(tool_executor=self.llm.execute_tool)
        self.llm.set_scheduler(self.scheduler)

        tools_to_register = [
            ScheduleEventTool(self.scheduler),
#             TurnOnOffLedTool(),
            LocalTimeTool(),
            LocalDateTimeTool(),
            GetLatLonTool(),
            GetWeatherTool()
        ]

        for tool in tools_to_register:
            if not hasattr(tool, "name"):
                tool.name = getattr(tool, "NAME", tool.__class__.__name__)
            if not hasattr(tool, "schema"):
                tool.schema = getattr(tool, "_SCHEMA", {})
            if not hasattr(tool, "func"):
                tool.func = tool.__call__

            self.llm.register_tool(tool=tool)

        self.display_callback = TerminalCallback(self.dt)
        self.chat = ChatService(llm=self.llm, callback=self.display_callback)
        gc.collect()

    async def ask_llm(self, question):
        # Liberação agressiva de memória pré-requisito
        gc.collect()

        for i in range(3):
            if gc.mem_free() > MIN_MEM:
                break
            print(f"[RAM]: Memória crítica ({gc.mem_free()} B). Forçando limpeza profunda {i+1}...")
            gc.collect()

        self.display_callback.started_response = False

        try:
            # Para economizar ainda mais RAM, você pode mitigar o envio de todas as ferramentas de uma vez
            # extraindo apenas o esquema necessário ou executando diretamente:
            tools_schema = self.llm.get_tools_schema()

            result = await self.chat.ask(
                question=question,
                tools=tools_schema
            )
            
            response_text = result.get("response", "")
            if not self.display_callback.started_response:
                print(f"\nGPT: {response_text}")
                self.dt.new_line()
                self.dt.write_str(f"GPT: {response_text}", 0xFFFF)
            else:
                print() 

        except Exception as e:
            msg_erro = f"Erro: {e}"
            print(f"\n{msg_erro}")
            self.dt.new_line()
            self.dt.write_str(msg_erro, 0xF800) # Vermelho
            
        finally:
            # Garante a limpeza pós-execução da requisição HTTP HTTP/REST da OpenAI
            gc.collect()


# =========================================================
# Loop de Captura Assíncrono
# =========================================================
async def async_input(prompt, display_terminal):
    print(prompt, end="")
    if hasattr(sys.stdout, "flush"):
        sys.stdout.flush()
    
    display_terminal.new_line()
    display_terminal.write_str(prompt, 0x07E0) 
        
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
                
                display_terminal.write_str(char, 0xFFFF)
        
        await asyncio.sleep(0.02)


async def main():
    print(f"Memória RAM livre antes do display: {gc.mem_free()} Bytes")
    
    tft = TFTTouch(
        disp_sck=6,
        disp_mosi=7,
        disp_miso=2,
        
        # Pinos de Controle Individuais
        disp_cs=10,
        disp_dc=9,
        disp_rst=8,
        disp_bl=5,
        rotation=0,
        has_touch=False
    )
    
    dt = DisplayTerminal(tft.display)
    dt.write_str("Iniciando LLM...", 0x07E0)
    
    assistant = TerminalAssistant(api_key=API_KEY, display_terminal=dt)
    
    dt.clear_screen()
    dt.write_str("Pronto para uso!\n", 0x07E0)
    print(f"Memória RAM livre após carregar o sistema: {gc.mem_free()} Bytes\n")
    
    while True:
        # Monitoramento em tempo real antes de cada prompt
        print(f"[RAM Livre: {gc.mem_free()} Bytes]")
        
        question = await async_input("USER: ", dt)
        question = question.strip()
        
        if not question:
            continue
            
        if question.lower() in ["sair", "exit", "quit", "clear", "cls"]:
            if question.lower() in ["clear", "cls"]:
                dt.clear_screen()
                gc.collect()
                continue
            break
            
        await assistant.ask_llm(question)
        print("-" * 40)
        gc.collect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDesconectado.")