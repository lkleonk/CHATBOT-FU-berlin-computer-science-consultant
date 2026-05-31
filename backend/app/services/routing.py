from app.services.states.consultant_state import ConsultantState


def route_after_classifier(state: ConsultantState) -> str:
    message_type = state.get("message_type")
    if message_type == "plan_check":
        return "plan_check"
    if message_type == "study_question":
        return "study_question"
    return "off_topic"
