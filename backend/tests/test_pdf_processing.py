import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.pdf.clean import clean_pdf_text  # noqa: E402
from app.pdf.extract import PDFExtractor  # noqa: E402
from app.pdf.models import ExtractedDocument, ExtractedPage, PdfUnreadableError  # noqa: E402
from app.pdf.service import extract_and_validate  # noqa: E402
from app.pdf.validation import validate_pdf_readability  # noqa: E402


RESOURCE_PDF = (
    Path(__file__).resolve().parents[2] / "ressources" / "Leistungsuebersicht.pdf"
)


def _page(text: str, number: int = 1) -> ExtractedPage:
    return ExtractedPage(page=number, text=text)


def test_clean_pdf_text_is_conservative():
    raw = "Telematik\x00   10 LP\r\n\r\n\r\n\r\nNote   4,0   \n"
    cleaned = clean_pdf_text(raw)
    assert "\x00" not in cleaned
    assert "   " not in cleaned
    assert "\n\n\n" not in cleaned
    assert cleaned.startswith("Telematik 10 LP")
    # Content is preserved, not summarised away.
    assert "Note 4,0" in cleaned


def test_clean_pdf_text_handles_empty():
    assert clean_pdf_text("") == ""


def test_validate_readability_accepts_text_pages():
    document = ExtractedDocument(
        filename="ok.pdf",
        pages=[_page("x" * 200, 1), _page("y" * 200, 2)],
    )
    result = validate_pdf_readability(document)
    assert result.is_readable
    assert result.readable_pages == 2


def test_validate_readability_rejects_short_total():
    document = ExtractedDocument(filename="tiny.pdf", pages=[_page("only a little", 1)])
    result = validate_pdf_readability(document)
    assert not result.is_readable
    assert result.reason


def test_validate_readability_rejects_low_ratio():
    # One rich page, three near-empty pages -> ratio 0.25 < 0.5, even though
    # total length passes the 300-char floor.
    document = ExtractedDocument(
        filename="scanned.pdf",
        pages=[_page("z" * 400, 1), _page("", 2), _page("", 3), _page("", 4)],
    )
    result = validate_pdf_readability(document)
    assert not result.is_readable


def test_validate_readability_rejects_empty_document():
    result = validate_pdf_readability(ExtractedDocument(filename="empty.pdf", pages=[]))
    assert not result.is_readable
    assert result.total_pages == 0


class _StubExtractor(PDFExtractor):
    def __init__(self, document: ExtractedDocument):
        self._document = document

    def extract(self, data: bytes, filename: str) -> ExtractedDocument:
        return self._document


def test_extract_and_validate_raises_on_unreadable():
    stub = _StubExtractor(
        ExtractedDocument(filename="scan.pdf", pages=[_page("  \x00  ", 1)])
    )
    with pytest.raises(PdfUnreadableError) as excinfo:
        extract_and_validate(b"%PDF-fake", "scan.pdf", extractor=stub)
    assert excinfo.value.readability.is_readable is False


def test_extract_and_validate_cleans_pages():
    stub = _StubExtractor(
        ExtractedDocument(
            filename="ok.pdf",
            pages=[_page("Module A\x00" + "a" * 200, 1), _page("b" * 200, 2)],
        )
    )
    document = extract_and_validate(b"%PDF-fake", "ok.pdf", extractor=stub)
    assert document.total_pages == 2
    assert "\x00" not in document.full_text


def test_real_transcript_pdf_is_readable():
    pytest.importorskip("pypdf")
    if not RESOURCE_PDF.exists():
        pytest.skip("sample transcript PDF not present")

    document = extract_and_validate(RESOURCE_PDF.read_bytes(), RESOURCE_PDF.name)
    assert document.total_pages == 3
    text = document.full_text
    # Spot-check that real content survived extraction + cleaning. Umlauts may be
    # extracted in a decomposed form, so assert on ASCII-safe substrings.
    assert "Telematik" in text
    assert "Masterstudiengang Informatik" in text
    assert "Koch" in text
