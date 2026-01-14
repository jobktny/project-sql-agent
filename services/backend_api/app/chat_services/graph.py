from app.chat_services.agents import (
    Agent,
)
from app.models.state import State
from fastapi import Depends
from langgraph.graph import END, StateGraph


class GraphBuilder:
    def __init__(self, agent: Agent = Depends(Agent)) -> None:
        self.agent = agent

        self.workflow = StateGraph(State)

        self.workflow.add_node("write_query", agent.write_query)
        self.workflow.add_node("execute_query", agent.execute_query)
        self.workflow.add_node("generate_answer", agent.generate_answer)
        self.workflow.add_node("cannot_answer", agent.cannot_answer)
        self.workflow.add_node("plot_agent", agent.plot_agent)
        self.workflow.add_node("chat_agent", agent.chat_agent)

        # flow start here
        self.workflow.set_entry_point("write_query")
        self.workflow.add_conditional_edges(
            "write_query",
            self.chat_router,
            ["chat_agent", "execute_query", "cannot_answer"],
        )
        self.workflow.add_conditional_edges(
            "execute_query",
            self.query_router,
            ["generate_answer", "cannot_answer", "plot_agent", "write_query"],
        )
        # flow end here
        self.workflow.add_edge("chat_agent", END)
        self.workflow.add_edge("plot_agent", END)
        self.workflow.add_edge("generate_answer", END)
        self.workflow.add_edge("cannot_answer", END)

    def build_graph(self) -> StateGraph:
        return self.workflow.compile()

    def chat_router(self, state: State):
        if state.chit_chat:
            return "chat_agent"
        elif state.out_of_policy:
            return "cannot_answer"
        else:
            return "execute_query"

    def query_router(self, state: State):
        """Routes to generate_answer, cannot_answer, plot_agent or write_query based on query_execution_status."""
        if state.sql_query_execution_status == "success":
            if state.need_visualise:
                return "plot_agent"
            else:
                return "generate_answer"

        elif state.sql_query_execution_status == "failure":
            if state.sql_error_count < 2:
                return "write_query"

            else:
                return "cannot_answer"
