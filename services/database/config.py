import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    # database config allow user to change the database type and driver also need change in docker-compose.yml
    DB_TYPE = os.getenv("DB_TYPE", "postgresql")
    DB_DRIVER = os.getenv("DB_DRIVER", "psycopg2")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "postgres")

    def DATABASE_URI(self):
        return f"{self.DB_TYPE}+{self.DB_DRIVER}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


db_config = Config()
