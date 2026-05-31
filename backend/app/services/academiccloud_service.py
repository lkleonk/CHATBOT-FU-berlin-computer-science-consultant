import json
import logging
from typing import Any

import httpx
from fastapi import HTTPException

from app.settings import settings


logger = logging.getLogger(__name__)


class AcademicCloudService:
    """Client for AcademicCloud's OpenAI-compatible chat API."""

    def __init__(self, config=None):
        self.config = config or settings.ACADEMICCLOUD

    def _base_url(self) -> str:
        return self.config.BASE_URL.rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.config.API_KEY}",
            "Content-Type": "application/json",
        }

    def _require_api_key(self) -> None:
        if self.config.API_KEY:
            return
        logger.error("AcademicCloud API key is not configured.")
        raise HTTPException(status_code=500, detail="AcademicCloud API key is not configured")

    def _prepare_system_prompt(self, prompt: str | None) -> str | None:
        if not prompt:
            return prompt
        if "qwen3" in self.config.MODEL.lower() and "/no_think" not in prompt:
            return f"/no_think\n{prompt}"
        return prompt

    def _build_payload(
        self,
        messages: list[dict[str, str]],
        stream: bool = False,
        format: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.config.MODEL,
            "messages": messages,
            "temperature": self.config.TEMPERATURE,
            "max_tokens": self.config.MAX_TOKENS,
            "stream": stream,
        }
        if format is not None:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "structured_output",
                    "schema": format,
                    "strict": True,
                },
            }
        return payload

    async def chat(
        self,
        messages: list[dict[str, str]],
        stream: bool = False,
        format: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if stream:
            raise HTTPException(status_code=400, detail="Streaming is not implemented for this consultant API")

        self._require_api_key()
        try:
            async with httpx.AsyncClient(timeout=self.config.TIMEOUT) as client:
                response = await client.post(
                    f"{self._base_url()}/chat/completions",
                    headers=self._headers(),
                    json=self._build_payload(messages, stream=False, format=format),
                )
            if response.status_code != 200:
                logger.error("AcademicCloud error: %s", response.text)
                raise HTTPException(status_code=500, detail="AcademicCloud API error")

            result = response.json()
            choice = (result.get("choices") or [{}])[0]
            message = choice.get("message") or {}
            return {
                "content": message.get("content", ""),
                "tokens": (result.get("usage") or {}).get("completion_tokens", 0),
                "raw": result,
            }
        except httpx.TimeoutException:
            logger.error("AcademicCloud request timeout")
            raise HTTPException(status_code=504, detail="AI model timeout")
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Error calling AcademicCloud")
            raise HTTPException(status_code=500, detail=f"Failed to get AI response: {exc}") from exc

    async def invoke(
        self,
        prompt: str,
        message: str,
        format: dict[str, Any] | None = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        prompt = self._prepare_system_prompt(prompt)
        messages = [
            {"role": "system", "content": prompt or ""},
            {"role": "user", "content": message},
        ]
        return await self.chat(messages=messages, stream=stream, format=format)

    async def check_connection(self) -> bool:
        if not self.config.API_KEY:
            logger.error("AcademicCloud API key is not configured.")
            return False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._base_url()}/models", headers=self._headers())
            return response.status_code == 200
        except Exception as exc:
            logger.error("AcademicCloud connection error: %s", exc)
            return False


def parse_json_content(content: str) -> dict[str, Any]:
    """Small helper for provider responses that may contain extra text."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start : end + 1])
        raise
