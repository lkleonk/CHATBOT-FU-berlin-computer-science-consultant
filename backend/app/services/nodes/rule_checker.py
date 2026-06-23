import logging

from app.domain.degree_rules import validate_study_plan
from app.domain.study_plan import StudyPlan
from app.services.states.consultant_state import ConsultantState
from app.services.wizardflow_service import log_node_input, log_node_output


logger = logging.getLogger(__name__)


def check_study_plan(
    plan: StudyPlan | dict,
    wizardflow_message_id: str | None = None,
):
    log_node_input(wizardflow_message_id, "rule_checker", plan.model_dump() if isinstance(plan, StudyPlan) else plan)
    result = validate_study_plan(plan)
    log_node_output(wizardflow_message_id, "rule_checker", result.model_dump())
    return result


async def rule_checker_node(state: ConsultantState) -> ConsultantState:
    logger.info("Rule checker invoked")
    plan = state.get("parsed_study_plan") or {"modules": []}
    result = check_study_plan(plan, state.get("wizardflow_message_id"))
    return {"rule_check_result": result.model_dump()}
