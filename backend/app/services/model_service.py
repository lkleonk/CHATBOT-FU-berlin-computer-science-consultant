from typing import Any

from app.services.academiccloud_service import AcademicCloudService
from app.services.ollama_service import OllamaService
from app.settings import settings


class ModelService:
    """Provider selector for the active LLM backend."""

    def __init__(self):
        if settings.is_academiccloud():
            self.provider = AcademicCloudService(settings.ACADEMICCLOUD)
        elif settings.is_fu_ollama():
            self.provider = OllamaService(settings.FU_OLLAMA)
        elif settings.is_local_ollama():
            self.provider = OllamaService(settings.LOCAL_OLLAMA)
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.LLM.PROVIDER}")

    async def chat(
        self,
        messages: list[dict[str, str]],
        stream: bool = False,
        format: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await self.provider.chat(messages=messages, stream=stream, format=format)

    async def invoke(
        self,
        prompt: str,
        message: str,
        format: dict[str, Any] | None = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        return await self.provider.invoke(prompt=prompt, message=message, format=format, stream=stream)

    async def check_connection(self) -> bool:
        return await self.provider.check_connection()
