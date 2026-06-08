import asyncio

from assistant.display.display_callback import (
    DisplayCallback
)



class ChatService:

    def __init__(
        self,
        llm,
        ui,
        player,
        display
    ):

        self.llm = llm
        self.ui = ui
        self.player = player

        self.callback = (
            DisplayCallback(
                display
            )
        )

    async def ask(
        self,
        question,
        tools=None
    ):

        self.callback.buffer = ""
        self.callback.started_response = False


        prompt = (
            "Voce e um mini assistente para um display OLED 128x64. "
            "Sua resposta sera exibida em uma unica linha com texto corrido. "
            "Responda de forma curta, clara e natural. "
            "Nao use acentuacao. "
            "Nao use markdown. "
            "Nao use emojis. "
            "Nao use listas. "
            "Use no maximo uma frase curta. "
            f"Pergunta do usuario: {question}"
            "\nAo agendar uma ferramenta utilize exatamente"
            "o nome registrado na lista de tools."
            "Exemplo: turn_onoff_led\n"
            "Nao utilize prefixos como:"
            "\n functions."
            "\n tools."
            "\n assistant."
        )

        result = self.llm.chat(
            prompt=prompt,
            stream=(tools is None),
            callback=self.callback.on_token,
            tools=tools
        )

        if not self.callback.started_response:

            response = result.get(
                "response",
                ""
            )

            if response:

                self.callback.on_token(
                    response
                )

        await asyncio.sleep(0.5)

        return result