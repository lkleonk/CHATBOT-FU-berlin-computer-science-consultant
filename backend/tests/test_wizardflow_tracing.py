import asyncio
import json
import uuid
from pathlib import Path

import wizardflow
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.domain.degrees import get_degree_or_default
from app.routes import tracing_router
from app.services import wizardflow_service
from app.services.nodes import scope_classifier
from app.services.session_service import SessionService


def test_wizardflow_payloads_include_prompt_and_msg(tmp_path, monkeypatch):
    client = wizardflow.init(
        output_dir=str(tmp_path),
        nodes=["__start__", "scope_classifier", "__end__"],
    )
    monkeypatch.setattr(wizardflow_service, "tracer", client)

    wizardflow_service.log_llm_input(
        "message-1",
        "scope_classifier",
        "system prompt",
        "user message",
    )
    wizardflow_service.log_llm_output(
        "message-1",
        "scope_classifier",
        '{"message_type":"degree_question"}',
    )
    wizardflow_service.end_message("message-1", title="Question")

    records = [
        json.loads(line)
        for line in Path(client.current_path).read_text(encoding="utf-8").splitlines()
    ]
    message = next(record for record in records if record["type"] == "message")
    classifier_step = next(
        step for step in message["steps"] if step["nodeId"] == "scope_classifier"
    )

    assert all(step["nodeId"] != "__start__" for step in message["steps"])
    assert all(step["nodeId"] != "__end__" for step in message["steps"])
    assert classifier_step["payloads"] == [
        {
            "label": "llm_input",
            "value": {"prompt": "system prompt", "msg": "user message"},
        },
        {
            "label": "llm_output",
            "value": '{"message_type":"degree_question"}',
        },
    ]


def test_session_service_adds_a_unique_wizardflow_id_to_graph_state(monkeypatch):
    captured = {}

    class FakeAgentApp:
        async def ainvoke(self, state, config):
            captured["state"] = state
            captured["config"] = config
            return {
                "reply": "Answer",
                "message_type": "degree_question",
                "citations": [],
            }

    ends = []
    monkeypatch.setattr(
        "app.services.session_service._get_agent_app",
        lambda: FakeAgentApp(),
    )
    monkeypatch.setattr(
        wizardflow_service,
        "end_message",
        lambda message_id, title=None: ends.append((message_id, title)),
    )

    reply = asyncio.run(SessionService().process_message("session-1", "How many LP?"))

    message_id = captured["state"]["wizardflow_message_id"]
    uuid.UUID(message_id)
    assert reply.reply == "Answer"
    assert ends == [(message_id, "How many LP?")]


def test_session_service_writes_no_trace_payloads_when_the_client_opts_out(tmp_path, monkeypatch):
    class FakeAgentApp:
        async def ainvoke(self, state, config):
            # Mirror a node: log through the real service using the state's id.
            wizardflow_service.log_llm_input(
                state["wizardflow_message_id"],
                "scope_classifier",
                "system prompt",
                "user message",
            )
            return {"reply": "Answer", "message_type": "degree_question", "citations": []}

    tracer = wizardflow.init(
        output_dir=str(tmp_path),
        nodes=["__start__", "scope_classifier", "__end__"],
    )
    monkeypatch.setattr(wizardflow_service, "tracer", tracer)
    monkeypatch.setattr(
        "app.services.session_service._get_agent_app",
        lambda: FakeAgentApp(),
    )

    reply = asyncio.run(
        SessionService().process_message("session-1", "How many LP?", tracing_enabled=False)
    )

    assert reply.reply == "Answer"
    # An empty id disables tracing, so nothing was written and the lazily
    # created trace file never came into existence.
    assert not Path(tracer.current_path).exists()


def _tracing_client() -> TestClient:
    app = FastAPI()
    app.include_router(tracing_router)
    return TestClient(app)


def test_tracing_reinit_returns_conflict_when_tracing_is_disabled(monkeypatch):
    monkeypatch.setattr(wizardflow_service, "tracer", None)
    monkeypatch.setattr(wizardflow_service.settings.WIZARDFLOW, "ENABLED", False)

    with _tracing_client() as client:
        response = client.post("/api/tracing/reinit")

    assert response.status_code == 409
    assert response.json()["detail"]["error_code"] == "tracing_disabled"


def test_tracing_reinit_starts_a_new_trace_file(tmp_path, monkeypatch):
    tracer = wizardflow.init(
        output_dir=str(tmp_path),
        nodes=["__start__", "scope_classifier", "__end__"],
    )
    old_path = str(tracer.current_path)
    monkeypatch.setattr(wizardflow_service, "tracer", tracer)

    with _tracing_client() as client:
        response = client.post("/api/tracing/reinit")

    assert response.status_code == 200
    new_path = response.json()["trace_path"]
    assert new_path == str(tracer.current_path)
    assert new_path != old_path


def test_scope_classifier_logs_the_exact_llm_input(monkeypatch):
    captured = {}

    class FakeModelService:
        async def invoke(self, prompt, message, format):
            return {"content": '{"message_type":"degree_question"}'}

    monkeypatch.setattr(scope_classifier, "ModelService", FakeModelService)
    monkeypatch.setattr(
        scope_classifier,
        "log_llm_input",
        lambda message_id, node, prompt, msg: captured.update(
            message_id=message_id,
            node=node,
            prompt=prompt,
            msg=msg,
        ),
    )
    monkeypatch.setattr(scope_classifier, "log_llm_output", lambda *args: None)
    monkeypatch.setattr(scope_classifier, "log_node_output", lambda *args: None)

    result = asyncio.run(
        scope_classifier.scope_classifier_node(
            {
                "wizardflow_message_id": "trace-id",
                "messages": [{"role": "user", "content": "How many LP do I need?"}],
            }
        )
    )

    assert result == {"message_type": "degree_question"}
    assert captured["message_id"] == "trace-id"
    assert captured["node"] == "scope_classifier"
    assert captured["prompt"] == get_degree_or_default(None).prompts.classifier_system_prompt
    assert captured["msg"] == "Latest user message:\nHow many LP do I need?"
