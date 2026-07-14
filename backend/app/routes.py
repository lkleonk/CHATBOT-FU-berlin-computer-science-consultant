from fastapi import APIRouter, File, HTTPException, Request, Response, UploadFile, status

from app.domain.course_offerings import (
    area_label,
    course_type_label,
    normalize_course_url,
    project_offerings,
    semester_label,
)
from app.domain.degrees import DEFAULT_DEGREE_ID, get_degree, is_valid_degree, list_degrees
from app.domain.program_rules import ProgramRulesCatalogue
from app.models import (
    CourseOfferingsCatalogue,
    DegreeInfo,
    HealthResponse,
    MessageRequest,
    ModelReply,
    SessionCreateRequest,
    SessionResponse,
    TracingReinitResponse,
    TranscriptUploadResponse,
    UsageResponse,
)
from app.services import wizardflow_service
from app.services.model_service import ModelService
from app.services.quota_service import daily_quota
from app.settings import settings


session_router = APIRouter(prefix="/api/sessions", tags=["Sessions"])
program_rules_router = APIRouter(prefix="/api/program-rules", tags=["Program rules"])
course_offerings_router = APIRouter(prefix="/api/course-offerings", tags=["Course offerings"])
degrees_router = APIRouter(prefix="/api/degrees", tags=["Degrees"])
health_router = APIRouter(tags=["Health"])
usage_router = APIRouter(prefix="/api/usage", tags=["Usage"])
tracing_router = APIRouter(prefix="/api/tracing", tags=["Tracing"])

model_service = ModelService()
_session_service = None


def get_session_service():
    global _session_service
    if _session_service is None:
        from app.services.session_service import SessionService

        _session_service = SessionService()
    return _session_service


@session_router.post("", response_model=SessionResponse)
async def create_session(payload: SessionCreateRequest | None = None):
    degree_id = (payload or SessionCreateRequest()).degree
    _ensure_known_degree(degree_id)
    return {
        "session_id": get_session_service().create_session(degree_id),
        "degree": degree_id,
    }


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


@tracing_router.post("/reinit", response_model=TracingReinitResponse)
async def reinit_trace_file():
    if wizardflow_service.tracer is None and settings.WIZARDFLOW.ENABLED:
        # The tracer is created when the agent graph module first loads
        # (normally on first session use); mirror that lazy import so the
        # button also works on a fresh backend.
        import app.services.agent_graph_service  # noqa: F401

    trace_path = wizardflow_service.reinit_tracing()
    if trace_path is None:
        raise HTTPException(
            status_code=409,
            detail={
                "error_code": "tracing_disabled",
                "message": "WizardFlow tracing is not enabled on this backend.",
            },
        )
    return {"trace_path": trace_path}


@degrees_router.get("", response_model=list[DegreeInfo])
async def read_degrees():
    return [
        DegreeInfo(id=degree.id, display_name=degree.display_name, regulation=degree.regulation)
        for degree in list_degrees()
    ]


@program_rules_router.get("", response_model=ProgramRulesCatalogue)
async def read_program_rules(degree: str = DEFAULT_DEGREE_ID):
    _ensure_known_degree(degree)
    return get_degree(degree).get_program_rules()


@course_offerings_router.get("", response_model=CourseOfferingsCatalogue)
async def read_course_offerings(degree: str = DEFAULT_DEGREE_ID):
    _ensure_known_degree(degree)
    degree_definition = get_degree(degree)
    semesters = []
    for semester_id, areas in project_offerings(degree).items():
        rendered_areas = []
        for area_id, course_types in areas.items():
            rendered_types = []
            for course_type_id, courses in course_types.items():
                rendered_types.append(
                    {
                        "id": course_type_id,
                        "label": course_type_label(course_type_id),
                        "courses": [
                            {**course, "url": normalize_course_url(course.get("url"))}
                            for course in courses
                        ],
                    }
                )
            rendered_areas.append(
                {
                    "id": area_id,
                    "label": area_label(degree, area_id),
                    "course_types": rendered_types,
                }
            )
        semesters.append(
            {
                "id": semester_id,
                "label": semester_label(semester_id),
                "areas": rendered_areas,
            }
        )

    return {
        "degree_program": degree_definition.display_name,
        "regulation": degree_definition.regulation,
        "source_note": (
            "Courses currently present in the local course catalogue and semester-offering data. "
            "Verify details in the official FU Berlin course catalogue."
        ),
        "semesters": semesters,
    }


def _ensure_known_degree(degree_id: str) -> None:
    if not is_valid_degree(degree_id):
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "unknown_degree",
                "message": f"Unknown degree id: {degree_id}",
                "known_degrees": [degree.id for degree in list_degrees()],
            },
        )


@health_router.get("/health", response_model=HealthResponse)
async def health_check():
    services: dict[str, str] = {"llm_provider": settings.LLM.PROVIDER}
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
