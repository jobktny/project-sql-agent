from app.chat_services.graph import GraphBuilder
from app.models.state import State
from fastapi import Depends


class ChatService:
    def __init__(self, graph_builder: GraphBuilder = Depends(GraphBuilder)):
        self.graph = graph_builder.get_graph()

    def chat_flow(self, user_message: str):
        state = State(user_message=user_message)
        result = self.graph.invoke(state)
        print(result)
        return result
