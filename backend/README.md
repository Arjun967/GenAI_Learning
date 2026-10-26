# GenAI Learning API

FastAPI service for the Angular chat client. It exposes a health check and a chat endpoint backed by OpenAI Chat Completions.

## Setup

From the `backend` folder in PowerShell:

```powershell
py -3.14 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

`OPENAI_MODEL` is read from the environment and defaults to `gpt-4.1-mini`.

**Credential warning:** the current `main.py` has an API credential hard-coded in source. It does not read `OPENAI_API_KEY` from `.env`, despite the example variable. Do not commit or share the source with a live credential. Revoke and rotate it if it is real, then update the application to read the key from the environment before using the service.

## Run

```powershell
.venv\Scripts\uvicorn.exe main:app --reload --host 127.0.0.1 --port 8000
```

The health endpoint is `GET /health`, which returns `{"status":"ok"}`. The chat endpoint is `POST /api/chat` and accepts up to 20 messages, each with a `role` of `user` or `assistant` and `content` between 1 and 4,000 characters:

```json
{
	"messages": [
		{ "role": "user", "content": "Hello" }
	]
}
```

Successful requests return `{ "reply": "..." }`. Invalid request data returns 422; OpenAI request failures return 502. Interactive API docs are at `/docs`. Start the Angular client separately with `npm start` from the `client` folder.