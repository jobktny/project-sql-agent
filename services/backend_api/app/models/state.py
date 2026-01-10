from typing import Annotated, Literal

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel


class State(BaseModel):
    messages: Annotated[list, add_messages] = []

    # selected_agent: Optional[str] = None
    history: list[HumanMessage | AIMessage] = []
    sql_query: str = ""
    sql_query_execution_status: Literal["success", "failure"] = "failure"
    sql_error_count: int = 0
    sql_query_error: str = ""
    sql_result: str = ""
    # sql_agent_answer: str = ""
    agent_answer: str = ""
    need_visualise: bool = False
    chit_chat: bool = False
    out_of_policy: bool = False

    class Config:
        arbitrary_types_allowed = True
