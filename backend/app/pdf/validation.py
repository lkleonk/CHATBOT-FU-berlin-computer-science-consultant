from __future__ import annotations

from app.pdf.models import ExtractedDocument, ReadabilityResult


# A page counts as readable when it yields more than this many characters.
READABLE_PAGE_MIN_CHARS = 100

# Reject when fewer than this fraction of pages are readable...
MIN_READABLE_RATIO = 0.5

# ...or when the whole document yields less text than this.
MIN_TOTAL_TEXT_LENGTH = 300


def validate_pdf_readability(document: ExtractedDocument) -> ReadabilityResult:
    """Decide whether an extracted PDF carries enough real text to use.

    This is the gate that keeps scanned / image-only PDFs (which extract to
    little or no text) from ever reaching the LLM. We do not OCR; an unreadable
    PDF is rejected outright.
    """
    total_pages = document.total_pages
    readable_pages = sum(
        1 for page in document.pages if len(page.text) > READABLE_PAGE_MIN_CHARS
    )
    total_text_length = sum(len(page.text) for page in document.pages)

    if total_pages == 0:
        return ReadabilityResult(
            is_readable=False,
            total_pages=0,
            readable_pages=0,
            total_text_length=0,
            reason="The PDF contains no extractable pages.",
        )

    if total_text_length < MIN_TOTAL_TEXT_LENGTH:
        return ReadabilityResult(
            is_readable=False,
            total_pages=total_pages,
            readable_pages=readable_pages,
            total_text_length=total_text_length,
            reason=(
                f"Only {total_text_length} characters of text were extracted "
                f"(minimum {MIN_TOTAL_TEXT_LENGTH})."
            ),
        )

    readable_ratio = readable_pages / total_pages
    if readable_ratio < MIN_READABLE_RATIO:
        return ReadabilityResult(
            is_readable=False,
            total_pages=total_pages,
            readable_pages=readable_pages,
            total_text_length=total_text_length,
            reason=(
                f"Only {readable_pages}/{total_pages} pages contain readable text "
                f"(minimum {int(MIN_READABLE_RATIO * 100)}%)."
            ),
        )

    return ReadabilityResult(
        is_readable=True,
        total_pages=total_pages,
        readable_pages=readable_pages,
        total_text_length=total_text_length,
    )
