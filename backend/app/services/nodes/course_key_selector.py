import logging
import re
from typing import Any

from app.domain.course_offerings import (
    available_areas,
    available_course_types,
    available_semesters,
    build_available_semesters_note,
    build_course_lookup_tree,
    has_offerings,
    iter_lookup_keys,
    lookup_key,
)
from app.domain.degrees import DEFAULT_DEGREE_ID
from app.services.agent_config import agent_flow_config
from app.services.model_service import ModelService
from app.services.quota_service import DailyQuotaExceeded
from app.services.nodes.utils import (
    degree_for,
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


COURSE_KEY_SELECTOR_SCHEMA = {
    "type": "object",
    "properties": {
        "keys": {"type": "array", "items": {"type": "string"}},
        "needs_clarification": {"type": "boolean"},
        "clarification_question": {"type": "string"},
    },
    "required": ["keys", "needs_clarification", "clarification_question"],
}


AREA_TERMS = {
    "technical": ["technical", "technisch", "technische", "technischen"],
    "practical": ["practical", "praktisch", "praktische", "praktischen"],
    "theoretical": ["theoretical", "theoretisch", "theoretische", "theoretischen"],
    "application": ["application", "anwendungsbereich", "nebenfach"],
}

COURSE_TYPE_TERMS = {
    "vl": ["vl", "vorlesung", "vorlesungen", "lecture", "lectures"],
    "swp": ["swp", "softwareprojekt", "softwareprojekte", "software project", "software projects"],
    "seminar": ["seminar", "seminare", "wissenschaftliches arbeiten", "scientific work"],
}

OFFERING_TERMS = [
    "angebot",
    "angeboten",
    "available",
    "course offerings",
    "findet",
    "gibt es",
    "kurse",
    "lehrveranstaltungen",
    "liste",
    "list",
    "offered",
    "veranstaltungen",
    "welche",
    "which",
]

RULE_QUESTION_PATTERNS = [
    r"\bhow many\b.*\b(can|may|allowed|take|count|counts|required|need|needed)\b",
    r"\bhow much\b.*\b(lp|credit|credits)\b",
    r"\bwie viele\b.*\b(darf|kann|zaehlen|zählen|belegen|machen|brauche|benoetige|benötige)\b",
    r"\bwie viel\b.*\b(lp|leistungspunkt|leistungspunkte|credits?)\b",
    r"\b(at most|at least|maximum|minimum)\b",
    r"\b(max|min)\.?\b",
    r"\b(allowed|erlaubt|required|requirement|requirements|brauche|benoetige|benötige|muss|must)\b",
    r"\b(wahlbereich|core|kernbereich|regel|rules?)\b",
]


async def course_key_selector_node(state: ConsultantState) -> ConsultantState:
    logger.info("Course key selector invoked")
    wizardflow_message_id = state.get("wizardflow_message_id")
    degree = degree_for(state)
    if not has_offerings(degree.id):
        result: ConsultantState = {
            "course_lookup_keys": [],
            "course_lookup_invalid_keys": [],
            "course_lookup_needs_clarification": False,
            "course_lookup_clarification_question": "",
            "course_lookup_message": (
                f"No local course-offering data is available for {degree.display_name} yet. "
                "Course offerings must be checked in the official FU Berlin Vorlesungsverzeichnis."
            ),
        }
        log_node_output(wizardflow_message_id, "course_key_selector", result)
        return result
    user_message = latest_user_message(state)
    semester_note = (
        build_available_semesters_note(degree.id)
        if agent_flow_config.course_key_selector.include_available_semesters_note
        else "(semester coverage note disabled)"
    )
    prompt = (
        degree.prompts.course_key_selector_template.replace(
            "{semester_coverage_note}",
            semester_note,
        ).replace(
            "{course_tree}",
            build_course_lookup_tree(degree.id),
        )
    )
    history = format_recent_messages(
        recent_messages(state, agent_flow_config.course_key_selector.history_turns)
    )
    llm_message = f"Recent conversation:\n{history}\n\nLatest user message:\n{user_message}"

    log_llm_input(
        wizardflow_message_id,
        "course_key_selector",
        prompt,
        llm_message,
    )
    try:
        response = await ModelService().invoke(
            prompt=prompt,
            message=llm_message,
            format=COURSE_KEY_SELECTOR_SCHEMA,
        )
        response_content = response.get("content", "")
        log_llm_output(wizardflow_message_id, "course_key_selector", response_content)
        data = parse_json_content(response_content)
    except DailyQuotaExceeded:
        raise
    except Exception as exc:
        log_llm_error(wizardflow_message_id, "course_key_selector", exc)
        logger.exception("Course key selection failed; using heuristic selector.")
        data = heuristic_select_course_keys(user_message, degree.id)

    selected = _sanitize_selector_result(data, user_message, degree.id)
    logger.info("Selected course lookup keys: %s", selected["course_lookup_keys"])
    log_node_output(wizardflow_message_id, "course_key_selector", selected)
    return selected


def heuristic_select_course_keys(message: str, degree_id: str = DEFAULT_DEGREE_ID) -> dict[str, Any]:
    text = _normalize_text(message)
    semester_mentions = _detect_semester_mentions(text, degree_id)
    offering_question = _looks_like_course_offering_question(text, semester_mentions)

    if not offering_question:
        return {
            "keys": [],
            "needs_clarification": False,
            "clarification_question": "",
        }

    if not semester_mentions:
        return {
            "keys": [],
            "needs_clarification": True,
            "clarification_question": "Which semester should I use for the course offering lookup?",
        }

    valid_semesters = set(available_semesters(degree_id))
    selected_semesters = [semester for semester in semester_mentions if semester in valid_semesters]
    missing_semesters = [semester for semester in semester_mentions if semester not in valid_semesters]

    if not selected_semesters:
        return {
            "keys": [],
            "needs_clarification": False,
            "clarification_question": "",
            "message": "No local course-offering data is available for semester(s): "
            + ", ".join(missing_semesters),
        }

    areas = _detect_areas(text)
    course_types = _detect_course_types(text)
    keys = _expand_keys(selected_semesters, areas, course_types, degree_id)

    return {
        "keys": keys,
        "needs_clarification": False,
        "clarification_question": "",
        "message": (
            "No local course-offering data is available for semester(s): "
            + ", ".join(missing_semesters)
            if missing_semesters
            else ""
        ),
    }


def _sanitize_selector_result(
    data: dict[str, Any],
    message: str,
    degree_id: str = DEFAULT_DEGREE_ID,
) -> ConsultantState:
    text = _normalize_text(message)
    if _looks_like_degree_rule_question(text) and not _has_explicit_offering_term(text):
        return {
            "course_lookup_keys": [],
            "course_lookup_invalid_keys": [],
            "course_lookup_needs_clarification": False,
            "course_lookup_clarification_question": "",
            "course_lookup_message": "",
        }

    valid_keys = set(iter_lookup_keys(degree_id))
    max_keys = agent_flow_config.course_key_selector.max_keys
    raw_keys = data.get("keys") if isinstance(data, dict) else []
    if not isinstance(raw_keys, list):
        raw_keys = []

    keys: list[str] = []
    invalid_keys: list[str] = []
    seen: set[str] = set()
    for raw_key in raw_keys:
        if not isinstance(raw_key, str):
            continue
        key = raw_key.strip()
        if not key:
            continue
        if key not in valid_keys:
            invalid_keys.append(key)
            continue
        if key not in seen:
            seen.add(key)
            keys.append(key)
        if max_keys and len(keys) >= max_keys:
            break

    needs_clarification = bool(data.get("needs_clarification")) if isinstance(data, dict) else False
    clarification = ""
    if isinstance(data, dict) and isinstance(data.get("clarification_question"), str):
        clarification = data["clarification_question"].strip()

    message_text = ""
    if isinstance(data, dict) and isinstance(data.get("message"), str):
        message_text = data["message"].strip()

    if not keys and not needs_clarification:
        semester_mentions = _detect_semester_mentions(text, degree_id)
        valid_semesters = set(available_semesters(degree_id))
        missing = [semester for semester in semester_mentions if semester not in valid_semesters]
        if missing and _looks_like_course_offering_question(text, semester_mentions):
            message_text = "No local course-offering data is available for semester(s): " + ", ".join(missing)

    return {
        "course_lookup_keys": keys,
        "course_lookup_invalid_keys": invalid_keys,
        "course_lookup_needs_clarification": needs_clarification,
        "course_lookup_clarification_question": clarification,
        "course_lookup_message": message_text,
    }


def _expand_keys(
    semesters: list[str],
    areas: list[str],
    course_types: list[str],
    degree_id: str = DEFAULT_DEGREE_ID,
) -> list[str]:
    valid_keys = set(iter_lookup_keys(degree_id))
    keys: list[str] = []

    for semester in semesters:
        selected_areas = areas or available_areas(degree_id, semester)
        for area in selected_areas:
            selected_types = course_types or available_course_types(degree_id, semester, area)
            for course_type in selected_types:
                key = lookup_key(semester, area, course_type)
                if key in valid_keys:
                    keys.append(key)

    return keys


def _detect_areas(text: str) -> list[str]:
    areas: list[str] = []
    for area, terms in AREA_TERMS.items():
        if any(_contains_term(text, term) for term in terms):
            areas.append(area)
    return areas


def _detect_course_types(text: str) -> list[str]:
    course_types: list[str] = []
    for course_type, terms in COURSE_TYPE_TERMS.items():
        if any(_contains_term(text, term) for term in terms):
            course_types.append(course_type)
    return course_types


def _detect_semester_mentions(text: str, degree_id: str = DEFAULT_DEGREE_ID) -> list[str]:
    mentions: list[str] = []

    for semester in available_semesters(degree_id):
        for alias in _semester_aliases(semester):
            if alias in text:
                _append_unique(mentions, semester)

    for match in re.finditer(r"\b(?:sose|ss|sommersemester|summer semester|summer)\s*([0-9]{2,4})\b", text):
        year = _two_digit_year(match.group(1))
        _append_unique(mentions, f"sose{year}")

    for match in re.finditer(
        r"\b(?:wise|ws|wintersemester|winter semester|winter)\s*([0-9]{2,4})(?:\s*[-/]\s*([0-9]{2,4}))?\b",
        text,
    ):
        first = _two_digit_year(match.group(1))
        second = _two_digit_year(match.group(2)) if match.group(2) else str(int(first) + 1).zfill(2)
        _append_unique(mentions, f"wise{first}-{second}")

    return mentions


def _semester_aliases(semester: str) -> list[str]:
    aliases = [semester, semester.replace("-", "/"), semester.replace("-", " ")]
    sose_match = re.fullmatch(r"sose([0-9]{2})", semester)
    if sose_match:
        year = sose_match.group(1)
        aliases.extend([f"sose {year}", f"ss{year}", f"ss {year}", f"sommersemester 20{year}", f"summer 20{year}"])

    wise_match = re.fullmatch(r"wise([0-9]{2})-([0-9]{2})", semester)
    if wise_match:
        first, second = wise_match.groups()
        aliases.extend(
            [
                f"wise {first}/{second}",
                f"wise {first}-{second}",
                f"ws{first}/{second}",
                f"ws {first}/{second}",
                f"wintersemester 20{first}/{second}",
                f"winter 20{first}/{second}",
            ]
        )

    return aliases


def _looks_like_course_offering_question(text: str, semester_mentions: list[str]) -> bool:
    if _looks_like_degree_rule_question(text) and not _has_explicit_offering_term(text):
        return False
    if _has_explicit_offering_term(text):
        return True
    return bool(semester_mentions)


def _has_explicit_offering_term(text: str) -> bool:
    return any(term in text for term in OFFERING_TERMS)


def _looks_like_degree_rule_question(text: str) -> bool:
    return any(re.search(pattern, text) for pattern in RULE_QUESTION_PATTERNS)


def _contains_term(text: str, term: str) -> bool:
    if " " in term:
        return term in text
    return bool(re.search(rf"\b{re.escape(term)}\b", text))


def _normalize_text(text: str) -> str:
    return text.lower().replace("ü", "ue").replace("ä", "ae").replace("ö", "oe").replace("ß", "ss")


def _two_digit_year(value: str) -> str:
    return value[-2:]


def _append_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)
