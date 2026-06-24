import gc
# Força o Garbage Collector a ser extremamente agressivo
gc.threshold(gc.mem_free() // 4)
gc.collect()

import sys
import uselect
import asyncio

# Imports de Conectividade e Variáveis de Ambiente
from udotenv.dotenv import load_dotenv
from connectivity.wifi import connect_to_wifi, WLAN

# Imports do Driver do Display através do __init__.py da pasta driver
from driver import TFTTouch

# Imports essenciais da LLM (Sem ferramentas pesadas para poupar RAM)
from ullmtools import OpenAI
from ullmtools import ChatService

# =========================================================
# Configuração de Ambiente e Rede
# =========================================================
MIN_MEM = 28000  # Limite rígido de segurança
config = load_dotenv("env.txt")

API_KEY = config.get("API_KEY")
SSID = config.get("WIFI_SSID")
PASSWORD = config.get("WIFI_PASS")

# Conexão Wi-Fi
connect_to_wifi(ssid=SSID, password=PASSWORD, verbose=True)

# Forçar DNS público do Google (8.8.8.8)
ip, mascara, gateway, dns_antigo = WLAN.ifconfig()
WLAN.ifconfig((ip, mascara, gateway, '8.8.8.8'))

# Destruição completa de objetos temporários pós-conexão
del config, ip, mascara, gateway, dns_antigo
gc.collect()

# =========================================================
# Gerenciador do Display Otimizado para Baixa Memória
# =========================================================
class DisplayTerminal:
    def __init__(self, display):
        self.display = display
        self.cursor_x = 0
        self.cursor_y = 0
        self.max_x = display.width   
        self.max_y = display.height  
        self.line_height = 10        
        self.clear_screen()

    def clear_screen(self):
        self.display.clear(0) # 0 = Preto
        self.cursor_x = 0
        self.cursor_y = 0
        gc.collect()

    def write_str(self, text, color):
        if not text:
            return

        for char in text:
            if char == '\n' or char == '\r':
                self.new_line()
                continue
                
            if self.cursor_x + 8 > self.max_x:
                self.new_line()

            # Desenha o caractere
            self.display.draw_text8x8(self.cursor_x, self.cursor_y, char, color, background=0)
            self.cursor_x += 8
            
            # Força o GC a limpar o lixo que o draw_text8x8 cria a cada caractere
            gc.collect()

    def new_line(self):
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
            self.dt.write_str("GPT: ", 0x07E0) # Verde
            self.started_response = True
        
        sys.stdout.write(token_str)
        if hasattr(sys.stdout, "flush"):
            sys.stdout.flush()
            
        self.dt.write_str(token_str, 0xFFFF) # Branco
        del token_str
        
        # Monitora e limpa buffers HTTP agressivamente durante a recepção
        if gc.mem_free() < MIN_MEM:
            gc.collect()


# =========================================================
# Terminal Assistant Manager (Ultra Light)
# =========================================================
class TerminalAssistant:
    def __init__(self, api_key, display_terminal):
        self.api_key = api_key
        self.dt = display_terminal
        self.llm = OpenAI(api_key=self.api_key)
        
        # ChatService sem passagem de Scheduler ou ferramentas complexas
        self.display_callback = TerminalCallback(self.dt)
        self.chat = ChatService(llm=self.llm, callback=self.display_callback)
        gc.collect()

    async def ask_llm(self, question):
        gc.collect()

        # Ciclo de liberação extrema pré-requisito
        for _ in range(3):
            if gc.mem_free() > MIN_MEM:
                break
            gc.collect()

        self.display_callback.started_response = False

        try:
            # Enviamos tools=None explicitamente para impedir a biblioteca 
            # de gerar payloads JSON gigantescos na memória heap contínua.
            result = await self.chat.ask(
                question=question,
                tools=None
            )
            
            response_text = result.get("response", "")
            if not self.display_callback.started_response:
                print(f"\nGPT: {response_text}")
                self.dt.new_line()
                self.dt.write_str(f"GPT: {response_text}", 0xFFFF)
            else:
                print() 

            del result, response_text
        except Exception as e:
            msg_erro = f"Erro: {e}"
            print(f"\n{msg_erro}")
            self.dt.new_line()
            self.dt.write_str("Erro ENOMEM. Reiniciando memoria...", 0xF800)
        finally:
            gc.collect()


# =========================================================
# Loop de Captura Assíncrono (Teclado Serial)
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


# =========================================================
# Fluxo Principal
# =========================================================
async def main():
    # Inicializa display usando os parâmetros internos automáticos do driver
    tft = TFTTouch(
#         disp_sck=6,
#         disp_mosi=7,
#         disp_miso=2,
#         
#         # Pinos de Controle Individuais
#         disp_cs=10,
#         disp_dc=9,
#         disp_rst=8,
#         disp_bl=5,
#         rotation=0,
        has_touch=False
    )
    dt = DisplayTerminal(tft.display)
    
    dt.write_str("Inicializando Chat...\n", 0x07E0)
    assistant = TerminalAssistant(api_key=API_KEY, display_terminal=dt)
    
    dt.clear_screen()
    dt.write_str("Pronto!\n", 0x07E0)
    print(f"Sistema Pronto. Memoria Livre Inicializada: {gc.mem_free()} Bytes\n")
    
    while True:
        gc.collect()
        print(f"[RAM Livre: {gc.mem_free()} Bytes]")
        
        question = await async_input("USER: ", dt)
        question = question.strip()
        
        if not question:
            continue
            
        if question.lower() in ["sair", "exit", "quit", "clear", "cls"]:
            if question.lower() in ["clear", "cls"]:
                dt.clear_screen()
                continue
            break
            
        await assistant.ask_llm(question)
        print("-" * 40)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDesconectado.")