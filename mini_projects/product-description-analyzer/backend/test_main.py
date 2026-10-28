import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
from openai import AuthenticationError
from fastapi.testclient import TestClient

from main import ANALYSIS_TOOL_NAME, app


class FakeOpenAIClient:
    def __init__(self, completion: object) -> None:
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=AsyncMock(return_value=completion))
        )

    async def __aenter__(self) -> "FakeOpenAIClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


class AnalyzerApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health_returns_ok(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_analyze_requires_api_key(self) -> None:
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            response = self.client.post(
                "/api/analyze",
                json={
                    "product_name": "Everyday Carry Tote",
                    "description": "A durable tote for everyday essentials.",
                },
            )

        self.assertEqual(response.status_code, 503)
        self.assertIn("OPENAI_API_KEY", response.json()["detail"])

    def test_analyze_rejects_missing_required_fields(self) -> None:
        response = self.client.post("/api/analyze", json={"category": "Accessories"})

        self.assertEqual(response.status_code, 422)

    def test_analyze_uses_tool_and_returns_tool_result(self) -> None:
        analysis = {
            "score": 82,
            "summary": "A clear description with room for more detail.",
            "strengths": ["Names the product clearly"],
            "improvements": ["Add material details"],
            "optimized_description": "A tote for everyday essentials.",
        }
        tool_call = SimpleNamespace(
            function=SimpleNamespace(
                name=ANALYSIS_TOOL_NAME,
                arguments=json.dumps(analysis),
            )
        )
        completion = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(tool_calls=[tool_call]),
                )
            ]
        )
        openai_client = FakeOpenAIClient(completion)

        with (
            patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}),
            patch("main.AsyncOpenAI", return_value=openai_client) as openai_constructor,
        ):
            response = self.client.post(
                "/api/analyze",
                json={
                    "product_name": "Everyday Carry Tote",
                    "description": "A durable tote for everyday essentials.",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), analysis)
        openai_constructor.assert_called_once_with(api_key="test-key")
        create_call = openai_client.chat.completions.create
        self.assertEqual(
            create_call.await_args.kwargs["tool_choice"]["function"]["name"],
            ANALYSIS_TOOL_NAME,
        )
        self.assertEqual(len(create_call.await_args.kwargs["tools"]), 1)

    def test_analyze_returns_gateway_error_when_tool_result_is_missing(self) -> None:
        completion = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(tool_calls=None))]
        )
        openai_client = FakeOpenAIClient(completion)

        with (
            patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}),
            patch("main.AsyncOpenAI", return_value=openai_client),
        ):
            response = self.client.post(
                "/api/analyze",
                json={
                    "product_name": "Everyday Carry Tote",
                    "description": "A durable tote for everyday essentials.",
                },
            )

        self.assertEqual(response.status_code, 502)
        self.assertIn("tool result", response.json()["detail"])

    def test_analyze_explains_invalid_api_key(self) -> None:
        response_from_openai = httpx.Response(
            401,
            request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"),
        )
        authentication_error = AuthenticationError(
            "Invalid API key",
            response=response_from_openai,
            body=None,
        )
        openai_client = FakeOpenAIClient(completion=None)
        openai_client.chat.completions.create.side_effect = authentication_error

        with (
            patch.dict(os.environ, {"OPENAI_API_KEY": "invalid-test-key"}),
            patch("main.AsyncOpenAI", return_value=openai_client),
        ):
            response = self.client.post(
                "/api/analyze",
                json={
                    "product_name": "Everyday Carry Tote",
                    "description": "A durable tote for everyday essentials.",
                },
            )

        self.assertEqual(response.status_code, 502)
        self.assertIn("OPENAI_API_KEY", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
