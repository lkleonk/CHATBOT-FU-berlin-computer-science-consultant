import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("LLM_PROVIDER", "local_ollama")

from app.domain.study_plan import PlannedModule, StudyPlan  # noqa: E402
from app.pdf.models import ExtractedDocument, ExtractedPage, PdfUnreadableError, ReadabilityResult  # noqa: E402
from app.routes import session_router  # noqa: E402


def _build_client() -> TestClient:
    # Build a minimal app from just the session router so the test runs without
    # the uvicorn/SSH dependencies pulled in by app.main.
    app = FastAPI()
    app.include_router(session_router)
    return TestClient(app)


def _create_session(client: TestClient) -> str:
    response = client.post("/api/sessions", json={})
    assert response.status_code == 200
    return response.json()["session_id"]


def test_transcript_rejects_non_pdf():
    with _build_client() as client:
        session_id = _create_session(client)
        response = client.post(
            f"/api/sessions/{session_id}/transcript",
            files={"file": ("notes.txt", b"hello", "text/plain")},
        )
    assert response.status_code == 415
    assert response.json()["detail"]["error_code"] == "unsupported_file_type"


def test_transcript_unreadable_returns_dialog_payload(monkeypatch):
    def fake_extract(data, filename, extractor=None):
        raise PdfUnreadableError(
            ReadabilityResult(
                is_readable=False,
                total_pages=2,
                readable_pages=0,
                total_text_length=12,
                reason="too little text",
            )
        )

    monkeypatch.setattr("app.services.session_service.extract_and_validate", fake_extract)

    with _build_client() as client:
        session_id = _create_session(client)
        response = client.post(
            f"/api/sessions/{session_id}/transcript",
            files={"file": ("scan.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["error_code"] == "pdf_unreadable"
    assert "unreadable" in detail["message"].lower()


def test_transcript_readable_returns_plan_and_rule_check(monkeypatch):
    def fake_extract(data, filename, extractor=None):
        return ExtractedDocument(
            filename=filename,
            pages=[ExtractedPage(page=1, text="Telematik 10 LP " + "x" * 300)],
        )

    async def fake_parse(text, wizardflow_message_id=None, degree=None):
        return StudyPlan(
            specialization_area="technical",
            modules=[PlannedModule(name="Telematik", lp=10, area="technical")],
        )

    monkeypatch.setattr("app.services.session_service.extract_and_validate", fake_extract)
    monkeypatch.setattr("app.services.session_service.parse_study_plan", fake_parse)

    with _build_client() as client:
        session_id = _create_session(client)
        response = client.post(
            f"/api/sessions/{session_id}/transcript",
            files={"file": ("transcript.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["filename"] == "transcript.pdf"
    assert payload["message_type"] == "plan_check"
    assert payload["parsed_study_plan"]["modules"][0]["name"] == "Telematik"
    assert payload["rule_check_result"] is not None
    assert "transcript.pdf" in payload["reply"]
    assert "10 LP" in payload["reply"]
