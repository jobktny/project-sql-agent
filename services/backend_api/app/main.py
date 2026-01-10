from contextlib import asynccontextmanager

from app.chat_services.chat import ChatService
from app.config import Config
from app.models.chat_models import ChatRequest, ChatResponse
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text

# database
config = Config()
db_uri = config.DATABASE_URI()
engine = create_engine(db_uri)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Database connection established")
    except Exception as e:
        print(f"Database connection failed: {e}")
        raise
    yield
    engine.dispose()
    print("Database connection closed")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/chat", response_model=ChatResponse)
async def agent_chat(
    request: ChatRequest, chat_service: ChatService = Depends(ChatService)
):
    result = chat_service.chat_flow(request.message)
    return ChatResponse(message=result["agent_answer"])


@app.get("/health")
def health_check():
    return {"message": "OK"}
