import logging

from app.domain.degree_rules import validate_study_plan
from app.services.states.consultant_state import ConsultantState


logger = logging.getLogger(__name__)


async def rule_checker_node(state: ConsultantState) -> ConsultantState:
    logger.info("Rule checker invoked")
    plan = state.get("parsed_study_plan") or {"modules": []}
    result = validate_study_plan(plan)
    return {"rule_check_result": result.model_dump()}
