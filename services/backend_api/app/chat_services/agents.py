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
            You are a SQL router agent. You are given a user message and you will need to determine what is the most intention of the user.

            You will need to do the following tasks:
            1. You need to create a syntactically correct {dialect} query to run to help find the answer.
            2. You will need to determine if the user need to visualise the data or not (eg. vistualise..., show me the barchart... etc.) If so, you will need to set the need_visualise flag to True.
            3. Never query for all the columns from a specific table, only ask for a few relevant columns given the question.
            4. Pay attention to use only the column names that you can see in the schema description.
            5. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.

            Only use the following tables:
            {table_info}

            Out of policy handling:
            If the user's message is greeting, farewell, or anything that is not about the data in the database, or not sure about the intention of the user you should set the chit_chat flag to True.
            If the user's message is far from the data in the database, you should set the out_of_policy flag to True.
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
        system_prompt = """
            /no_think\n
            You are a business assistant. You are given a user message about business data and you need to answer the question.
            You will keep in mind to keep the professional tone and answer the question clearly and professionally. Analytically answer the question.

            You will need to do the following tasks:
            1. Use a well-formatted table with clear headers **only if** the question requires structured data, such as a list of transactions, balances over time, or multiple entries. Otherwise, respond in plain text that reads naturally.
            2. Do not mention SQL queries, databases, or how the data was retrieved.
            3. Avoid phrases like 'Hello there!', 'I'm happy to help...', or anything overly formal or robotic.
            4. Give a direct, informative, human-like answer as if responding to a manager's internal query.
        """
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
            You are a data visualization expert and use your favourite graphing library Plotly only.
            The full database schema is as follows: \n{table_info}\n
            The data to be visualised is provided as \n{sql_result}.\n

            You will need to do the following tasks:
            1. Follow the user's indications when creating the graph.
            2. Analytically answer the question. (eg. point out potential insights, trends, annomalies, etc.)
            3. Ensure you do NOT repeat any keyword arguments. 
            4. Each parameter (like xaxis, yaxis, title, etc.) should only appear once in any function call.
            5. Generate clean, syntactically correct Python code without duplicate arguments.
            6. IMPORTANT: Always include ALL necessary imports at the top of your code (e.g., `import datetime`, `from datetime import datetime`, `import pandas as pd`, etc.). Never assume any module is pre-imported.
            7. ONLY use table_info to see the columns and how data are related to each other. DONOT import database or use any other data source, use sql_resul as the source of data.
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
                "table_info": self.db.get_table_info(),
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
