import logging
from typing import Any

import httpx
from fastapi import HTTPException


logger = logging.getLogger(__name__)


class OllamaService:
    """Client for a local or FU-hosted Ollama chat endpoint."""

    def __init__(self, config):
        self.config = config

    def _build_payload(
        self,
        messages: list[dict[str, str]],
        stream: bool = False,
        format: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.config.MODEL,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": self.config.TEMPERATURE,
                "num_predict": self.config.MAX_TOKENS,
            },
        }
        if format is not None:
            payload["format"] = format
        return payload

    async def chat(
        self,
        messages: list[dict[str, str]],
        stream: bool = False,
        format: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if stream:
            raise HTTPException(status_code=400, detail="Streaming is not implemented for this consultant API")

        try:
            async with httpx.AsyncClient(timeout=self.config.TIMEOUT) as client:
                response = await client.post(
                    f"{self.config.BASE_URL.rstrip('/')}/api/chat",
                    json=self._build_payload(messages, stream=False, format=format),
                )
            if response.status_code != 200:
                logger.error("Ollama error: %s", response.text)
                raise HTTPException(status_code=500, detail="Ollama API error")

            result = response.json()
            return {
                "content": (result.get("message") or {}).get("content", ""),
                "tokens": result.get("eval_count", 0),
                "raw": result,
            }
        except httpx.TimeoutException:
            logger.error("Ollama request timeout")
            raise HTTPException(status_code=504, detail="AI model timeout")
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Error calling Ollama")
            raise HTTPException(status_code=500, detail=f"Failed to get AI response: {exc}") from exc

    async def invoke(
        self,
        prompt: str,
        message: str,
        format: dict[str, Any] | None = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": message},
        ]
        return await self.chat(messages=messages, stream=stream, format=format)

    async def check_connection(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.config.BASE_URL.rstrip('/')}/api/tags")
            return response.status_code == 200
        except Exception as exc:
            logger.error("Ollama connection error: %s", exc)
            return False
