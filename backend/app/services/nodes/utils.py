import difflib
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


ADVISORY_DISCLAIMER_DE = (
    "Hinweis: Diese Auskunft ist unverbindlich – maßgeblich sind die "
    "offiziellen FU-Dokumente und das Prüfungsbüro."
)
ADVISORY_DISCLAIMER_EN = (
    "Advisory: official FU documents and the examination office remain authoritative."
)

# Any sentence that reads like the advisory disclaimer, regardless of the
# model's phrasing or language.
_DISCLAIMER_SENTENCE_RE = re.compile(
    r"\s*[^.!?\n]*\b("
    r"official FU documents"
    r"|offiziellen?\s+FU[- ]Dokumenten?"
    r"|examination office remains? authoritative"
    r"|Pr(?:ü|ue)fungsb(?:ü|ue)ro\s+(?:bleib|sind|ist)"
    r")\b[^.!?\n]*[.!?]?",
    re.IGNORECASE,
)
_ORPHAN_ADVISORY_RE = re.compile(r"\s*\b(?:advisory|hinweis)\b\s*[:;.,]?\s*$", re.IGNORECASE)


def strip_advisory_disclaimer(reply: str) -> tuple[str, bool]:
    """Remove model-emitted advisory disclaimers; report whether one was found.

    The canonical, correctly localized disclaimer is re-appended by the answer
    composer, so the model's own (often English, oddly placed) phrasing never
    reaches the user.
    """

    stripped, count = _DISCLAIMER_SENTENCE_RE.subn("", reply)
    stripped = _ORPHAN_ADVISORY_RE.sub("", stripped).strip()
    return stripped, count > 0


_URL_RE = re.compile(r"https?://[^\s<>\"')\]]+")
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# Markdown links first so their URLs are not re-matched as bare URLs.
_REPLY_LINK_RE = re.compile(r"\[([^\]\n]+)\]\(([^)\s]+)\)|https?://[^\s<>\"')\]]+")
_TRAILING_PUNCTUATION = ".,;:!?"


def sanitize_reply_links(reply: str, context: str) -> str:
    """Keep only links whose URLs actually appear in the LLM context.

    Models copy long URLs imperfectly and occasionally invent plausible ones.
    URLs close to a context URL are repaired to the exact original; links to
    unknown URLs are reduced to their label text (Markdown) or removed (bare).
    """

    allowed_urls = set(_URL_RE.findall(context))
    allowed_emails = set(_EMAIL_RE.findall(context))

    def repaired_url(url: str) -> str | None:
        if url in allowed_urls:
            return url
        close = difflib.get_close_matches(url, list(allowed_urls), n=1, cutoff=0.9)
        return close[0] if close else None

    def replace(match: re.Match) -> str:
        label, target = match.group(1), match.group(2)
        if label is None:
            raw = match.group(0)
            bare = raw.rstrip(_TRAILING_PUNCTUATION)
            trailing = raw[len(bare):]
            url = repaired_url(bare)
            return f"{url}{trailing}" if url else trailing
        if target.startswith("mailto:"):
            return match.group(0) if target[len("mailto:"):] in allowed_emails else label
        if target.startswith(("http://", "https://")):
            url = repaired_url(target)
            return f"[{label}]({url})" if url else label
        return label

    return _REPLY_LINK_RE.sub(replace, reply)
