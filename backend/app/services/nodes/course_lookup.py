import logging

from app.domain.course_offerings import (
    build_course_citations,
    format_course_lookup_context,
    lookup_course_buckets,
)
from app.services.states.consultant_state import ConsultantState


logger = logging.getLogger(__name__)


async def course_lookup_node(state: ConsultantState) -> ConsultantState:
    logger.info("Course lookup invoked")

    if state.get("course_lookup_needs_clarification"):
        question = state.get("course_lookup_clarification_question") or (
            "Which semester should I use for the course offering lookup?"
        )
        return {
            "retrieved_context": f"Course lookup needs clarification: {question}",
            "citations": [],
        }

    keys = state.get("course_lookup_keys") or []
    invalid_keys = state.get("course_lookup_invalid_keys") or []
    message = state.get("course_lookup_message")
    notes = [message] if message else []

    if not keys:
        context = format_course_lookup_context([], invalid_keys=invalid_keys, notes=notes)
        return {
            "retrieved_context": context,
            "citations": [],
        }

    buckets, missing_keys = lookup_course_buckets(keys)
    context = format_course_lookup_context(
        buckets,
        invalid_keys=[*invalid_keys, *missing_keys],
        notes=notes,
    )
    citations = build_course_citations(buckets)

    logger.info("Course lookup returned %d bucket(s)", len(buckets))
    return {
        "retrieved_context": context,
        "citations": citations,
    }
