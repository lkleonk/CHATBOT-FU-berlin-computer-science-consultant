from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from app.pdf.clean import clean_pdf_text


@dataclass(frozen=True)
class ExtractedPdfPage:
    page_number: int
    text: str


def extract_pdf_pages(path: Path) -> list[ExtractedPdfPage]:
    reader = PdfReader(str(path))
    pages: list[ExtractedPdfPage] = []
    for index, page in enumerate(reader.pages, start=1):
        text = clean_pdf_text(page.extract_text() or "")
        if text:
            pages.append(ExtractedPdfPage(page_number=index, text=text))
    return pages


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Extract text from a PDF resource.")
    parser.add_argument("pdf_path", type=Path)
    args = parser.parse_args()

    for page in extract_pdf_pages(args.pdf_path):
        print(f"\n--- page {page.page_number} ---\n")
        print(page.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
