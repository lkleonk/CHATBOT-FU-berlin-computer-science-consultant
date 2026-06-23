import asyncio
import json
import uuid
from pathlib import Path

import wizardflow

from app.services import wizardflow_service
from app.services.nodes import scope_classifier
from app.services.session_service import SessionService


def test_wizardflow_payloads_include_prompt_and_msg(tmp_path, monkeypatch):
    client = wizardflow.init(
        output_dir=str(tmp_path),
        nodes=["__start__", "scope_classifier", "__end__"],
    )
    monkeypatch.setattr(wizardflow_service, "_client", client)

    wizardflow_service.start_message("message-1", "chat")
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

    starts = []
    ends = []
    monkeypatch.setattr(
        "app.services.session_service._get_agent_app",
        lambda: FakeAgentApp(),
    )
    monkeypatch.setattr(
        wizardflow_service,
        "start_message",
        lambda message_id, request_kind: starts.append((message_id, request_kind)),
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
    assert starts == [(message_id, "chat")]
    assert ends == [(message_id, "How many LP?")]


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
    assert captured["prompt"] == scope_classifier.CLASSIFIER_SYSTEM_PROMPT
    assert captured["msg"] == "Latest user message:\nHow many LP do I need?"
