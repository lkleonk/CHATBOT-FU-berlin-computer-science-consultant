from __future__ import annotations

import logging

from app.pdf.clean import clean_pdf_text
from app.pdf.extract import PDFExtractor, PyPdfExtractor
from app.pdf.models import ExtractedDocument, ExtractedPage, PdfUnreadableError
from app.pdf.validation import validate_pdf_readability


logger = logging.getLogger(__name__)


_default_extractor: PDFExtractor = PyPdfExtractor()


def extract_and_validate(
    data: bytes,
    filename: str,
    extractor: PDFExtractor | None = None,
) -> ExtractedDocument:
    """Extract, clean, and validate a PDF, returning the cleaned document.

    Raises :class:`PdfUnreadableError` when the document fails the readability
    check, so the caller can reject scanned/image-only PDFs before anything is
    parsed or sent to the LLM. May raise :class:`PdfExtractionError` if the bytes
    are not a parseable PDF.
    """
    extractor = extractor or _default_extractor
    raw_document = extractor.extract(data, filename)

    cleaned_document = ExtractedDocument(
        filename=raw_document.filename,
        pages=[
            ExtractedPage(page=page.page, text=clean_pdf_text(page.text))
            for page in raw_document.pages
        ],
    )

    readability = validate_pdf_readability(cleaned_document)
    if not readability.is_readable:
        # Filename omitted: uploaded names can identify the student.
        logger.info("Rejected unreadable PDF: %s", readability.reason)
        raise PdfUnreadableError(readability)

    return cleaned_document
