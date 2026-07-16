from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from io import BytesIO

from app.pdf.models import ExtractedDocument, ExtractedPage


logger = logging.getLogger(__name__)


class PdfExtractionError(Exception):
    """Raised when a file cannot be opened/parsed as a PDF at all."""


class PDFExtractor(ABC):
    """Pluggable text-extraction interface.

    Implementations return raw per-page text. Cleaning and readability checks
    live in separate stages, so swapping this for an OCR-backed extractor later
    requires no changes to validation, parsing, storage, or LLM integration.
    """

    @abstractmethod
    def extract(self, data: bytes, filename: str) -> ExtractedDocument:
        """Extract raw text from PDF ``data``, one entry per page."""


class PyPdfExtractor(PDFExtractor):
    """Text extractor backed by ``pypdf`` (no OCR)."""

    def extract(self, data: bytes, filename: str) -> ExtractedDocument:
        try:
            from pypdf import PdfReader
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise PdfExtractionError("pypdf is not installed.") from exc

        try:
            reader = PdfReader(BytesIO(data))
        except Exception as exc:
            raise PdfExtractionError("The file could not be read as a PDF.") from exc

        pages: list[ExtractedPage] = []
        for index, page in enumerate(reader.pages, start=1):
            try:
                raw = page.extract_text() or ""
            except Exception:
                # Filename omitted: uploaded names can identify the student.
                logger.warning("Failed to extract text from page %s of %s pages", index, len(reader.pages))
                raw = ""
            pages.append(ExtractedPage(page=index, text=raw))

        return ExtractedDocument(filename=filename, pages=pages)
