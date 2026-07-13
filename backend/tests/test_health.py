import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("LLM_PROVIDER", "local_ollama")

from app.routes import health_router  # noqa: E402


def test_health_reports_the_active_llm_provider(monkeypatch):
    async def fake_check_connection():
        return True

    monkeypatch.setattr("app.routes.model_service.check_connection", fake_check_connection)
    app = FastAPI()
    app.include_router(health_router)

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["services"]["llm"] == "connected"
