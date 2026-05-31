import logging

from app.prompts import QUERY_REWRITER_SYSTEM_PROMPT
from app.services.model_service import ModelService
from app.services.nodes.utils import latest_user_message, parse_json_content
from app.services.states.consultant_state import ConsultantState


logger = logging.getLogger(__name__)


QUERY_SCHEMA = {
    "type": "object",
    "properties": {
        "retrieval_query": {"type": "string"},
    },
    "required": ["retrieval_query"],
}


async def query_rewriter_node(state: ConsultantState) -> ConsultantState:
    logger.info("Query rewriter invoked")
    message = latest_user_message(state)
    try:
        response = await ModelService().invoke(
            prompt=QUERY_REWRITER_SYSTEM_PROMPT,
            message=f"User message:\n{message}",
            format=QUERY_SCHEMA,
        )
        data = parse_json_content(response.get("content", ""))
        retrieval_query = (data.get("retrieval_query") or message).strip()
    except Exception:
        logger.exception("Query rewrite failed; using raw user message.")
        retrieval_query = message
    return {"retrieval_query": retrieval_query}
