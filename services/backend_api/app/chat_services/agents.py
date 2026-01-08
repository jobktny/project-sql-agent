from app.config import GROQ_MODEL, Config
from app.models.chat_models import QueryOutput
from app.models.state import State
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain_community.utilities.sql_database import SQLDatabase
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
        prompt = general_agent_prompt_template.invoke(
            {
                "user_message": state.user_message,
                "table_info": self.db.get_table_info(),
            }
        )
        llm = ChatGroq(model=GROQ_MODEL, groq_api_key=Config.groq_api_key)
        response = llm.invoke(prompt)
        state.agent_answer = response.content

        return state

    def write_query(self, state: State):
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
            prompt = query_prompt_template.invoke(
                {
                    "dialect": self.db.dialect,
                    "table_info": self.db.get_table_info(),
                    "input": state.user_message,
                    "query_error": state.sql_query_error,
                }
            )

            llm = ChatGroq(model=GROQ_MODEL, groq_api_key=Config.groq_api_key)
            structured_llm = llm.with_structured_output(QueryOutput)
            result = structured_llm.invoke(prompt)
            state.sql_query = result.generated_sql_query
            state.need_visualise = result.need_visualise
            state.out_of_policy = result.out_of_policy
            state.chit_chat = result.chit_chat

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

            state.sql_query = ""  # No query generated
            state.sql_query_execution_status = "failure"
            state.sql_query_error = f"Error generating query: {error_msg}"
            state.sql_error_count = state.sql_error_count + 1

        return state

    def execute_query(self, state: State):
        """Execute SQL query and set query_execution_status."""
        execute_query_tool = QuerySQLDatabaseTool(db=self.db)
        result = execute_query_tool.invoke(state.sql_query)

        if isinstance(result, str) and result.startswith("Error:"):
            state.sql_query_execution_status = "failure"
            state.sql_query_error = result
            state.sql_error_count = state.sql_error_count + 1

        else:
            state.sql_result = result
            state.sql_query_execution_status = "success"
            state.sql_query_error = ""
            state.sql_error_count = 0

        return state

    def cannot_answer(self, state: State):
        state.sql_error_count = 0
        state.agent_answer = (
            "I'm sorry, but I cannot find the information you're looking for."
        )

        return state

    def generate_answer(self, state: State):
        prompt = (
            "/no_think\n"
            "You are a business assistant responding to a manager's queriesthe Question. in short sentence\n"
            "Given the manager's question and the result of the internal SQL query used to retrieve the relevant data, answer the question clearly and professionally.\n"
            "Use a well-formatted table with clear headers **only if** the question requires structured data, such as a list of transactions, balances over time, or multiple entries.\n"
            "Otherwise, respond in plain text that reads naturally.\n"
            "Do not mention SQL queries, databases, or how the data was retrieved.\n"
            "Avoid phrases like 'Hello there!', 'I'm happy to help...', or anything overly formal or robotic.\n"
            "Give a direct, informative, human-like answer as if responding to a manager's internal query.\n\n"
            f"Manager's Question: {state.user_message}\n"
            f"Result: {state.sql_result}"
        )
        llm = ChatGroq(model=GROQ_MODEL, groq_api_key=Config.groq_api_key)
        response = llm.invoke(prompt)
        state.agent_answer = response.content

        return state

    def plot_agent(self, state: State):
        system_message = """
            You are a data visualization expert and use your favourite graphing library Plotly only. Suppose, that
            the data is provided as {sql_result}. Follow the user's indications when creating the graph.
        """
        user_prompt = """
            User message: {user_message}
        """
        plot_agent_prompt_template = ChatPromptTemplate(
            [("system", system_message), ("user", user_prompt)]
        )

        prompt = plot_agent_prompt_template.invoke(
            {
                "sql_result": state.sql_result,
                "user_message": state.user_message,
            }
        )

        llm = ChatGroq(model=GROQ_MODEL, groq_api_key=Config.groq_api_key)
        response = llm.invoke(prompt)
        state.agent_answer = response.content

        return state

    def get_fig_from_code(code):
        local_variables = {}
        exec(code, {}, local_variables)
        return local_variables.get("fig")
