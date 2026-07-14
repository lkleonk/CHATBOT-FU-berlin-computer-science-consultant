import json
import logging

from app.services.agent_config import agent_flow_config
from app.services.model_service import ModelService
from app.services.quota_service import DailyQuotaExceeded
from app.services.nodes.utils import (
    ADVISORY_DISCLAIMER_DE,
    ADVISORY_DISCLAIMER_EN,
    degree_for,
    format_recent_messages,
    latest_user_message,
    looks_german,
    parse_json_content,
    recent_messages,
    sanitize_reply_links,
    strip_advisory_disclaimer,
)
from app.services.states.consultant_state import ConsultantState
from app.services.wizardflow_service import (
    log_llm_error,
    log_llm_input,
    log_llm_output,
    log_node_output,
)


logger = logging.getLogger(__name__)


class AnswerGenerationError(RuntimeError):
    """Raised when the answer composer cannot produce a real answer."""


ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "message": {"type": "string"},
    },
    "required": ["message"],
}


async def answer_composer_node(state: ConsultantState) -> ConsultantState:
    logger.info("Answer composer invoked")
    wizardflow_message_id = state.get("wizardflow_message_id")
    composer_prompt = degree_for(state).prompts.answer_composer_system_prompt
    user_message = latest_user_message(state)
    history = format_recent_messages(
        recent_messages(state, agent_flow_config.answer_composer.history_turns)
    )
    context = state.get("course_context") or "(no course-offering context)"
    rule_result = state.get("rule_check_result")
    parsed_plan = state.get("parsed_study_plan")

    message = f"""
User message:
{user_message}

Recent conversation:
{history}

Course-offering context:
{context}

Course lookup keys:
{json.dumps(state.get("course_lookup_keys") or [], ensure_ascii=False, indent=2)}

Parsed study plan (validated module list, e.g. from an uploaded transcript):
{json.dumps(parsed_plan, ensure_ascii=False, indent=2) if parsed_plan else "(no parsed study plan)"}

Deterministic rule-check result:
{json.dumps(rule_result, ensure_ascii=False, indent=2) if rule_result else "(not a plan check)"}
""".strip()

    log_llm_input(
        wizardflow_message_id,
        "answer_composer",
        composer_prompt,
        message,
    )
    try:
        response = await ModelService().invoke(
            prompt=composer_prompt,
            message=message,
            format=ANSWER_SCHEMA,
        )
        response_content = response.get("content", "")
        log_llm_output(wizardflow_message_id, "answer_composer", response_content)
        data = parse_json_content(response_content)
        reply = data.get("message") if isinstance(data, dict) else None
        if not isinstance(reply, str) or not reply.strip():
            raise AnswerGenerationError("The answer composer returned an empty response.")
    except DailyQuotaExceeded:
        raise
    except Exception as exc:
        log_llm_error(wizardflow_message_id, "answer_composer", exc)
        logger.exception("Answer composition failed.")
        if isinstance(exc, AnswerGenerationError):
            raise
        raise AnswerGenerationError("The answer composer failed to generate a response.") from exc

    reply = sanitize_reply_links(reply, f"{composer_prompt}\n{message}")
    reply, model_added_disclaimer = strip_advisory_disclaimer(reply)
    if model_added_disclaimer or state.get("message_type") == "plan_check":
        disclaimer = ADVISORY_DISCLAIMER_DE if looks_german(user_message) else ADVISORY_DISCLAIMER_EN
        reply = f"{reply}\n\n{disclaimer}"
    result: ConsultantState = {
        "reply": reply,
        "messages": [{"role": "assistant", "content": reply}],
    }
    log_node_output(wizardflow_message_id, "answer_composer", result)
    return result
