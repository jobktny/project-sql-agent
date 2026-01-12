from app.chat_services.chat_history import ChatHistory
from app.chat_services.graph import GraphBuilder
from app.models.chat_models import History
from app.models.state import State
from fastapi import Depends


class ChatService:
    def __init__(
        self,
        history: ChatHistory = Depends(ChatHistory),
        graph_builder: GraphBuilder = Depends(GraphBuilder),
    ):
        self.graph = graph_builder.build_graph()
        self.history = history

    def chat_flow(self, message: str, history: list[History]):
        history = self.history.build_chat_history(history)
        state = State(message=message, history=history)
        result = self.graph.invoke(state)
        print(result)
        return result
