import os

from dotenv import load_dotenv

load_dotenv()

# GROQ_MODEL = "openai/gpt-oss-120b"  # 200k tokens per day
GROQ_MODEL = "qwen/qwen3-32b"  # 500k tokens per day


class Config:
    groq_api_key = os.getenv("GROQ_API_KEY")
    langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
    langsmith_project = os.getenv("LANGSMITH_PROJECT")
    langsmith_endpoint = os.getenv("LANGSMITH_ENDPOINT")
