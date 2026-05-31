"""PDF transcript ingestion: extraction, cleaning, and readability validation.

The extraction layer is intentionally pluggable (see ``PDFExtractor``) so a future
OCR-based extractor can replace ``PyPdfExtractor`` without touching cleaning,
validation, parsing, or LLM integration.
"""

from app.pdf.clean import clean_pdf_text
from app.pdf.extract import PDFExtractor, PdfExtractionError, PyPdfExtractor
from app.pdf.models import (
    ExtractedDocument,
    ExtractedPage,
    PdfUnreadableError,
    ReadabilityResult,
)
from app.pdf.service import extract_and_validate
from app.pdf.validation import validate_pdf_readability


__all__ = [
    "clean_pdf_text",
    "PDFExtractor",
    "PdfExtractionError",
    "PyPdfExtractor",
    "ExtractedDocument",
    "ExtractedPage",
    "PdfUnreadableError",
    "ReadabilityResult",
    "extract_and_validate",
    "validate_pdf_readability",
]
