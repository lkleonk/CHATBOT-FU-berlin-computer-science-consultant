from fastapi import APIRouter, File, HTTPException, Request, Response, UploadFile, status

from app.domain.program_rules import ProgramRulesCatalogue, get_program_rules
from app.models import (
    HealthResponse,
    MessageRequest,
    ModelReply,
    SessionResponse,
    TranscriptUploadResponse,
    UsageResponse,
)
from app.services.model_service import ModelService
from app.services.quota_service import daily_quota
from app.settings import settings


session_router = APIRouter(prefix="/api/sessions", tags=["Sessions"])
program_rules_router = APIRouter(prefix="/api/program-rules", tags=["Program rules"])
health_router = APIRouter(tags=["Health"])
usage_router = APIRouter(prefix="/api/usage", tags=["Usage"])

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


@session_router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str):
    get_session_service().delete_session(session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@session_router.post("/{session_id}/message", response_model=ModelReply)
async def send_message(
    session_id: str,
    message: MessageRequest,
    request: Request,
    response: Response,
):
    quota = daily_quota.consume_user_action(_client_id(request))
    _set_quota_headers(response, quota)
    return await get_session_service().process_message(session_id, message.content)


@session_router.post("/{session_id}/transcript", response_model=TranscriptUploadResponse)
async def upload_transcript(
    session_id: str,
    request: Request,
    response: Response,
    file: UploadFile = File(...),
):
    quota = daily_quota.consume_user_action(_client_id(request))
    _set_quota_headers(response, quota)
    return await get_session_service().process_transcript(session_id, file)


def _client_id(request: Request) -> str:
    return request.client.host if request.client else "unknown-client"


def _set_quota_headers(response: Response, quota: dict) -> None:
    response.headers["X-RateLimit-Limit"] = str(quota["limit"])
    response.headers["X-RateLimit-Remaining"] = str(quota["remaining"])
    response.headers["X-RateLimit-Reset"] = quota["reset_at"].isoformat()
    response.headers["X-RateLimit-Scope"] = "user_action"


@usage_router.get("", response_model=UsageResponse)
async def read_usage(request: Request):
    quota = daily_quota.user_action_status(_client_id(request))
    return {
        **quota,
        "session_inactivity_ttl_seconds": settings.SESSIONS.INACTIVITY_TTL_SECONDS,
        "diagnostic_tracing_enabled": settings.WIZARDFLOW.ENABLED,
        "quota_scope": "client_ip",
    }


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
