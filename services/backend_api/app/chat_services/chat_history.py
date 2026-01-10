from app.models.chat_models import History
from langchain_core.messages import AIMessage, HumanMessage


class ChatHistory:
    def __init__(self):
        self.history = []

    def build_chat_history(
        self, history: list[History]
    ) -> list[HumanMessage | AIMessage]:
        output_history: list[HumanMessage | AIMessage] = []

        for message in history:
            if message.actor == "user":
                output_history.append(HumanMessage(content=message.message))
            else:
                output_history.append(AIMessage(content=message.message))

        return output_history
