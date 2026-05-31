from app.prompts import OFFTOPIC_REPLY_DE, OFFTOPIC_REPLY_EN
from app.services.nodes.utils import latest_user_message, looks_german
from app.services.states.consultant_state import ConsultantState


async def offtopic_node(state: ConsultantState) -> ConsultantState:
    message = latest_user_message(state)
    reply = OFFTOPIC_REPLY_DE if looks_german(message) else OFFTOPIC_REPLY_EN
    return {
        "reply": reply,
        "messages": [{"role": "assistant", "content": reply}],
    }
