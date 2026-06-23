import logging
import re

from app.prompts import CLASSIFIER_SYSTEM_PROMPT
from app.services.model_service import ModelService
from app.services.quota_service import DailyQuotaExceeded
from app.services.nodes.utils import latest_user_message, parse_json_content
from app.services.states.consultant_state import ConsultantState
from app.services.wizardflow_service import (
    log_llm_error,
    log_llm_input,
    log_llm_output,
    log_node_output,
)


logger = logging.getLogger(__name__)


CLASSIFIER_SCHEMA = {
    "type": "object",
    "properties": {
        "message_type": {
            "type": "string",
            "enum": ["degree_question", "course_offering_question", "plan_check", "off_topic"],
        }
    },
    "required": ["message_type"],
}


def heuristic_classify(message: str) -> str:
    lowered = _normalize_text(message)
    plan_intent_terms = [
        "pruef",
        "check",
        "passt",
        "valid",
        "studienplan",
        "study plan",
        "module plan",
    ]
    domain_terms = [
        "informatik",
        "master",
        "computer science",
        "cs",
        "technical",
        "technisch",
        "practical",
        "praktisch",
        "theoretical",
        "theoretisch",
        "lp",
        "credit",
        "credits",
        "vertiefung",
        "wissenschaftliches arbeiten",
        "softwareprojekt",
        "software project",
        "anwendungsbereich",
        "nebenfach",
        "unbenotet",
        "bachelormodul",
        "fu berlin",
        "studienplan",
    ]
    has_domain_signal = any(term in lowered for term in domain_terms)
    has_concrete_lp_list = lowered.count(" lp") >= 3

    if (any(term in lowered for term in plan_intent_terms) or has_concrete_lp_list) and has_domain_signal:
        return "plan_check"
    if _looks_like_degree_rule_question(lowered) and has_domain_signal:
        return "degree_question"
    if _looks_like_course_offering_question(lowered):
        return "course_offering_question"
    if has_domain_signal:
        return "degree_question"
    return "off_topic"


def _looks_like_degree_rule_question(text: str) -> bool:
    patterns = [
        r"\bhow many\b.*\b(can|may|allowed|take|count|counts|required|need|needed)\b",
        r"\bhow much\b.*\b(lp|credit|credits)\b",
        r"\bwie viele\b.*\b(darf|kann|zaehlen|belegen|machen|brauche|benoetige)\b",
        r"\bwie viel\b.*\b(lp|leistungspunkt|leistungspunkte|credits?)\b",
        r"\b(at most|at least|maximum|minimum)\b",
        r"\b(max|min)\.?\b",
        r"\b(allowed|erlaubt|required|requirement|requirements|brauche|benoetige|muss|must)\b",
        r"\b(wahlbereich|core|kernbereich|regel|rules?)\b",
    ]
    return any(re.search(pattern, text) for pattern in patterns)


def _looks_like_course_offering_question(text: str) -> bool:
    offering_terms = [
        "angebot",
        "angeboten",
        "available",
        "course offerings",
        "findet",
        "gibt es",
        "kurse",
        "courses",
        "lecture",
        "lectures",
        "lehrveranstaltungen",
        "offered",
        "veranstaltungen",
    ]
    semester_pattern = r"\b(sose|ss|wise|ws|sommersemester|wintersemester|summer|winter)\s*[0-9]{2,4}\b"
    course_type_terms = [
        "softwareprojekt",
        "software project",
        "seminar",
        "wissenschaftliches arbeiten",
        "vorlesung",
        "lecture",
        "course",
        "courses",
    ]
    return any(term in text for term in offering_terms) or (
        bool(re.search(semester_pattern, text)) and any(term in text for term in course_type_terms)
    )


def _normalize_text(text: str) -> str:
    lowered = text.lower()
    replacements = {
        "\u00fc": "ue",
        "\u00e4": "ae",
        "\u00f6": "oe",
        "\u00df": "ss",
        "\u00c3\u00bc": "ue",
        "\u00c3\u00a4": "ae",
        "\u00c3\u00b6": "oe",
    }
    for source, target in replacements.items():
        lowered = lowered.replace(source, target)
    return lowered


async def scope_classifier_node(state: ConsultantState) -> ConsultantState:
    logger.info("Scope classifier invoked")
    wizardflow_message_id = state.get("wizardflow_message_id")
    message = latest_user_message(state)
    llm_message = f"Latest user message:\n{message}"
    fallback = heuristic_classify(message)
    source = "heuristic"

    log_llm_input(
        wizardflow_message_id,
        "scope_classifier",
        CLASSIFIER_SYSTEM_PROMPT,
        llm_message,
    )
    try:
        response = await ModelService().invoke(
            prompt=CLASSIFIER_SYSTEM_PROMPT,
            message=llm_message,
            format=CLASSIFIER_SCHEMA,
        )
        response_content = response.get("content", "")
        log_llm_output(wizardflow_message_id, "scope_classifier", response_content)
        data = parse_json_content(response_content)
        message_type = data.get("message_type")
        if message_type not in {"degree_question", "course_offering_question", "plan_check", "off_topic"}:
            message_type = fallback
            source = "heuristic_invalid_llm_output"
        else:
            source = "llm"
    except DailyQuotaExceeded:
        raise
    except Exception as exc:
        log_llm_error(wizardflow_message_id, "scope_classifier", exc)
        logger.exception("Classifier failed; using heuristic fallback.")
        message_type = fallback

    logger.info("Scope classifier chose message_type=%s source=%s", message_type, source)
    result: ConsultantState = {"message_type": message_type}
    log_node_output(
        wizardflow_message_id,
        "scope_classifier",
        {"message_type": message_type, "source": source},
    )
    return result
