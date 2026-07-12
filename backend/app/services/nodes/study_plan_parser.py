import logging
import re

from app.domain.degrees import DegreeDefinition, get_degree_or_default
from app.domain.study_plan import PlannedModule, StudyPlan
from app.services.model_service import ModelService
from app.services.quota_service import DailyQuotaExceeded
from app.services.nodes.utils import degree_for, latest_user_message, parse_json_content
from app.services.states.consultant_state import ConsultantState
from app.services.wizardflow_service import (
    log_llm_error,
    log_llm_input,
    log_llm_output,
    log_node_output,
)


logger = logging.getLogger(__name__)


def heuristic_parse_plan(message: str, degree: DegreeDefinition | None = None) -> StudyPlan:
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

    enrich = (degree or get_degree_or_default(None)).enrich_study_plan
    return enrich(StudyPlan(specialization_area=specialization, modules=modules))


async def parse_study_plan(
    text: str,
    wizardflow_message_id: str | None = None,
    degree: DegreeDefinition | None = None,
) -> StudyPlan:
    """Parse free-form text (chat message or extracted PDF) into a StudyPlan.

    The LLM only parses here; deterministic Python rules validate the result
    afterwards. Falls back to a heuristic parser if the LLM call fails.
    """
    degree = degree or get_degree_or_default(None)
    parser_prompt = degree.prompts.study_plan_parser_system_prompt
    fallback = heuristic_parse_plan(text, degree)
    llm_message = f"User message:\n{text}"

    log_llm_input(
        wizardflow_message_id,
        "study_plan_parser",
        parser_prompt,
        llm_message,
    )
    try:
        response = await ModelService().invoke(
            prompt=parser_prompt,
            message=llm_message,
            format=degree.study_plan_schema,
        )
        response_content = response.get("content", "")
        log_llm_output(wizardflow_message_id, "study_plan_parser", response_content)
        data = parse_json_content(response_content)
        plan = degree.enrich_study_plan(StudyPlan.model_validate(data))
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
    plan = await parse_study_plan(message, state.get("wizardflow_message_id"), degree_for(state))
    return {"parsed_study_plan": plan.model_dump()}
