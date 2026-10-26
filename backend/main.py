import os
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from openai import AsyncOpenAI, OpenAIError
from pydantic import BaseModel, Field

load_dotenv()

app = FastAPI(title="GenAI Learning API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=20)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat")
async def chat(request: ChatRequest) -> dict[str, str]:
    api_key = ""
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Set OPENAI_API_KEY in backend/.env to enable chat.",
        )

    client = AsyncOpenAI(api_key=api_key)
    try:
        completion = await client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Keep answers clear and concise.",
                },
                *(message.model_dump() for message in request.messages),
            ],
            max_completion_tokens=500,
        )
    except OpenAIError as exc:
        raise HTTPException(
            status_code=502,
            detail="The OpenAI service could not complete this request.",
        ) from exc
    finally:
        await client.close()

    if not completion.choices or not completion.choices[0].message.content:
        raise HTTPException(status_code=502, detail="The OpenAI service returned an empty reply.")

    return {"reply": completion.choices[0].message.content}