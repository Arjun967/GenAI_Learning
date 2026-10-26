# GenAI Learning

An Angular chat client backed by a FastAPI service that calls OpenAI's Chat Completions API.

## Features

- Suggested prompts, a conversation view, and a message composer. Enter sends; Shift+Enter adds a newline.
- The client sends the latest 20 conversation messages to the API and displays assistant replies or service errors.
- `GET /health` checks the API; `POST /api/chat` accepts `{ "messages": [{ "role": "user", "content": "..." }] }` and returns `{ "reply": "..." }`.
- The API accepts up to 20 messages, with each message limited to 4,000 characters. Conversations are kept in client memory and are not persisted.

## Prerequisites

- Python 3.14 and Node.js/npm
- An OpenAI API credential for live chat requests

## Start the backend

In PowerShell from the repository root:

```powershell
cd backend
py -3.14 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\uvicorn.exe main:app --reload --host 127.0.0.1 --port 8000
```

The API listens on `http://127.0.0.1:8000`; interactive docs are at `http://127.0.0.1:8000/docs`.

## Start the client

In a second terminal from the repository root:

```powershell
cd client
npm install
npm start
```

Open `http://localhost:4200`. The API allows requests from `localhost:4200` and `127.0.0.1:4200`.

## Credential warning

The current `backend/main.py` contains an API credential directly in source. The endpoint does not currently read `OPENAI_API_KEY` from `.env`, so the `.env.example` key setting will not override it. Do not commit or share the source with a live credential; revoke and rotate it if it is real, then move credential loading to the environment before using this project.