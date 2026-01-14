from typing import Annotated, Literal

from langgraph.graph.message import add_messages
from pydantic import BaseModel


class State(BaseModel):
    messages: Annotated[list, add_messages] = []
    # message: str = ""  # fastapi approach

    # history: list[HumanMessage | AIMessage] = []  # langgraph approach
    sql_query: str = ""
    sql_query_execution_status: Literal["success", "failure"] = "failure"
    sql_error_count: int = 0
    sql_query_error: str = ""
    sql_result: str = ""
    agent_answer: str = ""
    need_visualise: bool = False
    chit_chat: bool = False
    out_of_policy: bool = False
