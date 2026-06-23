import json
import logging

from app.prompts import ANSWER_COMPOSER_SYSTEM_PROMPT
from app.services.agent_config import agent_flow_config
from app.services.model_service import ModelService
from app.services.quota_service import DailyQuotaExceeded
from app.services.nodes.utils import (
    format_recent_messages,
    latest_user_message,
    parse_json_content,
    recent_messages,
)
from app.services.states.consultant_state import ConsultantState
from app.services.wizardflow_service import (
    log_llm_error,
    log_llm_input,
    log_llm_output,
    log_node_output,
)


logger = logging.getLogger(__name__)


ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "message": {"type": "string"},
    },
    "required": ["message"],
}


def fallback_answer(state: ConsultantState) -> str:
    if state.get("course_lookup_needs_clarification"):
        return state.get("course_lookup_clarification_question") or (
            "Which semester should I use for the course offering lookup?"
        )

    rule_result = state.get("rule_check_result")
    if rule_result:
        issues = rule_result.get("issues") or []
        if not issues:
            return rule_result.get("summary") or "The supplied study plan satisfies the implemented checks."
        first = issues[0]
        return f"{rule_result.get('summary')} First issue: {first.get('message')}"

    if state.get("retrieved_context"):
        if state.get("course_lookup_message"):
            return state["course_lookup_message"]
        return "I found relevant local context, but the LLM response could not be generated. Please retry."
    return "The local resources do not contain enough information to answer that."


async def answer_composer_node(state: ConsultantState) -> ConsultantState:
    logger.info("Answer composer invoked")
    wizardflow_message_id = state.get("wizardflow_message_id")
    user_message = latest_user_message(state)
    history = format_recent_messages(
        recent_messages(state, agent_flow_config.answer_composer.history_turns)
    )
    context = state.get("retrieved_context") or "(no retrieved context)"
    rule_result = state.get("rule_check_result")
    parsed_plan = state.get("parsed_study_plan")

    message = f"""
User message:
{user_message}

Recent conversation:
{history}

Retrieved consultant context:
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
        ANSWER_COMPOSER_SYSTEM_PROMPT,
        message,
    )
    try:
        response = await ModelService().invoke(
            prompt=ANSWER_COMPOSER_SYSTEM_PROMPT,
            message=message,
            format=ANSWER_SCHEMA,
        )
        response_content = response.get("content", "")
        log_llm_output(wizardflow_message_id, "answer_composer", response_content)
        data = parse_json_content(response_content)
        reply = data.get("message") or fallback_answer(state)
    except DailyQuotaExceeded:
        raise
    except Exception as exc:
        log_llm_error(wizardflow_message_id, "answer_composer", exc)
        logger.exception("Answer composition failed; using fallback.")
        reply = fallback_answer(state)

    result: ConsultantState = {
        "reply": reply,
        "messages": [{"role": "assistant", "content": reply}],
    }
    log_node_output(wizardflow_message_id, "answer_composer", result)
    return result
