import urequests
import ujson
import gc


# =========================================================
# OpenAI Client
# =========================================================

class OpenAI:

    def __init__(
        self,
        api_key,
        model="gpt-4o-mini",
        timeout=20,
        base_url="https://api.openai.com/v1/chat/completions"
    ):

        self.api_key = api_key
        self.model = model
        self.timeout = timeout

        self.base_url = base_url

    def _debug_mem(self, stage):

        try:
            print(
                "[openai]",
                stage,
                "mem_free=",
                gc.mem_free(),
                "mem_alloc=",
                gc.mem_alloc()
            )
        except Exception:
            print("[openai]", stage, "mem_unavailable")

    def _sleep_ms(self, milliseconds):

        try:
            import utime
            utime.sleep_ms(milliseconds)
            return
        except Exception:
            pass

        try:
            import time
            time.sleep(milliseconds / 1000)
        except Exception:
            pass

    def chat(
        self,
        prompt,
        system_prompt="You are a helpful assistant.",
        max_tokens=100,
        temperature=0.7,
        stream=True,
        callback=None,
        tools=None,
        keep_full_response=True
    ):

        stage = "chat_start"
        token_count = 0
        self._debug_mem(stage)
        print(
            "[openai] request model=",
            self.model,
            "stream=",
            stream,
            "keep_full_response=",
            keep_full_response,
            "prompt_len=",
            len(prompt)
        )

        stage = "build_payload"
        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream
        }
        
        if tools:
            data["tools"] = tools
        
        self._debug_mem(stage)

        stage = "serialize_payload"
        json_bytes = ujson.dumps(data).encode("utf-8")

        print("[openai] payload_bytes=", len(json_bytes))
        self._debug_mem(stage)
        
        # 2. Configure os cabeçalhos manualmente, incluindo o Content-Length exato
        stage = "build_headers"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.api_key,
            "Content-Length": str(len(json_bytes)) # <--- Essencial para o MicroPython
        }

        response = None

        try:

            stage = "http_post"
            self._debug_mem(stage)

            post_error = None

            for attempt in range(2):

                stage = "http_post_try_" + str(attempt + 1)

                gc.collect()
                self._debug_mem(
                    "http_post_pre_gc_try_" +
                    str(attempt + 1)
                )

                try:

                    response = urequests.post(
                        self.base_url,
                        headers=headers,
                        data=json_bytes,
                        stream=stream
                    )

                    self._debug_mem(
                        "http_post_done_try_" +
                        str(attempt + 1)
                    )
                    break

                except Exception as current_error:

                    post_error = current_error
                    print(
                        "[openai] post_error try=",
                        attempt + 1,
                        "error=",
                        current_error
                    )

                    if attempt == 0:
                        gc.collect()
                        self._debug_mem("http_post_retry_gc")
                        self._sleep_ms(250)
                        continue

            if response is None:
                raise Exception(post_error)

            # Release payload references after request is established.
            json_bytes = None
            data = None
            gc.collect()



            if response.status_code != 200:

                print("[openai] non_200 status=", response.status_code)

                raise Exception(
                    f"HTTP {response.status_code}: {response.text}"
                )

            # =================================================
            # STREAM MODE
            # =================================================

            if stream:

                stage = "stream_start"
                self._debug_mem(stage)

                if keep_full_response:
                    full_response = ""
                else:
                    full_response = None

                while True:

                    line = response.raw.readline()

                    if not line:
                        break

                    try:

                        line = line.decode("utf-8").strip()

                        # SSE lines start with:
                        # data: {...}

                        if not line.startswith("data: "):
                            continue

                        payload = line[6:]

                        if payload == "[DONE]":
                            break

                        json_line = ujson.loads(payload)

                        delta = (
                            json_line["choices"][0]
                            ["delta"]
                        )

                        token = delta.get("content", "")

                        if token:

                            token_count += 1

                            if token_count % 20 == 0:
                                self._debug_mem(
                                    "stream_tokens_" +
                                    str(token_count)
                                )

                            if keep_full_response:
                                full_response += token

                            if callback:
                                callback(token)
                            else:
                                print(token, end="")

                    except Exception as parse_error:
                        print(
                            "[openai] stream_parse_error:",
                            parse_error
                        )

                print()
                self._debug_mem("stream_end")

                if keep_full_response:
                    return {
                        "response": full_response
                    }

                return {
                    "response": ""
                }

            # =================================================
            # NORMAL MODE
            # =================================================

            stage = "normal_mode_parse_json"
            self._debug_mem(stage)

            result = response.json()

            message = (
                result["choices"][0]
                ["message"]
                ["content"]
            )

            if callback:
                callback(message)
            else:
                print(message)

            return {
                "response": message,
                "raw": result
            }

        except Exception as error:

            print("[openai] exception_stage=", stage)
            self._debug_mem("exception")

            raise Exception(
                f"OpenAI Error: {error}"
            )

        finally:

            if response:
                response.close()