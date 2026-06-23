from app.prompts import OFFTOPIC_REPLY_DE, OFFTOPIC_REPLY_EN
from app.services.nodes.utils import latest_user_message, looks_german
from app.services.states.consultant_state import ConsultantState
from app.services.wizardflow_service import log_node_input, log_node_output


async def offtopic_node(state: ConsultantState) -> ConsultantState:
    wizardflow_message_id = state.get("wizardflow_message_id")
    message = latest_user_message(state)
    log_node_input(wizardflow_message_id, "offtopic", {"message": message})
    reply = OFFTOPIC_REPLY_DE if looks_german(message) else OFFTOPIC_REPLY_EN
    result: ConsultantState = {
        "reply": reply,
        "messages": [{"role": "assistant", "content": reply}],
    }
    log_node_output(wizardflow_message_id, "offtopic", result)
    return result
