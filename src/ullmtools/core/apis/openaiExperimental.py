import gc
import urequests
import ujson

from .llminterface import (
    LLMInterface, ChatState
)


class OpenAI(
    LLMInterface
):

    def __init__(
        self,
        api_key,
        model="gpt-4o-mini",
        timeout=20,
        base_url=(
            "https://api.openai.com/"
            "v1/chat/completions"
        ),
        verbose=False
    ):

        super().__init__(
            model_name=model
        )

        self.api_key = api_key
        self.timeout = timeout
        self.base_url = base_url
        self.verbose = verbose

    def _log(self, msg):
        if self.verbose:
            print(msg)

    def _build_request_data(
        self,
        max_tokens,
        temperature,
        tools
    ):

        data = {
            "model":
                self.model_name,
            "messages":
                self.messages,
            "max_tokens":
                max_tokens,
            "temperature":
                temperature,
            "stream":
                False
        }

        if tools:

            data["tools"] = tools
            data["tool_choice"] = "auto"

        return data

    def _post_chat_completion(
        self,
        data,
        log_prefix=""
    ):

        payload = b""

        try:

            payload = (
                ujson.dumps(
                    data
                ).encode(
                    "utf-8"
                )
            )

            self._log(
                "{}JSON OK".format(
                    log_prefix
                )
            )

            self._log(
                "[openai] {}payload size={}".format(
                    log_prefix,
                    len(payload)
                )
            )

        except Exception as e:

            self._log(
                "{}JSON ERROR: {}".format(
                    log_prefix,
                    e
                )
            )

            raise

        headers = {
            "Authorization":
                "Bearer {}".format(
                    self.api_key
                ),
            "Content-Type":
                "application/json",
            "Content-Length":
                str(len(payload))
        }

        gc.collect()

        response = None

        try:

            response = urequests.post(
                self.base_url,
                headers=headers,
                data=payload
            )

            if (
                response.status_code
                != 200
            ):

                raise Exception(
                    "HTTP {}: {}".format(
                        response.status_code,
                        response.text
                    )
                )

            result = (
                response.json()
            )

            self._log(
                "[openai] result received"
            )

            return result

        finally:

            del payload

            if response:
                try:
                    response.close()
                except:
                    pass

            gc.collect()

    def _parse_tool_arguments(
        self,
        tool_call
    ):

        raw_arguments = (
            tool_call[
                "function"
            ].get(
                "arguments",
                "{}"
            )
        )

        if isinstance(
            raw_arguments,
            str
        ):

            if not raw_arguments:
                return {}

            return ujson.loads(
                raw_arguments
            )

        if raw_arguments is None:
            return {}

        return raw_arguments

    def _execute_tool_calls(
        self,
        tool_calls
    ):

        self._state = (
            ChatState.CALLING_TOOLS
        )

        self.add_message(
            "assistant",
            None,
            tool_calls=tool_calls
        )

        for tool_call in tool_calls:

            function_name = (
                tool_call[
                    "function"
                ]["name"]
            )

            arguments = (
                self._parse_tool_arguments(
                    tool_call
                )
            )

            tool_result = (
                self.execute_tool(
                    function_name,
                    arguments
                )
            )

            self.add_tool_message(
                content=tool_result,
                tool_call_id=(
                    tool_call[
                        "id"
                    ]
                )
            )

            gc.collect()

    def chat(
        self,
        prompt,
        system_prompt=(
            "You are a helpful assistant."
        ),
        max_tokens=100,
        temperature=0.7,
        stream=False,
        callback=None,
        tools=None
    ):

        self._state = ChatState.CALLING_LLM
        max_tool_rounds = 5

        try:

            gc.collect()

            if not self.messages:

                self.add_system_message(
                    system_prompt
                )

            self.add_user_message(
                prompt
            )

            for round_index in range(
                max_tool_rounds + 1
            ):

                if round_index == 0:
                    self._state = (
                        ChatState.WAITING_RESPONSE
                    )
                    log_prefix = ""
                else:
                    self._state = (
                        ChatState.WAITING_TOOLS
                    )
                    log_prefix = "ROUND{} ".format(
                        round_index + 1
                    )

                data = (
                    self._build_request_data(
                        max_tokens,
                        temperature,
                        tools
                    )
                )

                result = (
                    self._post_chat_completion(
                        data,
                        log_prefix=log_prefix
                    )
                )

                if "error" in result:

                    raise Exception(
                        result[
                            "error"
                        ]
                    )

                message = (
                    result["choices"][0]
                    ["message"]
                )

                tool_calls = (
                    message.get(
                        "tool_calls"
                    )
                )

                if tool_calls:

                    if round_index >= max_tool_rounds:

                        raise Exception(
                            "Tool-calling exceeded {} rounds".format(
                                max_tool_rounds
                            )
                        )

                    self._execute_tool_calls(
                        tool_calls
                    )

                    continue

                content = (
                    message.get(
                        "content",
                        ""
                    )
                )

                self.add_assistant_message(
                    content
                )

                if callback:

                    callback(
                        content
                    )

                self.clear_history()

                gc.collect()

                self._state = (
                    ChatState.RESPONSE_READY
                )

                return {
                    "response":
                        content,
                    "raw":
                        result
                }

            raise Exception(
                "No final assistant response returned"
            )

        except Exception as error:

            raise Exception(
                "OpenAI Error: {}".format(
                    error
                )
            )

        finally:

            gc.collect()




import gc
import network
import re
import time
import ntptime

import urequests
import ujson

def _log(msg, verbose):
    if verbose is True:
        print(msg)
# =========================================================
# WiFi
# =========================================================


def conectar_wifi(ssid, password):

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():

        print(f"Conectando em: {ssid}")

        wlan.connect(ssid, password)

        tentativas = 0

        while not wlan.isconnected() and tentativas < 10:
            time.sleep(1)
            tentativas += 1
            print(".", end="")

    if wlan.isconnected():

        print("\nWiFi conectado")
        print(wlan.ifconfig())
        time.sleep(1)
        
        try:        
            ntptime.settime()
            print("Local time after synchronization：%s" %str(time.localtime()))
            print(time.gmtime())
            print(time.time())
        except Exception as error:
            print(f"[wifi] NTPTime sinc fail: {error}")
            
        


        return True

    print("\nFalha no WiFi")

    return False

    
        
    

if __name__ == "__main__":
    
    # SSID_REDE = "NOTE-646635 1412"
    # SENHA_REDE = "798-y6N1"
    SSID_REDE = "RedeGamer"
    SENHA_REDE = "Vick0508"
    
    print(f"Conectando na rede: {SSID_REDE}")
    conectar_wifi(
        SSID_REDE,
        SENHA_REDE
    )
    

    def get_temperature(city):
        return "28 graus Celsius em {}".format(city)

    GET_TEMPERATURE_SCHEMA = {
        "type": "function",
        "function": {
            "name": "get_temperature",
            "description": "Retorna a temperatura atual de uma cidade.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Nome da cidade"
                    }
                },
                "required": ["city"]
            }
        }
    }

    API_KEY = "YOUR_OPENAI_API_KEY"

    if API_KEY == "YOUR_OPENAI_API_KEY":
        print("Defina API_KEY no exemplo antes de executar.")
    else:
        llm = OpenAI(
            api_key=API_KEY,
            model="gpt-4o-mini",
            verbose=True
        )

        llm.register_tool(
            name="get_temperature",
            func=get_temperature,
            schema=GET_TEMPERATURE_SCHEMA
        )

        response = llm.chat(
            prompt="Qual a temperatura em Sao Paulo?",
            tools=llm.get_tools_schema()
        )

        print("Resposta final:")
        print(response["response"])
