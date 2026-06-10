class ChatState:
    CALLING_LLM = 1
    WAITING_LLM = 2
    CALLING_TOOLS = 3
    WAITING_TOOLS = 4
    WAITING_RESPONSE = 5
    RESPONSE_READY = 6

class LLMInterface:

    def __init__(
        self,
        model_name,
        max_message_history=4
    ):

        self.model_name = model_name

        self.max_message_history = (
            max_message_history
        )

        self._messages = []

        self._tools = {}
        self._scheduler = None
        self._state = ChatState.CALLING_LLM

    @property
    def state(self):
        return self._state

    @property
    def messages(self):

        return self._messages
    
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
        raise NotImplementedError(
            "Subclasses must implement the chat method to interact with specific LLMs and tools."
        )

    def clear_history(self):

        self._messages = []

    def _trim_history(self):

        max_messages = (
            self.max_message_history * 4
        )

        while (
            len(self._messages)
            > max_messages
        ):
            self._messages.pop(0)

    def add_message(
        self,
        role,
        content=None,
        **kwargs
    ):

        message = {
            "role": role
        }

        if content is not None:
            message["content"] = content

        for key, value in kwargs.items():
            message[key] = value

        self._messages.append(
            message
        )

        self._trim_history()

    def add_system_message(
        self,
        content
    ):

        self.add_message(
            "system",
            content
        )

    def add_user_message(
        self,
        content
    ):

        self.add_message(
            "user",
            content
        )

    def add_assistant_message(
        self,
        content
    ):

        self.add_message(
            "assistant",
            content
        )

    def add_tool_message(
        self,
        content,
        tool_call_id=None,
        name=None
    ):

        message = {
            "role": "tool",
            "content": str(content)
        }

        if tool_call_id:
            message[
                "tool_call_id"
            ] = tool_call_id

        if name:
            message["name"] = name

        self._messages.append(
            message
        )

        self._trim_history()

    def register_tool(
        self,
        name=None,
        func=None,
        schema=None,
        tool=None
    ):

        if tool is not None:
            name = tool.name
            func = tool
            schema = tool.schema

        if name is None or func is None or schema is None:
            raise ValueError(
                "register_tool requires name, func and schema, or a tool object"
            )

        self._tools[name] = {
            "function": func,
            "schema": schema
        }

    def execute_tool(
        self,
        name,
        arguments
    ):

        if name not in self._tools:

            raise Exception(
                "Tool '{}' not found".format(
                    name
                )
            )

        return (
            self._tools[name]
            ["function"](
                **arguments
            )
        )

    def get_tools_schema(self):

        schemas = []

        for tool in (
            self._tools.values()
        ):
            schemas.append(
                tool["schema"]
            )

        return schemas
    
    def set_scheduler(
        self,
        scheduler
    ):

        self._scheduler = scheduler