import json
import logging
import os
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import (
    APIConnectionError,
    AsyncOpenAI,
    AuthenticationError,
    BadRequestError,
    OpenAIError,
    RateLimitError,
)
from pydantic import BaseModel, ConfigDict, Field, ValidationError

load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI(title="Product Description Analyzer API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_name: str = Field(min_length=1, max_length=120)
    category: str = Field(default="", max_length=80)
    target_audience: str = Field(default="", max_length=120)
    description: str = Field(min_length=1, max_length=4000)
    tone: Literal["Persuasive", "Friendly", "Professional", "Minimal", "Playful"] = (
        "Persuasive"
    )


class AnalysisResult(BaseModel):
    score: int = Field(ge=0, le=100)
    summary: str = Field(min_length=1, max_length=500)
    strengths: list[str] = Field(min_length=1, max_length=5)
    improvements: list[str] = Field(min_length=1, max_length=5)
    optimized_description: str = Field(min_length=1, max_length=4000)


ANALYSIS_TOOL_NAME = "return_product_description_analysis"
ANALYSIS_TOOL = {
    "type": "function",
    "function": {
        "name": ANALYSIS_TOOL_NAME,
        "description": (
            "Return a product description score, summary, strengths, "
            "improvements, and a truthful rewrite."
        ),
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "score": {
                    "type": "integer",
                    "description": "Overall description quality score from 0 to 100.",
                    "minimum": 0,
                    "maximum": 100,
                },
                "summary": {
                    "type": "string",
                    "description": "One concise sentence summarizing the description.",
                },
                "strengths": {
                    "type": "array",
                    "description": "One to five things the description does well.",
                    "items": {"type": "string"},
                },
                "improvements": {
                    "type": "array",
                    "description": "One to five actionable ways to improve the copy.",
                    "items": {"type": "string"},
                },
                "optimized_description": {
                    "type": "string",
                    "description": (
                        "A rewritten description in the requested tone using only "
                        "product facts provided by the user."
                    ),
                },
            },
            "required": [
                "score",
                "summary",
                "strengths",
                "improvements",
                "optimized_description",
            ],
            "additionalProperties": False,
        },
    },
}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyze", response_model=AnalysisResult)
async def analyze(request: AnalysisRequest) -> AnalysisResult:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Set OPENAI_API_KEY in backend/.env to enable product analysis.",
        )

    prompt = {
        "product_name": request.product_name,
        "category": request.category,
        "target_audience": request.target_audience,
        "description": request.description,
        "tone": request.tone,
    }

    try:
        async with AsyncOpenAI(api_key=api_key) as client:
            completion = await client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert ecommerce product-copy editor. Analyze "
                            "the supplied listing and call the analysis tool with a "
                            "score, concise summary, strengths, actionable improvements, "
                            "and a rewrite in the requested tone. Never invent product "
                            "facts or claim details absent from the source description."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(prompt, ensure_ascii=False),
                    },
                ],
                tools=[ANALYSIS_TOOL],
                tool_choice={
                    "type": "function",
                    "function": {"name": ANALYSIS_TOOL_NAME},
                },
                parallel_tool_calls=False,
                max_completion_tokens=1200,
            )
    except AuthenticationError as exc:
        logger.warning("OpenAI rejected the configured API key.")
        raise HTTPException(
            status_code=502,
            detail="OpenAI rejected OPENAI_API_KEY. Check that the key is valid and active.",
        ) from exc
    except RateLimitError as exc:
        logger.warning("OpenAI rate-limited the analysis request.")
        raise HTTPException(
            status_code=503,
            detail="OpenAI rate-limited this request or the account has insufficient quota. Try again or check the account's usage and billing.",
        ) from exc
    except BadRequestError as exc:
        logger.warning("OpenAI rejected the analysis request format.")
        raise HTTPException(
            status_code=502,
            detail="OpenAI rejected the request. Check that OPENAI_MODEL supports function tools and that the request is valid.",
        ) from exc
    except APIConnectionError as exc:
        logger.warning("Could not connect to OpenAI.")
        raise HTTPException(
            status_code=502,
            detail="Could not connect to OpenAI. Check network access and try again.",
        ) from exc
    except OpenAIError as exc:
        logger.warning("OpenAI analysis failed (%s).", type(exc).__name__)
        raise HTTPException(
            status_code=502,
            detail=f"OpenAI analysis failed ({type(exc).__name__}). Check the backend logs and OpenAI model configuration.",
        ) from exc

    if not completion.choices:
        raise HTTPException(status_code=502, detail="The AI service returned an empty analysis.")

    try:
        tool_calls = completion.choices[0].message.tool_calls
        analysis_call = next(
            (
                tool_call
                for tool_call in tool_calls or []
                if tool_call.function.name == ANALYSIS_TOOL_NAME
            ),
            None,
        )
        if analysis_call is None:
            raise HTTPException(
                status_code=502,
                detail="The AI service did not return the product analysis tool result.",
            )
        analysis = json.loads(analysis_call.function.arguments)
        return AnalysisResult.model_validate(analysis)
    except (ValidationError, json.JSONDecodeError, TypeError) as exc:
        raise HTTPException(
            status_code=502,
            detail="The AI service returned an invalid tool result.",
        ) from exc
