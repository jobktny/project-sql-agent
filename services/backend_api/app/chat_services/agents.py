from app.config import GROQ_MODEL, Config
from app.models.chat_models import QueryOutput
from app.models.state import State
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from sqlalchemy import create_engine

config = Config()


class Agent:
    def __init__(self):
        db_uri = config.DATABASE_URI()
        engine = create_engine(db_uri)
        self.db = SQLDatabase(engine)

    def chat_agent(self, state: State):
        user_message = state.messages[-1].content  # langgraph approach
        system_message = """
        /no_think
        You are a simple chat agent. You are given a user's message and you need to answer the question. and handle the simple message like greeting, farewell, etc.
        You will remind that you will need to keep the conversation about the subject of the database. need customer to query the data in the database.
        use the following tables:
        {table_info}
        """
        user_prompt = """
        User message: {user_message}
        """
        general_agent_prompt_template = ChatPromptTemplate(
            [("system", system_message), ("user", user_prompt)]
        )

        formatted_prompt = general_agent_prompt_template.invoke(
            {
                "table_info": self.db.get_table_info(),
                "user_message": user_message,
            }
        )

        # prompt = state.history + formatted_prompt.messages # fastapi approach
        prompt = list(state.messages) + formatted_prompt.messages

        llm = ChatGroq(model=GROQ_MODEL, groq_api_key=Config.groq_api_key)
        response = llm.invoke(prompt)

        return {
            # "agent_answer": response.content, # fastapi approach
            "messages": [AIMessage(content=response.content)],
        }

    def write_query(self, state: State):
        user_message = state.messages[-1].content  # langgraph approach
        system_message = """
        You are a SQL query agent. You are given a user's message and you need to create a syntactically correct {dialect} query to run to help find the answer.
        You will also need to determine if the user wants to visualise the data. If so, you will need to set the need_visualise flag to True.
        Never query for all the columns from a specific table, only ask for a few relevant columns given the question.
        Pay attention to use only the column names that you can see in the schema description.
        Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
        Only use the following tables:
        {table_info}
        If the user's message is not about the data in the database, you should set the out_of_policy flag to True.
        If the user's message is a chit chat, you should set the chit_chat flag to True.
        """
        user_prompt = """
        Question: {input}
        Use the following error information if there is any: {query_error}
        """
        query_prompt_template = ChatPromptTemplate(
            [("system", system_message), ("user", user_prompt)]
        )
        try:
            formatted_prompt = query_prompt_template.invoke(
                {
                    "dialect": self.db.dialect,
                    "table_info": self.db.get_table_info(),
                    "input": user_message,
                    "query_error": state.sql_query_error or "None",
                }
            )

            prompt = (
                list(state.messages) + formatted_prompt.messages
            )  # langgraph approach
            # prompt = state.history + formatted_prompt.messages # fastapi approach

            llm = ChatGroq(model=GROQ_MODEL, groq_api_key=Config.groq_api_key)
            structured_llm = llm.with_structured_output(QueryOutput)
            result = structured_llm.invoke(prompt)

            # If it's chit-chat or out of policy, return early with appropriate flags
            # (chit-chat and out_of_policy don't need SQL queries)
            if result.chit_chat or result.out_of_policy:
                return {
                    "sql_query": "",
                    "sql_query_execution_status": "success",
                    "sql_query_error": "",
                    "sql_error_count": 0,
                    "chit_chat": result.chit_chat,
                    "out_of_policy": result.out_of_policy,
                    "need_visualise": False,
                }

            # Validate that we got a SQL query for non-chit-chat queries
            if (
                not result.generated_sql_query
                or result.generated_sql_query.strip() == ""
            ):
                return {
                    "sql_query": "",
                    "sql_query_execution_status": "failure",
                    "sql_query_error": "Error: Generated SQL query is empty",
                    "sql_error_count": state.sql_error_count + 1,
                }

        except Exception as e:
            error_msg = str(e)
            if hasattr(e, "response") and hasattr(e.response, "body"):
                # Try to extract more detailed error message
                try:
                    import json

                    error_body = json.loads(e.response.body)
                    if "error" in error_body and "failed_generation" in error_body.get(
                        "error", {}
                    ):
                        error_msg = error_body["error"]["failed_generation"]
                except:
                    pass

            return {
                "sql_query": "",
                "sql_query_execution_status": "failure",
                "sql_query_error": f"Error generating query: {error_msg}",
                "sql_error_count": state.sql_error_count + 1,
            }

        return {
            "sql_query": result.generated_sql_query,
            "need_visualise": result.need_visualise,
            "out_of_policy": result.out_of_policy,
            "chit_chat": result.chit_chat,
            "sql_query_execution_status": "success",
            "sql_query_error": "",
            "sql_error_count": 0,
        }

    def execute_query(self, state: State):
        """Execute SQL query and set query_execution_status."""
        # Check if SQL query is empty
        if not state.sql_query or state.sql_query.strip() == "":
            return {
                "sql_result": "",
                "sql_query_execution_status": "failure",
                "sql_query_error": "Error: Cannot execute an empty SQL query",
                "sql_error_count": state.sql_error_count + 1,
            }

        execute_query_tool = QuerySQLDatabaseTool(db=self.db)
        result = execute_query_tool.invoke(state.sql_query)

        if isinstance(result, str) and result.startswith("Error:"):
            return {
                "sql_result": "",
                "sql_query_execution_status": "failure",
                "sql_query_error": result,
                "sql_error_count": state.sql_error_count + 1,
            }
        else:
            return {
                "sql_result": result,
                "sql_query_execution_status": "success",
                "sql_query_error": "",
                "sql_error_count": 0,
            }

    def cannot_answer(self, state: State):
        return {
            "sql_error_count": 0,
            # "agent_answer": "I'm sorry, but I cannot find the information you're looking for.", # fastapi approach
            "messages": [
                AIMessage(
                    content="I'm sorry, but I cannot find the information you're looking for."
                )
            ],
        }

    def generate_answer(self, state: State):
        user_message = state.messages[-1].content  # langgraph approach
        system_prompt = (
            "/no_think\n"
            "You are a business assistant responding to a manager's queriesthe Question. in short sentence\n"
            "Given the manager's question and the result of the internal SQL query used to retrieve the relevant data, answer the question clearly and professionally.\n"
            "Use a well-formatted table with clear headers **only if** the question requires structured data, such as a list of transactions, balances over time, or multiple entries.\n"
            "Otherwise, respond in plain text that reads naturally.\n"
            "Do not mention SQL queries, databases, or how the data was retrieved.\n"
            "Avoid phrases like 'Hello there!', 'I'm happy to help...', or anything overly formal or robotic.\n"
            "Give a direct, informative, human-like answer as if responding to a manager's internal query.\n"
        )
        user_prompt = "Manager's Question: {user_message}\nResult: {sql_result}"
        prompt_template = ChatPromptTemplate(
            [("system", system_prompt), ("user", user_prompt)]
        )
        formatted_prompt = prompt_template.invoke(
            {
                "user_message": user_message,
                "sql_result": state.sql_result,
            }
        )
        # Prepend history to the formatted messages
        messages = (
            list(state.messages) + formatted_prompt.messages
        )  # langgraph approach
        # messages = state.history + formatted_prompt.messages # fastapi approach

        llm = ChatGroq(model=GROQ_MODEL, groq_api_key=Config.groq_api_key)
        response = llm.invoke(messages)

        return {
            # "agent_answer": response.content, # fastapi approach
            "messages": [AIMessage(content=response.content)],
        }

    def plot_agent(self, state: State):
        user_message = state.messages[-1].content  # langgraph approach
        system_message = """
        /no_think
        You are a data visualization expert and use your favourite graphing library Plotly only. Suppose, that
        the data is provided as {sql_result}. Follow the user's indications when creating the graph.

        IMPORTANT: When creating Plotly figures, ensure you do NOT repeat any keyword arguments. 
        Each parameter (like xaxis, yaxis, title, etc.) should only appear once in any function call.
        Generate clean, syntactically correct Python code without duplicate arguments.
        """
        user_prompt = """
            User message: {user_message}
        """
        plot_agent_prompt_template = ChatPromptTemplate(
            [("system", system_message), ("user", user_prompt)]
        )

        formatted_prompt = plot_agent_prompt_template.invoke(
            {
                "sql_result": state.sql_result,
                "user_message": user_message,
            }
        )

        prompt = list(state.messages) + formatted_prompt.messages  # langgraph approach
        # prompt = state.history + formatted_prompt.messages # fastapi approach

        llm = ChatGroq(model=GROQ_MODEL, groq_api_key=Config.groq_api_key)
        response = llm.invoke(prompt)
        result_output = response.content

        return {
            # "agent_answer": result_output, # fastapi approach
            "messages": [AIMessage(content=result_output)],
        }
