import os

from dotenv import load_dotenv

load_dotenv()

# GROQ_MODEL = "openai/gpt-oss-120b"  # 200k tokens per day
GROQ_MODEL = "qwen/qwen3-32b"  # 500k tokens per day
# GROQ_MODEL = "llama-3.3-70b-versatile"  # 100k tokens per day
# GROQ_MODEL = "moonshotai/kimi-k2-instruct"  # 300k tokens per day


class Config:
    # agent
    groq_api_key = os.getenv("GROQ_API_KEY")
    langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
    langsmith_project = os.getenv("LANGSMITH_PROJECT")
    langsmith_endpoint = os.getenv("LANGSMITH_ENDPOINT")

    # database
    DB_TYPE = os.getenv("DB_TYPE", "postgresql")
    DB_DRIVER = os.getenv("DB_DRIVER", "psycopg2")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "postgres")

    def DATABASE_URI(self):
        return f"{self.DB_TYPE}+{self.DB_DRIVER}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
