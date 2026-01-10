from langchain_core.messages import AIMessage, HumanMessage


class ChatHistory:
    def __init__(self):
        self.history = []

    def build_chat_history(
        self, history: list[HumanMessage | AIMessage]
    ) -> list[HumanMessage | AIMessage]:
        output_history: list[HumanMessage | AIMessage] = []

        for message in history:
            if message.type == "human":
                output_history.append(HumanMessage(content=message.content))
            else:
                output_history.append(AIMessage(content=message.content))

        return output_history
