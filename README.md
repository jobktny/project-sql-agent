This project is to demonstrate application of agentic chatbot utilising LangGraph for agent orchestrate. This chatbot allow users to query and visualise plots about their business data.

## Project structure
This repository contains 3 main services which are database, backend and frontend, each service need its own environment and config.
```
.
└── project-sql-agent/
    ├── serivces/
    │   ├── backend_api/
    │   │   └── ...
    │   ├── database/
    │   │   └── ...
    │   └── frontend/
    │       └── ...
    ├── langgraph.json
    ├── pyproject.toml
    └── README.md
```

## Prerequisite
1. Download `conda` to manage environment and create a project environt use command `conda create -n chatbot_env python=3.13`
2. Activate envrionment `conda activate chatbot_env`
3. Install `pdm` (python dependency manager) to manage dependency, use `pip install pdm`
4. Install dependencies for the project `pdm install`
5. Download `Docker Desktop`

## Database
1. Access database folder `cd ./services/database/` create `.env` file to store credential of the database
2. Initial docker use `docker-compoes up -d`
3. Go to `http://localhost:8080/` and put username, password as stated in .env file
4. Upload csv files to `./cleaned_resources/` folder
5. Run `python load_data_to_db.py` to upload data to database

## Backend
1. Access to backend_api folder from root `cd ./services/backend_api` create `.env` file to store credential for backend
2. Create api key for `GROQ_API_KEY=gsk_...` from https://console.groq.com/home 
3. Create api key for `LANGSMITH_API_KEY=lsv2_...` from https://www.langchain.com/langsmith/observability once it created it will generate project name which will be use for `LANGSMITH_PROJECT=...`
4. Run `langgraph dev` at root directory to run langgraph server
5. Server will be running at `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`

(Optional) backend service is also available for fastapi by checking the commented code in  `./app/chat_services/agents.py` and `./app/models/state.py`
- Run at root `fastapi dev services/backend_api/app/main.py` the server will running at `http://127.0.0.1:8000`

## Frontend
1. Accress to frontend server from root `cd ./services/frontend` create `.env` file to store credential for backend
2. Use the same `LANGSMITH_API_KEY=lsv2_...` as the backend
3. Install nodejs environment from https://nodejs.org/en
4. Install `pnpm` to manage node dependency run `npm install -g pnpm`
5. Install depencendy `pnpm install`
6. Run `pnpm dev` the server will be running at `http://localhost:3000`

## Workflow
<img width="1224" height="330" alt="image" src="https://github.com/user-attachments/assets/228131be-f8df-4e9b-ade2-71aa878723bc" />

## ChatUI example
<img width="1500" height="820" alt="image" src="https://github.com/user-attachments/assets/e447d582-ea12-4551-a211-726da660bd4a" />


## References
- Agent Chat UI repo: https://github.com/langchain-ai/agent-chat-ui
- Postgres database with docker: https://geshan.com.np/blog/2021/12/docker-postgres/#why-use-postgres-with-docker-for-local-development
- Fastapi and ChatUI: https://www.youtube.com/watch?v=B3PT5_ALg94&t=197s
- Plotly agent: https://www.youtube.com/watch?v=Phix-s5NPUA&t=2s
- SQL agent: https://levelup.gitconnected.com/how-to-build-an-llm-powered-sql-agent-using-langgraph-367b3edd350a
- Langgraph server: https://www.youtube.com/watch?v=SGt786ne_Mk&t=955s
