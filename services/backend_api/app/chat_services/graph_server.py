import sys
from pathlib import Path

# Add the backend_api directory to Python path so 'app' can be found
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.chat_services.agents import Agent
from app.chat_services.graph import GraphBuilder

agent = Agent()
builder = GraphBuilder(agent=agent)
graph = builder.build_graph()
