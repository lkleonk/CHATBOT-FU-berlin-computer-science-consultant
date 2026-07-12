import logging
from typing import Any

import wizardflow

from app.settings import settings


logger = logging.getLogger(__name__)

tracer = None


def initialize_wizardflow(agent_app: Any) -> None:
    """Initialize one process-wide WizardFlow tracer from the compiled graph."""
    global tracer

    if not settings.WIZARDFLOW.ENABLED or tracer is not None:
        return

    try:
        tracer = wizardflow.init_from_langgraph(
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
        logger.info("WizardFlow tracing initialized: %s", tracer.current_path)
    except Exception:
        tracer = None
        logger.exception("Failed to initialize WizardFlow tracing")


def reinit_tracing() -> str | None:
    """Start a new trace file, keeping graph and output configuration.

    Returns the new trace path, or None when tracing is disabled. Errors
    propagate so the manual trigger surfaces them instead of silently
    continuing in the old file.
    """
    if tracer is None:
        return None

    path = str(tracer.reinit())
    logger.info("WizardFlow trace file rotated: %s", path)
    return path


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
    if not message_id or tracer is None:
        return

    try:
        path = tracer.end_message(message_id, title=title)
        logger.info("WizardFlow message written: %s", path)
    except Exception:
        logger.exception("Failed to finalize WizardFlow message %s", message_id)


def _log(message_id: str | None, node: str, label: str, content: Any) -> None:
    if not message_id or tracer is None:
        return

    try:
        tracer.log(message_id, node, label, content)
    except Exception:
        logger.exception(
            "Failed to write WizardFlow payload message_id=%s node=%s label=%s",
            message_id,
            node,
            label,
        )
