from app.services.nodes.utils import degree_for, latest_user_message, looks_german
from app.services.states.consultant_state import ConsultantState
from app.services.wizardflow_service import log_node_input, log_node_output


async def offtopic_node(state: ConsultantState) -> ConsultantState:
    wizardflow_message_id = state.get("wizardflow_message_id")
    prompts = degree_for(state).prompts
    message = latest_user_message(state)
    log_node_input(wizardflow_message_id, "offtopic", {"message": message})
    reply = prompts.offtopic_reply_de if looks_german(message) else prompts.offtopic_reply_en
    result: ConsultantState = {
        "reply": reply,
        "messages": [{"role": "assistant", "content": reply}],
    }
    log_node_output(wizardflow_message_id, "offtopic", result)
    return result
