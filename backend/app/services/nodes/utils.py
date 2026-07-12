import json
import re
from typing import Any

from app.domain.degrees import DegreeDefinition, get_degree_or_default


def degree_for(state: dict[str, Any]) -> DegreeDefinition:
    return get_degree_or_default(state.get("degree_id"))


def latest_user_message(state: dict[str, Any]) -> str:
    for message in reversed(state.get("messages", []) or []):
        if message.get("role") == "user":
            return message.get("content", "")
    return ""


def recent_messages(state: dict[str, Any], turns: int) -> list[dict[str, str]]:
    messages = [
        {"role": message.get("role", ""), "content": message.get("content", "")}
        for message in (state.get("messages") or [])
        if isinstance(message, dict)
        and isinstance(message.get("role"), str)
        and isinstance(message.get("content"), str)
        and message.get("content", "").strip()
    ]
    if turns <= 0 or not messages:
        return []

    user_messages_seen = 0
    start_index = 0
    for index in range(len(messages) - 1, -1, -1):
        if messages[index]["role"] == "user":
            user_messages_seen += 1
            if user_messages_seen == turns:
                start_index = index
                break

    return messages[start_index:]


def format_recent_messages(messages: list[dict[str, str]]) -> str:
    if not messages:
        return "(no recent conversation)"

    lines = []
    for message in messages:
        role = message.get("role", "message").strip() or "message"
        content = message.get("content", "").strip()
        if not content:
            continue
        lines.append(f"{role}: {content}")
    return "\n".join(lines) if lines else "(no recent conversation)"


def extract_first_json_object(text: str) -> str | None:
    start = text.find("{")
    if start < 0:
        return None

    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None


def parse_json_content(content: str) -> dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        extracted = extract_first_json_object(content)
        if extracted:
            return json.loads(extracted)
        raise


def looks_german(text: str) -> bool:
    lowered = text.lower()
    return bool(re.search(r"\b(der|die|das|und|ich|ist|sind|module|vertiefung|prüf|pruef|lp)\b", lowered))
