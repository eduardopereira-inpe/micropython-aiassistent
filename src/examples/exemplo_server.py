try:
    import usocket as socket
except ImportError:
    import socket

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import gc

from connectivity import connect_to_wifi
from udotenv.dotenv import load_dotenv

from ullmtools.core.apis.openaimtools import OpenAIMTools

from ullmtools.tools import (
    TurnOnOffLedTool,
    GetWeatherTool,
    Scheduler,
    ScheduleEventTool,
)

def render_template(filename, context):
    with open(filename, "r") as f:
        html = f.read()

    for key, value in context.items():
        html = html.replace("{{" + key + "}}", str(value))

    return html

class AssistantWebApp:

    def __init__(self):
        self.last_question = ""
        self.last_response = "Nenhuma pergunta enviada."
        self.queue = []
        self.llm = None
        self.scheduler = None
        self.is_processing = False  # Flag para controlar o estado do LLM

    def decode_url(self, text):
        text = text.replace("+", " ")
        encoded_bytes = bytearray()
        i = 0
        
        while i < len(text):
            if text[i] == '%' and i + 2 < len(text):
                try:
                    # Tenta converter o código hexadecimal
                    encoded_bytes.append(int(text[i+1:i+3], 16))
                    i += 3
                    continue
                except ValueError:
                    pass
            
            # Adiciona o caractere normal
            encoded_bytes.append(ord(text[i]))
            i += 1
            
        # Decodifica tudo junto como utf-8
        return encoded_bytes.decode('utf-8')

    def build_html(self):
        return  render_template(
            "./templates/index.html", {
                "QUESTION": self.last_question,
                "ANSWER": self.last_response
            }
        )

    def enqueue_message(self, text):
        self.queue.append(text)

    async def assistant_loop(self):
        while True:
            if self.queue:
                self.is_processing = True  # Sinaliza que começou a processar
                prompt = self.queue.pop(0)
                self.last_question = prompt

                try:
                    response = self.llm.chat(
                        prompt=prompt,
                        system_prompt=self.system_prompt,
                        tools=self.llm.get_tools_schema()
                    )

                    self.last_response = response["response"]

                except Exception as e:
                    self.last_response = "Erro: {}".format(e)

                gc.collect()
                self.is_processing = False  # Sinaliza que terminou de processar

            await asyncio.sleep(0.1)

    async def web_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("", 80))
        server.listen(3)
        
        # Torna o servidor não-bloqueante para o uasyncio poder rodar outras tarefas
        server.setblocking(False)

        print("Servidor HTTP iniciado")

        while True:
            try:
                conn, addr = server.accept()
            except OSError:
                # Se não houver conexão, cede tempo para o assistant_loop rodar
                await asyncio.sleep(0.1)
                continue

            try:
                # Evita que a leitura trave indefinidamente
                conn.settimeout(10.0)
                request = conn.recv(2048).decode("utf-8")

                if not request:
                    conn.close()
                    continue

                if "GET /favicon.ico" in request:
                    conn.send("HTTP/1.1 404 Not Found\r\n\r\n")
                    conn.close()
                    continue

                if "POST /" in request:
                    parts = request.split("\r\n\r\n")

                    if len(parts) > 1:
                        body = parts[1]

                        if "msg=" in body:
                            text = body.split("msg=")[1]
                            text = self.decode_url(text)
                            self.enqueue_message(text)

                            # Aguarda o assistant_loop processar esta mensagem antes de responder
                            while text in self.queue or self.is_processing:
                                await asyncio.sleep(0.5)

                html = self.build_html()

                conn.send("HTTP/1.1 200 OK\r\n")
                conn.send("Content-Type: text/html; charset=utf-8\r\n")
                conn.send("Connection: close\r\n\r\n")
                conn.sendall(html.encode("utf-8"))

                conn.close()

            except Exception as e:
                print("Erro servidor:", e)
                try:
                    conn.close()
                except:
                    pass

            await asyncio.sleep(0)

    async def setup_llm(self, api_key):

        self.system_prompt = (
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

        self.llm = OpenAIMTools(
            api_key=api_key,
            model="gpt-4o-mini",
            verbose=True
        )

        self.scheduler = Scheduler(
            tool_executor=self.llm.execute_tool
        )

        self.llm.set_scheduler(
            self.scheduler
        )

        schedule_tool = ScheduleEventTool(
            self.scheduler,
            verbose=True
        )

        weather_tool = GetWeatherTool()

        led_tool = TurnOnOffLedTool(
            pin=23
        )

        self.llm.register_tool(tool=schedule_tool)
        self.llm.register_tool(tool=weather_tool)
        self.llm.register_tool(tool=led_tool)

        asyncio.create_task(
            self.scheduler.run()
        )

    async def run(self, api_key):

        await self.setup_llm(api_key)

        asyncio.create_task(
            self.assistant_loop()
        )

        await self.web_server()


async def main():

    config = load_dotenv("env.txt")
    api_key = config.get("API_KEY")
    ssid = config.get("WIFI_SSID")
    password = config.get("WIFI_PASS")

    print("Conectando na rede:", ssid)

    connect_to_wifi(ssid, password)

    app = AssistantWebApp()

    await app.run(api_key)


asyncio.run(main())