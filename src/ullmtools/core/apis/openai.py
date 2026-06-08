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
        response = None

        try:

            # --------------------------------
            # Histórico
            # --------------------------------

            if not self.messages:

                self.add_system_message(
                    system_prompt
                )

            self.add_user_message(
                prompt
            )



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

                data["tools"] = (
                    tools
                )

                data[
                    "tool_choice"
                ] = "auto"

            self._state = ChatState.WAITING_RESPONSE
            
            payload = b""

            try:
                payload = ujson.dumps(data).encode(
                    "utf-8"
                    )
                self._log("JSON OK")
            except Exception as e:
                self._log(f"JSON ERROR: {e}")
                
            self._log(f"[openai] payload: {payload}")

            self._log(f"[openai] Type payload: {type(payload)}")
            
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
            
            self._log(f"[openai] result:\n{result}")

            message = (
                result["choices"][0]
                ["message"]
            )

            # --------------------------------
            # Tool Calling
            # --------------------------------

            tool_calls = (
                message.get(
                    "tool_calls"
                )
            )

            response.close()

            if tool_calls:

                self._state = ChatState.CALLING_TOOLS

                self.add_message(
                    "assistant",
                    None,
                    tool_calls=tool_calls
                )

                for tool_call in (
                    tool_calls
                ):

                    function_name = (
                        tool_call[
                            "function"
                        ]["name"]
                    )

                    arguments = (
                        ujson.loads(
                            tool_call[
                                "function"
                            ][
                                "arguments"
                            ]
                        )
                    )

                    tool_result = (
                        self.execute_tool(
                            function_name,
                            arguments
                        )
                    )

                    self.add_tool_message(
                        content=(
                            tool_result
                        ),
                        tool_call_id=(
                            tool_call[
                                "id"
                            ]
                        ),
#                         name=(
#                             function_name
#                         )
                    )

                second_data = {
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
                    second_data["tools"] = tools
                    second_data["tool_choice"] = "auto"

                
                
                self._log("[openai] second messages")
                self._log(self.messages)
                self._state = ChatState.WAITING_TOOLS


                payload2 = b""

                try:
                    payload2 = ujson.dumps(second_data).encode(
                    "utf-8"
                    )
                    self._log("SECOND JSON OK")
                    self._log(payload2)
                except Exception as e:
                    self._log(f"SECOND JSON ERROR: {e}")
                    
                
                headers = {
                    "Authorization":
                        "Bearer {}".format(
                            self.api_key
                        ),
                    "Content-Type":
                        "application/json",
                    "Content-Length":
                        str(len(payload2))
                }

                second_response = (
                    urequests.post(
                        self.base_url,
                        headers=headers,
                        data=payload2
                    )
                )

                second_result = (
                    second_response
                    .json()
                )

                self._state = ChatState.RESPONSE_READY
                
                if "error" in second_result:

                    raise Exception(
                        second_result["error"]
                    )
                
                self._log(
                    "[openai] second_result:"
                )

                self._log(
                    second_result
                )

                second_response.close()

                final_content = (
                    second_result
                    ["choices"][0]
                    ["message"]
                    ["content"]
                )

                self.add_assistant_message(
                    final_content
                )

                if callback:
                    callback(
                        final_content
                    )

                self.clear_history()
                return {
                    "response":
                        final_content,
                    "raw":
                        second_result
                }

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
                callback(content)

            self.clear_history()

            self._state = ChatState.RESPONSE_READY

            return {
                "response":
                    content,
                "raw":
                    result
            }

        except Exception as error:

            raise Exception(
                "OpenAI Error: {}".format(
                    error
                )
            )

        finally:

            if response:
                self._state = ChatState.RESPONSE_READY
                self.clear_history()
                response.close()