from fastapi import APIRouter, File, HTTPException, UploadFile

from app.domain.program_rules import ProgramRulesCatalogue, get_program_rules
from app.models import (
    HealthResponse,
    MessageRequest,
    ModelReply,
    SessionResponse,
    TranscriptUploadResponse,
)
from app.services.model_service import ModelService
from app.settings import settings


session_router = APIRouter(prefix="/api/sessions", tags=["Sessions"])
program_rules_router = APIRouter(prefix="/api/program-rules", tags=["Program rules"])
health_router = APIRouter(tags=["Health"])

model_service = ModelService()
_session_service = None


def get_session_service():
    global _session_service
    if _session_service is None:
        from app.services.session_service import SessionService

        _session_service = SessionService()
    return _session_service


@session_router.post("", response_model=SessionResponse)
async def create_session():
    return {"session_id": get_session_service().create_session()}


@session_router.post("/{session_id}/message", response_model=ModelReply)
async def send_message(session_id: str, message: MessageRequest):
    return await get_session_service().process_message(session_id, message.content)


@session_router.post("/{session_id}/transcript", response_model=TranscriptUploadResponse)
async def upload_transcript(session_id: str, file: UploadFile = File(...)):
    return await get_session_service().process_transcript(session_id, file)


@program_rules_router.get("", response_model=ProgramRulesCatalogue)
async def read_program_rules():
    return get_program_rules()


@health_router.get("/health", response_model=HealthResponse)
async def health_check():
    services: dict[str, str] = {
        "llm_provider": settings.LLM.PROVIDER,
        "qdrant": "disabled (legacy/manual RAG only)",
    }
    status = "healthy"

    if await model_service.check_connection():
        services["llm"] = "connected"
    else:
        services["llm"] = "error"
        status = "degraded"

    response = {"status": status, "services": services}
    if status != "healthy":
        raise HTTPException(status_code=503, detail=response)
    return response
