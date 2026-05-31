import logging

from app.prompts import CLASSIFIER_SYSTEM_PROMPT
from app.services.model_service import ModelService
from app.services.nodes.utils import latest_user_message, parse_json_content
from app.services.states.consultant_state import ConsultantState


logger = logging.getLogger(__name__)


CLASSIFIER_SCHEMA = {
    "type": "object",
    "properties": {
        "message_type": {
            "type": "string",
            "enum": ["study_question", "plan_check", "off_topic"],
        }
    },
    "required": ["message_type"],
}


def heuristic_classify(message: str) -> str:
    lowered = message.lower()
    plan_intent_terms = [
        "prüf",
        "pruef",
        "check",
        "passt",
        "valid",
        "studienplan",
        "study plan",
        "module plan",
    ]
    study_terms = [
        "informatik",
        "master",
        "vertiefung",
        "wissenschaftliches arbeiten",
        "softwareprojekt",
        "anwendungsbereich",
        "nebenfach",
        "unbenotet",
        "bachelormodul",
        "fu berlin",
        "studienplan",
    ]
    has_concrete_lp_list = lowered.count(" lp") >= 3
    if (any(term in lowered for term in plan_intent_terms) or has_concrete_lp_list) and any(
        term in lowered for term in study_terms
    ):
        return "plan_check"
    if any(term in lowered for term in study_terms):
        return "study_question"
    return "off_topic"


async def scope_classifier_node(state: ConsultantState) -> ConsultantState:
    logger.info("Scope classifier invoked")
    message = latest_user_message(state)
    fallback = heuristic_classify(message)
    source = "heuristic"

    try:
        response = await ModelService().invoke(
            prompt=CLASSIFIER_SYSTEM_PROMPT,
            message=f"Latest user message:\n{message}",
            format=CLASSIFIER_SCHEMA,
        )
        data = parse_json_content(response.get("content", ""))
        message_type = data.get("message_type")
        if message_type not in {"study_question", "plan_check", "off_topic"}:
            message_type = fallback
            source = "heuristic_invalid_llm_output"
        else:
            source = "llm"
    except Exception:
        logger.exception("Classifier failed; using heuristic fallback.")
        message_type = fallback

    logger.info("Scope classifier chose message_type=%s source=%s", message_type, source)
    return {"message_type": message_type}
