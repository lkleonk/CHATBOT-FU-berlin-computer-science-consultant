from app.services.agent_config import agent_flow_config
from app.services.nodes.utils import format_recent_messages, recent_messages


def test_agent_flow_config_values_are_available():
    assert isinstance(agent_flow_config.course_key_selector.history_turns, int)
    assert isinstance(agent_flow_config.course_key_selector.max_keys, int)
    assert isinstance(agent_flow_config.course_key_selector.include_available_semesters_note, bool)
    assert isinstance(agent_flow_config.answer_composer.history_turns, int)


def test_recent_messages_keeps_last_n_user_turns():
    state = {
        "messages": [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "first answer"},
            {"role": "user", "content": "second"},
            {"role": "assistant", "content": "second answer"},
            {"role": "user", "content": "third"},
        ]
    }

    messages = recent_messages(state, turns=2)

    assert [message["content"] for message in messages] == [
        "second",
        "second answer",
        "third",
    ]


def test_format_recent_messages_preserves_roles():
    text = format_recent_messages(
        [
            {"role": "user", "content": "What SWPs are offered in sose26?"},
            {"role": "assistant", "content": "I found SWP buckets."},
        ]
    )

    assert "user: What SWPs are offered in sose26?" in text
    assert "assistant: I found SWP buckets." in text
