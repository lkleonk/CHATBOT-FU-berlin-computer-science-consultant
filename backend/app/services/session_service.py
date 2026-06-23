import logging
import uuid

from fastapi import HTTPException, UploadFile

from app.domain.study_plan import StudyPlan
from app.models import ModelReply, TranscriptUploadResponse
from app.pdf.extract import PdfExtractionError
from app.pdf.models import PdfUnreadableError
from app.pdf.service import extract_and_validate
from app.services import wizardflow_service
from app.services.nodes.rule_checker import check_study_plan
from app.services.nodes.study_plan_parser import parse_study_plan
from app.services.session_lifecycle_service import SessionLifecycleService, session_lifecycle


logger = logging.getLogger(__name__)


def _get_agent_app():
    """Import the compiled LangGraph app lazily.

    Keeps ``session_service`` importable (and unit-testable) without pulling in
    the vector/embedding stack that the agent graph depends on.
    """
    from app.services.agent_graph_service import app as agent_app

    return agent_app


# Reject obviously oversized uploads before reading them into memory.
MAX_PDF_BYTES = 15 * 1024 * 1024

UNREADABLE_MESSAGE = "This PDF appears to be unreadable. Please upload a text-based PDF."


class SessionService:
    """DB-free session service using LangGraph memory keyed by session ID."""

    def __init__(self, lifecycle: SessionLifecycleService | None = None) -> None:
        self._lifecycle = lifecycle or session_lifecycle

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        logger.info("Created consultant session: %s", session_id)
        return session_id

    async def process_message(self, session_id: str, message_content: str) -> ModelReply:
        with self._lifecycle.activity(session_id):
            return await self._process_message(session_id, message_content)

    async def _process_message(self, session_id: str, message_content: str) -> ModelReply:
        wizardflow_message_id = str(uuid.uuid4())
        title = _message_title(message_content)
        try:
            agent_app = _get_agent_app()
            wizardflow_service.start_message(wizardflow_message_id, "chat")
            config = {"configurable": {"thread_id": session_id}}
            state = {
                "messages": [{"role": "user", "content": message_content}],
                "wizardflow_message_id": wizardflow_message_id,
            }
            result = await agent_app.ainvoke(state, config=config)
            return ModelReply(
                reply=result.get("reply") or "The consultant could not generate a reply.",
                message_type=result.get("message_type") or "off_topic",
                citations=result.get("citations") or [],
                rule_check_result=result.get("rule_check_result"),
                parsed_study_plan=result.get("parsed_study_plan"),
            )
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Error processing consultant message")
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        finally:
            wizardflow_service.end_message(wizardflow_message_id, title=title)

    async def process_transcript(
        self, session_id: str, file: UploadFile
    ) -> TranscriptUploadResponse:
        with self._lifecycle.activity(session_id):
            return await self._process_transcript(session_id, file)

    async def _process_transcript(
        self, session_id: str, file: UploadFile
    ) -> TranscriptUploadResponse:
        filename = file.filename or "transcript.pdf"
        content_type = (file.content_type or "").lower()
        if not filename.lower().endswith(".pdf") and content_type != "application/pdf":
            raise HTTPException(
                status_code=415,
                detail={
                    "error_code": "unsupported_file_type",
                    "message": "Only PDF files are supported.",
                },
            )

        data = await file.read()
        if not data:
            raise HTTPException(
                status_code=400,
                detail={"error_code": "empty_file", "message": "The uploaded file is empty."},
            )
        if len(data) > MAX_PDF_BYTES:
            raise HTTPException(
                status_code=413,
                detail={
                    "error_code": "file_too_large",
                    "message": "The PDF is too large. Please upload a file under 15 MB.",
                },
            )

        try:
            document = extract_and_validate(data, filename)
        except PdfUnreadableError as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "pdf_unreadable",
                    "message": UNREADABLE_MESSAGE,
                    "readability": exc.readability.model_dump(),
                },
            ) from exc
        except PdfExtractionError as exc:
            raise HTTPException(
                status_code=422,
                detail={"error_code": "pdf_unreadable", "message": UNREADABLE_MESSAGE},
            ) from exc

        wizardflow_message_id = str(uuid.uuid4())
        try:
            _get_agent_app()
            wizardflow_service.start_message(wizardflow_message_id, "transcript")
            plan = await parse_study_plan(document.full_text, wizardflow_message_id)
            rule_result = check_study_plan(plan, wizardflow_message_id)
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Failed to parse/validate uploaded transcript")
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        finally:
            wizardflow_service.end_message(
                wizardflow_message_id,
                title=f"Transcript: {document.filename}",
            )

        # Persist only the validated plan into LangGraph state so chat follow-ups
        # can reference it. Extracted text remains only in the local WizardFlow
        # trace because transcript llm_input payloads are intentionally unredacted.
        self._persist_plan(session_id, plan, rule_result, wizardflow_message_id)

        reply = self._summarize_transcript(document.filename, plan, rule_result)
        return TranscriptUploadResponse(
            filename=document.filename,
            reply=reply,
            parsed_study_plan=plan,
            rule_check_result=rule_result.model_dump(),
        )

    def delete_session(self, session_id: str) -> None:
        self._lifecycle.delete_session(session_id)

    def _persist_plan(
        self,
        session_id: str,
        plan: StudyPlan,
        rule_result,
        wizardflow_message_id: str,
    ) -> None:
        config = {"configurable": {"thread_id": session_id}}
        try:
            _get_agent_app().update_state(
                config,
                {
                    "wizardflow_message_id": wizardflow_message_id,
                    "parsed_study_plan": plan.model_dump(),
                    "rule_check_result": rule_result.model_dump(),
                    "message_type": "plan_check",
                },
            )
        except Exception:
            logger.exception("Failed to persist transcript plan to session %s", session_id)

    def _summarize_transcript(self, filename: str, plan: StudyPlan, rule_result) -> str:
        module_count = len(plan.modules)
        total_lp = sum(module.lp for module in plan.modules)
        return (
            f"Processed {filename}: extracted {module_count} module(s) totalling "
            f"{total_lp} LP. {rule_result.summary}"
        )


def _message_title(message: str, max_length: int = 100) -> str:
    compact = " ".join(message.split())
    return compact[:max_length] or "Consultant message"
