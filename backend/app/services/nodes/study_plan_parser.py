import logging
import re

from app.domain.module_catalog import enrich_study_plan
from app.domain.study_plan import PlannedModule, StudyPlan
from app.prompts import STUDY_PLAN_PARSER_SYSTEM_PROMPT
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


PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "specialization_area": {
            "type": ["string", "null"],
            "enum": ["practical", "theoretical", "technical", None],
        },
        "modules": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "lp": {"type": "integer"},
                    "area": {
                        "type": "string",
                        "enum": ["practical", "theoretical", "technical", "application", "thesis", "unknown"],
                    },
                    "is_wahlbereich": {"type": "boolean"},
                    "is_ungraded": {"type": "boolean"},
                    "is_bachelor_module": {"type": "boolean"},
                    "is_scientific_work": {"type": "boolean"},
                    "is_software_project": {"type": "boolean"},
                },
                "required": [
                    "name",
                    "lp",
                    "area",
                    "is_wahlbereich",
                    "is_ungraded",
                    "is_bachelor_module",
                    "is_scientific_work",
                    "is_software_project",
                ],
            },
        },
    },
    "required": ["specialization_area", "modules"],
}


def heuristic_parse_plan(message: str) -> StudyPlan:
    lowered = message.lower()
    specialization = None
    if "vertiefung praktische" in lowered or "specialization practical" in lowered:
        specialization = "practical"
    elif "vertiefung theoretische" in lowered or "specialization theoretical" in lowered:
        specialization = "theoretical"
    elif "vertiefung technische" in lowered or "specialization technical" in lowered:
        specialization = "technical"

    modules = []
    pattern = re.compile(
        r"(?P<name>[A-ZÄÖÜ][^;\n,()]{3,}?)\s*\(?\s*(?P<lp>\d{1,2})\s*LP\)?",
        re.IGNORECASE,
    )
    for match in pattern.finditer(message):
        name = match.group("name").strip(" -:;,.")
        lp = int(match.group("lp"))
        modules.append(PlannedModule(name=name, lp=lp))

    return enrich_study_plan(StudyPlan(specialization_area=specialization, modules=modules))


async def parse_study_plan(
    text: str,
    wizardflow_message_id: str | None = None,
) -> StudyPlan:
    """Parse free-form text (chat message or extracted PDF) into a StudyPlan.

    The LLM only parses here; deterministic Python rules validate the result
    afterwards. Falls back to a heuristic parser if the LLM call fails.
    """
    fallback = heuristic_parse_plan(text)
    llm_message = f"User message:\n{text}"

    log_llm_input(
        wizardflow_message_id,
        "study_plan_parser",
        STUDY_PLAN_PARSER_SYSTEM_PROMPT,
        llm_message,
    )
    try:
        response = await ModelService().invoke(
            prompt=STUDY_PLAN_PARSER_SYSTEM_PROMPT,
            message=llm_message,
            format=PLAN_SCHEMA,
        )
        response_content = response.get("content", "")
        log_llm_output(wizardflow_message_id, "study_plan_parser", response_content)
        data = parse_json_content(response_content)
        plan = enrich_study_plan(StudyPlan.model_validate(data))
    except DailyQuotaExceeded:
        raise
    except Exception as exc:
        log_llm_error(wizardflow_message_id, "study_plan_parser", exc)
        logger.exception("Study plan parser failed; using heuristic parser.")
        plan = fallback

    log_node_output(wizardflow_message_id, "study_plan_parser", plan.model_dump())
    return plan


async def study_plan_parser_node(state: ConsultantState) -> ConsultantState:
    logger.info("Study plan parser invoked")
    message = latest_user_message(state)
    plan = await parse_study_plan(message, state.get("wizardflow_message_id"))
    return {"parsed_study_plan": plan.model_dump()}
