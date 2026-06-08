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

            gc.collect()

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

                payload = (
                    ujson.dumps(
                        data
                    ).encode(
                        "utf-8"
                    )
                )

                del data

                gc.collect()

                self._log("JSON OK")
                self._log(
                    "[openai] payload size={}".format(
                        len(payload)
                    )
                )

            except Exception as e:

                self._log(
                    "JSON ERROR: {}".format(
                        e
                    )
                )

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

            response = urequests.post(
                self.base_url,
                headers=headers,
                data=payload
            )

            del payload

            gc.collect()

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

            message = (
                result["choices"][0]
                ["message"]
            )

            tool_calls = (
                message.get(
                    "tool_calls"
                )
            )

            response.close()
            response = None

            if tool_calls:

                self._state = (
                    ChatState.CALLING_TOOLS
                )

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
                        )
                    )

                    gc.collect()

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

                    second_data["tools"] = (
                        tools
                    )

                    second_data[
                        "tool_choice"
                    ] = "auto"

                self._state = (
                    ChatState.WAITING_TOOLS
                )

                payload2 = b""

                try:

                    payload2 = (
                        ujson.dumps(
                            second_data
                        ).encode(
                            "utf-8"
                        )
                    )

                    del second_data

                    gc.collect()

                    self._log(
                        "SECOND JSON OK"
                    )

                    self._log(
                        "[openai] payload2 size={}".format(
                            len(payload2)
                        )
                    )

                except Exception as e:

                    self._log(
                        "SECOND JSON ERROR: {}".format(
                            e
                        )
                    )

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

                gc.collect()

                second_response = (
                    urequests.post(
                        self.base_url,
                        headers=headers,
                        data=payload2
                    )
                )

                del payload2

                gc.collect()

                second_result = (
                    second_response
                    .json()
                )

                second_response.close()

                self._state = (
                    ChatState.RESPONSE_READY
                )

                if (
                    "error"
                    in second_result
                ):

                    raise Exception(
                        second_result[
                            "error"
                        ]
                    )

                second_message = (
                    second_result[
                        "choices"
                    ][0][
                        "message"
                    ]
                )

                second_tool_calls = (
                    second_message.get(
                        "tool_calls"
                    )
                )

                if second_tool_calls:

                    self.add_message(
                        "assistant",
                        None,
                        tool_calls=(
                            second_tool_calls
                        )
                    )

                    for tool_call in (
                        second_tool_calls
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
                            )
                        )

                        gc.collect()

                    third_data = {
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

                        third_data[
                            "tools"
                        ] = tools

                        third_data[
                            "tool_choice"
                        ] = "auto"

                    payload3 = (
                        ujson.dumps(
                            third_data
                        ).encode(
                            "utf-8"
                        )
                    )

                    del third_data

                    gc.collect()

                    headers = {
                        "Authorization":
                            "Bearer {}".format(
                                self.api_key
                            ),
                        "Content-Type":
                            "application/json",
                        "Content-Length":
                            str(
                                len(
                                    payload3
                                )
                            )
                    }

                    third_response = (
                        urequests.post(
                            self.base_url,
                            headers=headers,
                            data=payload3
                        )
                    )

                    del payload3

                    gc.collect()

                    third_result = (
                        third_response
                        .json()
                    )

                    third_response.close()

                    if (
                        "error"
                        in third_result
                    ):

                        raise Exception(
                            third_result[
                                "error"
                            ]
                        )

                    final_content = (
                        third_result[
                            "choices"
                        ][0][
                            "message"
                        ].get(
                            "content",
                            ""
                        )
                    )

                    raw_result = (
                        third_result
                    )

                else:

                    final_content = (
                        second_message.get(
                            "content",
                            ""
                        )
                    )

                    raw_result = (
                        second_result
                    )

                self.add_assistant_message(
                    final_content
                )

                if callback:

                    callback(
                        final_content
                    )

                self.clear_history()

                gc.collect()

                return {
                    "response":
                        final_content,
                    "raw":
                        raw_result
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

        except Exception as error:

            raise Exception(
                "OpenAI Error: {}".format(
                    error
                )
            )

        finally:

            gc.collect()

            if response:

                self._state = (
                    ChatState.RESPONSE_READY
                )

                self.clear_history()

                try:
                    response.close()
                except:
                    pass

                gc.collect()