try:
    import usocket as socket
except ImportError:
    import socket

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import gc

from ullmtools.core.apis.llminterface import LLMInterface


def render_template(filename, context):

    with open(filename, "r") as f:
        html = f.read()

    for key, value in context.items():
        html = html.replace(
            "{{" + key + "}}",
            str(value)
        )

    return html


class WebService:

    llm: "LLMInterface"

    def __init__(
        self,
        template_path="./templates/index.html"
    ):

        self.last_question = ""
        self.last_response = (
            "Nenhuma pergunta enviada."
        )

        self.system_prompt = ""

        self.scheduler = None

        self.template_path = (
            template_path
        )

    def decode_url(self, text):

        text = text.replace(
            "+",
            " "
        )

        encoded_bytes = bytearray()

        i = 0

        while i < len(text):

            if (
                text[i] == "%"
                and i + 2 < len(text)
            ):

                try:

                    encoded_bytes.append(
                        int(
                            text[i + 1:i + 3],
                            16
                        )
                    )

                    i += 3

                    continue

                except ValueError:

                    pass

            encoded_bytes.extend(
                text[i].encode("utf-8")
            )

            i += 1

        return encoded_bytes.decode(
            "utf-8"
        )

    def build_html(self):

        return render_template(
            self.template_path,
            {
                "QUESTION":
                    self.last_question,
                "ANSWER":
                    self.last_response
            }
        )

    async def process_message(
        self,
        text
    ):

        self.last_question = text

        try:

            response = self.llm.chat(
                    prompt=text,
                    system_prompt=(
                        self.system_prompt
                    ),
                    tools=(
                        self.llm
                        .get_tools_schema()
                    )
                )
            

            self.last_response = (
                response.get(
                    "response",
                    "Resposta vazia."
                )
            )

        except Exception as e:

            self.last_response = (
                "Erro: {}".format(e)
            )

        finally:

            gc.collect()

    async def web_server(self):

        server = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        server.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        server.bind(
            ("", 80)
        )

        server.listen(3)

        server.setblocking(False)

        print(
            "Servidor HTTP iniciado"
        )

        while True:

            try:

                conn, addr = (
                    server.accept()
                )

            except OSError:

                await asyncio.sleep(0.1)

                continue

            try:

                conn.settimeout(30)

                request = conn.recv(
                    4096
                )

                if not request:

                    conn.close()

                    continue

                request = request.decode(
                    "utf-8"
                )

                if (
                    "GET /favicon.ico"
                    in request
                ):

                    conn.sendall(
                        b"HTTP/1.1 404 Not Found\r\n\r\n"
                    )

                    conn.close()

                    continue

                if "POST /" in request:

                    parts = request.split(
                        "\r\n\r\n"
                    )

                    if len(parts) > 1:

                        body = parts[1]

                        if (
                            "msg="
                            in body
                        ):

                            text = (
                                body.split(
                                    "msg="
                                )[1]
                            )

                            if "&" in text:
                                text = (
                                    text.split(
                                        "&"
                                    )[0]
                                )

                            text = (
                                self.decode_url(
                                    text
                                )
                            )

                            print(
                                "Pergunta:",
                                text
                            )

                            #
                            # AGUARDA A RESPOSTA
                            #
                            await self.process_message(
                                text
                            )

                            print(
                                "Resposta pronta"
                            )

                html = self.build_html()

                body = html.encode(
                    "utf-8"
                )

                headers = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/html; charset=utf-8\r\n"
                    "Content-Length: {}\r\n"
                    "Connection: close\r\n\r\n"
                ).format(
                    len(body)
                )

                conn.sendall(
                    headers.encode(
                        "utf-8"
                    )
                )

                conn.sendall(body)

            except Exception as e:

                print(
                    "Erro servidor:",
                    e
                )

            finally:

                try:
                    conn.close()
                except:
                    pass

            await asyncio.sleep(0)

    def setup_llm(
        self,
        llm,
        scheduler,
        system_prompt=""
    ):

        self.llm = llm

        self.scheduler = (
            scheduler
        )

        self.system_prompt = (
            system_prompt
        )

        self.llm.set_scheduler(
            self.scheduler
        )

        asyncio.create_task(
            self.scheduler.run()
        )

    async def run(
        self,
        llm,
        scheduler,
        system_prompt=""
    ):

        self.setup_llm(
            llm=llm,
            scheduler=scheduler,
            system_prompt=(
                system_prompt
            )
        )

        await self.web_server()
