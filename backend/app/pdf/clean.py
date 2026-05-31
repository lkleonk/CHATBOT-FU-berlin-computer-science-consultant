from __future__ import annotations

import re


_REPEATED_SPACES = re.compile(r"[ \t]{2,}")
_TRAILING_SPACES = re.compile(r"[ \t]+\n")
_EXCESSIVE_NEWLINES = re.compile(r"\n{3,}")


def clean_pdf_text(text: str) -> str:
    """Light, lossless-enough cleaning of raw extracted PDF text.

    Intentionally conservative: it only removes null bytes, normalises line
    endings, collapses runs of spaces and blank lines, and trims surrounding
    whitespace. It must not summarise, rewrite, reorder, or drop content, so the
    downstream parser still sees the full document.
    """
    if not text:
        return ""

    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _TRAILING_SPACES.sub("\n", text)
    text = _REPEATED_SPACES.sub(" ", text)
    text = _EXCESSIVE_NEWLINES.sub("\n\n", text)
    return text.strip()
