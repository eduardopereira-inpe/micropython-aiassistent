"""OpenAI Chat Completions client with tool-calling support for MicroPython.

Overview
--------
This module implements an `LLMInterface` adapter that talks to the OpenAI
Chat Completions API. It is designed for constrained devices and keeps
memory usage explicit with frequent garbage collection and short-lived buffers.

Responsibilities
----------------
- Build request payloads for chat completion.
- Execute HTTP calls against the configured OpenAI endpoint.
- Parse and execute model-requested tool calls.
- Keep a bounded tool-calling loop to avoid infinite conversations.

Execution Flow
--------------
1. Initialize system/user messages.
2. Send chat completion request.
3. If tool calls are returned, execute tools and append tool messages.
4. Repeat until final assistant content is produced or round limit is hit.

Notes for Embedded Usage
------------------------
- JSON payloads are encoded once per request to reduce temporary objects.
- HTTP responses are always closed in `finally` blocks.
- `gc.collect()` is intentionally used at key points to free RAM.
"""

import gc
try:
    import urequests  # type: ignore
except ImportError:
    import requests as urequests

try:
    import ujson  # type: ignore
except ImportError:
    import json as ujson

from .llminterface import (
    LLMInterface, ChatState
)


class OpenAIMTools(
    LLMInterface
):
    """OpenAI implementation of `LLMInterface` with optional tool-calling.

    The class stores conversation history in the inherited message list,
    sends requests to the OpenAI Chat Completions endpoint, and orchestrates
    tool execution rounds before returning a final assistant response.
    """

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
        """Create a new API client.

        Args:
            api_key: OpenAI API key used in the Authorization header.
            model: Model identifier used in chat requests.
            timeout: Reserved timeout value for future transport handling.
            base_url: Full URL of the chat completions endpoint.
            verbose: Enables diagnostic logging when True.
        """

        super().__init__(
            model_name=model
        )

        self.api_key = api_key
        self.timeout = timeout
        self.base_url = base_url
        self.verbose = verbose

    def _log(self, msg):
        """Print a diagnostic message only when verbose mode is enabled."""
        if self.verbose:
            print(msg)

    def _build_request_data(
        self,
        max_tokens,
        temperature,
        tools
    ):
        """Build the JSON-serializable request body for chat completion.

        Args:
            max_tokens: Maximum number of output tokens.
            temperature: Sampling temperature for response variability.
            tools: Optional tool schema list following OpenAI format.

        Returns:
            dict: Request payload ready to be JSON-encoded.
        """

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
        """Send a chat completion request and return parsed JSON response.

        Args:
            data: Request payload dictionary.
            log_prefix: Optional prefix for debug log grouping.

        Returns:
            dict: Parsed response from OpenAI.

        Raises:
            Exception: On JSON encoding errors, HTTP errors, or transport
                failures.
        """

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
        """Normalize tool-call argument payload into a dictionary.

        OpenAI may return `function.arguments` as a JSON string, as a dict,
        or as null. This method normalizes all valid variants.
        """

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
        """Execute model-requested tools and append tool messages.

        Args:
            tool_calls: List of tool call descriptors returned by the model.
        """

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
        """Run a full chat turn with optional iterative tool-calling.

        Args:
            prompt: User prompt for this turn.
            system_prompt: System instruction used when history is empty.
            max_tokens: Maximum response tokens for each model round.
            temperature: Sampling temperature for each model round.
            stream: Present for interface compatibility; not used here.
            callback: Optional callback receiving final assistant text.
            tools: Optional list of OpenAI tool schemas.

        Returns:
            dict: `{"response": <text>, "raw": <full_api_response>}`.

        Raises:
            Exception: Wrapped as `OpenAI Error: ...` when any step fails.
        """

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

