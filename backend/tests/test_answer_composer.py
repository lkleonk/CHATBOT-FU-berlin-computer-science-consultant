import asyncio

import pytest

from app.services.nodes import answer_composer
from app.services.nodes.answer_composer import AnswerGenerationError


def test_answer_composer_does_not_return_fallback_when_model_fails(monkeypatch):
    class FailingModelService:
        async def invoke(self, **kwargs):
            raise RuntimeError("provider unavailable")

    monkeypatch.setattr(answer_composer, "ModelService", FailingModelService)

    state = {
        "degree_id": "msc_informatik",
        "messages": [{"role": "user", "content": "How many LP are required?"}],
        "wizardflow_message_id": "test-message",
    }

    with pytest.raises(AnswerGenerationError):
        asyncio.run(answer_composer.answer_composer_node(state))
