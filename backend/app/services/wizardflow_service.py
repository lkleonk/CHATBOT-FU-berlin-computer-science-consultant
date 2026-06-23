import logging
from typing import Any

import wizardflow

from app.settings import settings


logger = logging.getLogger(__name__)

_client: Any | None = None


def initialize_wizardflow(agent_app: Any) -> None:
    """Initialize one process-wide WizardFlow client from the compiled graph."""
    global _client

    if not settings.WIZARDFLOW.ENABLED or _client is not None:
        return

    try:
        _client = wizardflow.init_from_langgraph(
            agent_app,
            output_dir=str(settings.WIZARDFLOW.OUTPUT_DIR),
            file_prefix=settings.WIZARDFLOW.FILE_PREFIX,
            name="FU Berlin CS Consultant",
            description="LangGraph traces for consultant messages and transcript uploads.",
            meta={
                "llm_provider": settings.provider_name(),
                "llm_model": settings.active_model_name(),
            },
        )
        logger.info("WizardFlow tracing initialized: %s", _client.current_path)
    except Exception:
        _client = None
        logger.exception("Failed to initialize WizardFlow tracing")


def start_message(message_id: str, request_kind: str) -> None:
    _log(message_id, "__start__", "request", {"kind": request_kind})


def log_llm_input(message_id: str | None, node: str, prompt: str, msg: str) -> None:
    _log(message_id, node, "llm_input", {"prompt": prompt, "msg": msg})


def log_llm_output(message_id: str | None, node: str, output: Any) -> None:
    _log(message_id, node, "llm_output", output)


def log_llm_error(message_id: str | None, node: str, error: Exception) -> None:
    _log(
        message_id,
        node,
        "llm_error",
        {"type": type(error).__name__, "message": str(error)},
    )


def log_node_input(message_id: str | None, node: str, content: Any) -> None:
    _log(message_id, node, "node_input", content)


def log_node_output(message_id: str | None, node: str, content: Any) -> None:
    _log(message_id, node, "node_output", content)


def end_message(message_id: str, title: str | None = None) -> None:
    if not message_id or _client is None:
        return

    try:
        _client.log(message_id, "__end__")
        path = _client.end_message(message_id, title=title)
        logger.info("WizardFlow message written: %s", path)
    except Exception:
        logger.exception("Failed to finalize WizardFlow message %s", message_id)


def _log(message_id: str | None, node: str, label: str, content: Any) -> None:
    if not message_id or _client is None:
        return

    try:
        _client.log(message_id, node, label, content)
    except Exception:
        logger.exception(
            "Failed to write WizardFlow payload message_id=%s node=%s label=%s",
            message_id,
            node,
            label,
        )
