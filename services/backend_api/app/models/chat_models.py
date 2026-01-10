from typing import Annotated

from pydantic import BaseModel, Field


class History(BaseModel):
    query: str
    response: str


class ChatRequest(BaseModel):
    history: list[History] = []
    message: str
    user_id: str


class ChatResponse(BaseModel):
    message: str


class QueryOutput(BaseModel):
    generated_sql_query: Annotated[
        str, Field(description="Syntactically valid SQL query.")
    ]
    need_visualise: Annotated[
        bool,
        Field(
            description="Whether the user wants to visualize the data. Set to True if the user's question mentions visualization, plotting, graphing, charts, or similar terms."
        ),
    ]
    chit_chat: Annotated[
        bool,
        Field(
            description="Whether the query is a chit chat. Set to True if the query is a chit chat."
        ),
    ]
    out_of_policy: Annotated[
        bool,
        Field(
            description="Whether the query is not about query the data in database. Set to True if the query is not allowed to be executed."
        ),
    ]
