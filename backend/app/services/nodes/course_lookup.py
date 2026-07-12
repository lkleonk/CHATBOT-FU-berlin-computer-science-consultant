import logging

from app.domain.course_offerings import (
    build_course_citations,
    format_course_lookup_context,
    lookup_course_buckets,
)
from app.services.nodes.utils import degree_for
from app.services.states.consultant_state import ConsultantState
from app.services.wizardflow_service import log_node_input, log_node_output


logger = logging.getLogger(__name__)


async def course_lookup_node(state: ConsultantState) -> ConsultantState:
    logger.info("Course lookup invoked")
    wizardflow_message_id = state.get("wizardflow_message_id")
    log_node_input(
        wizardflow_message_id,
        "course_lookup",
        {
            "keys": state.get("course_lookup_keys") or [],
            "invalid_keys": state.get("course_lookup_invalid_keys") or [],
            "needs_clarification": bool(state.get("course_lookup_needs_clarification")),
        },
    )

    if state.get("course_lookup_needs_clarification"):
        question = state.get("course_lookup_clarification_question") or (
            "Which semester should I use for the course offering lookup?"
        )
        result: ConsultantState = {
            "retrieved_context": f"Course lookup needs clarification: {question}",
            "citations": [],
        }
        log_node_output(wizardflow_message_id, "course_lookup", result)
        return result

    keys = state.get("course_lookup_keys") or []
    invalid_keys = state.get("course_lookup_invalid_keys") or []
    message = state.get("course_lookup_message")
    notes = [message] if message else []

    if not keys:
        context = format_course_lookup_context([], invalid_keys=invalid_keys, notes=notes)
        result = {
            "retrieved_context": context,
            "citations": [],
        }
        log_node_output(wizardflow_message_id, "course_lookup", result)
        return result

    buckets, missing_keys = lookup_course_buckets(degree_for(state).id, keys)
    context = format_course_lookup_context(
        buckets,
        invalid_keys=[*invalid_keys, *missing_keys],
        notes=notes,
    )
    citations = build_course_citations(buckets)

    logger.info("Course lookup returned %d bucket(s)", len(buckets))
    result = {
        "retrieved_context": context,
        "citations": citations,
    }
    log_node_output(wizardflow_message_id, "course_lookup", result)
    return result
