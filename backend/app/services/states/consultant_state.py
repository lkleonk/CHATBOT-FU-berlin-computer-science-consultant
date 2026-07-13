from typing import Annotated, Any, Literal

from typing_extensions import TypedDict


def append_messages(existing: list[dict[str, str]] | None, update: list[dict[str, str]] | None):
    if not existing:
        return update or []
    if not update:
        return existing
    return existing + update


class ConsultantState(TypedDict, total=False):
    messages: Annotated[list[dict[str, str]], append_messages]
    degree_id: str
    wizardflow_message_id: str
    message_type: Literal["degree_question", "course_offering_question", "plan_check", "off_topic"]
    course_lookup_keys: list[str]
    course_lookup_invalid_keys: list[str]
    course_lookup_needs_clarification: bool
    course_lookup_clarification_question: str | None
    course_lookup_message: str | None
    course_context: str | None
    citations: list[dict[str, Any]]
    parsed_study_plan: dict[str, Any] | None
    rule_check_result: dict[str, Any] | None
    reply: str | None
