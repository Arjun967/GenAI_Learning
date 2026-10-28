# Product Description Analyzer backend

FastAPI service that analyzes product copy with the OpenAI Chat Completions API.

## Setup

From this directory in PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `OPENAI_API_KEY` in `.env`. `OPENAI_MODEL` is optional and defaults to
`gpt-4.1-mini`. Keep `.env` private; credentials are read from the environment
and are never included in source code.

## Run

```powershell
.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The health endpoint is `GET /health`. The analyzer endpoint is `POST /api/analyze`.
Interactive API documentation is available at `http://127.0.0.1:8000/docs`.
The Angular frontend's dev server proxies its `/api` requests to this service.

## OpenAI tool

The analyzer requests one clearly named function tool,
`return_product_description_analysis`. Its description and parameter schema tell
the model to return the score, summary, strengths, improvements, and rewritten
description in a validated structure. Tool choice is required, so the endpoint
doesn't depend on parsing free-form assistant text.

## Analyze request

```json
{
  "product_name": "Everyday Carry Tote",
  "category": "Accessories",
  "target_audience": "Daily commuters",
  "description": "A durable tote with room for your daily essentials.",
  "tone": "Persuasive"
}
```

`category` and `target_audience` may be empty. Supported tones are `Persuasive`,
`Friendly`, `Professional`, `Minimal`, and `Playful`. Product name and description
are required. The endpoint returns a score, summary, strengths, improvements, and
a rewritten description. Requests that omit `OPENAI_API_KEY` return HTTP 503;
upstream AI failures or invalid model output return HTTP 502.
