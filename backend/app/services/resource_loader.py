import hashlib
import re
from dataclasses import dataclass
from pathlib import Path


HEADING_RE = re.compile(
    r"^("
    r"Ablauf des Studiums|Randbedingungen|Allgemeines:|"
    r"[A-E]\.\s+.+|"
    r"\d+\.\s+Module\s+.+|"
    r"Module\s+.+|"
    r"Summe\s+LP\s+.+"
    r")$"
)


@dataclass(frozen=True)
class TextChunk:
    content: str
    section_heading: str | None
    page: int | None = None


def decode_text_file(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\f", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def content_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def detect_title(path: Path, text: str) -> str:
    for line in normalize_text(text).splitlines():
        cleaned = line.strip()
        if cleaned:
            return cleaned[:160]
    return path.stem


def _is_heading(line: str) -> bool:
    cleaned = line.strip()
    if not cleaned:
        return False
    if HEADING_RE.match(cleaned):
        return True
    return len(cleaned) <= 90 and cleaned.endswith(":")


def _split_long_section(text: str, max_chars: int) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for paragraph in paragraphs:
        next_len = current_len + len(paragraph) + 2
        if current and next_len > max_chars:
            chunks.append("\n\n".join(current).strip())
            current = [paragraph]
            current_len = len(paragraph)
        else:
            current.append(paragraph)
            current_len = next_len

    if current:
        chunks.append("\n\n".join(current).strip())
    return chunks


def chunk_text(
    text: str,
    *,
    default_heading: str | None = None,
    page: int | None = None,
    max_chars: int = 1400,
) -> list[TextChunk]:
    normalized = normalize_text(text)
    if not normalized:
        return []

    sections: list[tuple[str | None, str]] = []
    current_heading = default_heading
    current_lines: list[str] = []

    for line in normalized.splitlines():
        stripped = line.strip()
        if _is_heading(stripped):
            if current_lines:
                sections.append((current_heading, "\n".join(current_lines).strip()))
            current_heading = stripped
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_heading, "\n".join(current_lines).strip()))

    if not sections:
        sections = [(default_heading, normalized)]

    chunks: list[TextChunk] = []
    for heading, body in sections:
        for part in _split_long_section(body, max_chars=max_chars):
            chunks.append(TextChunk(content=part, section_heading=heading, page=page))
    return chunks


def load_text_resource(path: Path) -> tuple[str, list[TextChunk]]:
    text = decode_text_file(path)
    title = detect_title(path, text)
    return title, chunk_text(text, default_heading=title)
