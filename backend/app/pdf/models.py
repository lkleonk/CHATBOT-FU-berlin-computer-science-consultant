from __future__ import annotations

from pydantic import BaseModel, Field


class ExtractedPage(BaseModel):
    """Text extracted from a single PDF page (1-indexed)."""

    page: int
    text: str = ""


class ExtractedDocument(BaseModel):
    """Per-page extraction result for one uploaded PDF."""

    filename: str
    pages: list[ExtractedPage] = Field(default_factory=list)

    @property
    def total_pages(self) -> int:
        return len(self.pages)

    @property
    def full_text(self) -> str:
        return "\n\n".join(page.text for page in self.pages if page.text).strip()


class ReadabilityResult(BaseModel):
    """Verdict from the deterministic readability check."""

    is_readable: bool
    total_pages: int
    readable_pages: int
    total_text_length: int
    reason: str | None = None


class PdfUnreadableError(Exception):
    """Raised when an extracted PDF does not pass the readability check.

    Carries the structured :class:`ReadabilityResult` so the API layer can return
    diagnostic detail and the frontend can show the unreadable-PDF dialog.
    """

    def __init__(self, readability: ReadabilityResult):
        self.readability = readability
        super().__init__(readability.reason or "PDF is not readable.")
