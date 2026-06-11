import urequests
import ujson

from .llminterface import (
    LLMInterface
)


class Ollama(
    LLMInterface
):

    def __init__(
        self,
        url="http://192.168.137.1",
        port="11434",
        model="gemma4:e2b",
        timeout=10
    ):

        super().__init__(
            model_name=model
        )

        self.timeout = timeout

        self._chat_url = (
            "{}:{}/api/chat".format(
                url,
                port
            )
        )

    def chat(
        self,
        prompt,
        system_prompt=(
            "You are a helpful assistant."
        ),
        stream=False,
        callback=None,
        tools=None
    ):

        response = None

        try:

            # ----------------------------
            # Histórico
            # ----------------------------

            if not self.messages:

                self.add_system_message(
                    system_prompt
                )

            self.add_user_message(
                prompt
            )

            if tools:
                stream = False

            data = {
                "model":
                    self.model_name,
                "messages":
                    self.messages,
                "stream":
                    stream
            }

            if tools:

                data["tools"] = (
                    tools
                )

            response = (
                urequests.post(
                    self._chat_url,
                    json=data
                )
            )

            response.raw.settimeout(
                self.timeout
            )

            # ----------------------------
            # Streaming
            # ----------------------------

            if stream:

                full_response = ""

                while True:

                    line = (
                        response.raw
                        .readline()
                    )

                    if not line:
                        break

                    try:

                        json_line = (
                            ujson.loads(
                                line
                            )
                        )

                        message = (
                            json_line.get(
                                "message",
                                {}
                            )
                        )

                        token = (
                            message.get(
                                "content",
                                ""
                            )
                        )

                        if token:

                            full_response += (
                                token
                            )

                            if callback:

                                callback(
                                    token
                                )

                        if (
                            json_line.get(
                                "done",
                                False
                            )
                        ):
                            break

                    except:
                        pass

                self.add_assistant_message(
                    full_response
                )

                return {
                    "response":
                        full_response
                }

            # ----------------------------
            # Resposta normal
            # ----------------------------

            result = (
                response.json()
            )

            message = (
                result.get(
                    "message",
                    {}
                )
            )

            tool_calls = (
                message.get(
                    "tool_calls"
                )
            )
            
            response.close()

            # ----------------------------
            # Tool Calling
            # ----------------------------

            if tool_calls:

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
                        tool_call[
                            "function"
                        ].get(
                            "arguments",
                            {}
                        )
                    )

                    tool_result = (
                        self.execute_tool(
                            function_name,
                            arguments
                        )
                    )

                    self.add_tool_message(
                        content=
                            tool_result,
                        name=
                            function_name
                    )

                second_data = {
                    "model":
                        self.model_name,
                    "messages":
                        self.messages,
                    "stream":
                        False
                }

                second_response = (
                    urequests.post(
                        self._chat_url,
                        json=second_data
                    )
                )

                second_result = (
                    second_response
                    .json()
                )

                second_response.close()

                final_content = (
                    second_result
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

                return {
                    "response":
                        final_content,
                    "raw":
                        second_result
                }

            # ----------------------------
            # Resposta comum
            # ----------------------------

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

            return {
                "response":
                    content,
                "raw":
                    result
            }

        except Exception as error:

            raise Exception(
                "Ollama Error: {}".format(
                    error
                )
            )

        finally:

            if response:

                response.close()