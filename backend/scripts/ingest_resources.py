import argparse
import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_ROOT.parent if (BACKEND_ROOT.parent / "ressources").exists() else BACKEND_ROOT
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.resource_loader import (  # noqa: E402
    TextChunk,
    chunk_text,
    content_hash,
    detect_title,
    load_text_resource,
)
from app.services.vector_service import VectorService  # noqa: E402
from app.settings import settings  # noqa: E402
from scripts.extract_pdf import extract_pdf_pages  # noqa: E402


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("ingest_resources")

CHUNK_NAMESPACE = uuid.UUID("11793f0f-3f2b-4f1d-9c91-3f6b5d65f44f")
GENERATED_ROOT = BACKEND_ROOT / "knowledge_base" / "generated"

# Degree-rule sources (Informatik_Master_Ablauf.txt, Checkliste PDF, degree_rules.md)
# live in the system prompt now (see app.domain.degrees.msc_informatik.prompts). Only module-level
# lookups still need RAG.
INGEST_FILENAMES = {"module_catalog.md"}


def chunk_id_for(source_path: Path, position: int, chunk: TextChunk) -> str:
    name = f"{source_path.as_posix()}::{position}::{chunk.page or ''}::{chunk.section_heading or ''}"
    return str(uuid.uuid5(CHUNK_NAMESPACE, name))


def iter_source_files(include_generated: bool) -> list[Path]:
    roots = [settings.RAG.RESOURCES_DIR]
    if include_generated:
        roots.append(GENERATED_ROOT)

    files: list[Path] = []
    for root in roots:
        if not root.exists():
            logger.warning("Source root does not exist: %s", root)
            continue
        for path in sorted(root.rglob("*")):
            if path.suffix.lower() not in {".txt", ".pdf", ".md"}:
                continue
            if path.name not in INGEST_FILENAMES:
                logger.info("Skipping %s (covered by system prompt)", path.name)
                continue
            files.append(path)
    return files


def chunks_for_file(path: Path) -> tuple[str, list[TextChunk]]:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return load_text_resource(path)
    if suffix == ".pdf":
        pages = extract_pdf_pages(path)
        if not pages:
            return path.stem, []
        title = detect_title(path, pages[0].text)
        chunks: list[TextChunk] = []
        for page in pages:
            chunks.extend(chunk_text(page.text, default_heading=title, page=page.page_number))
        return title, chunks
    return path.stem, []


def build_payloads(include_generated: bool) -> list[dict]:
    ingested_at = datetime.now(timezone.utc).isoformat()
    payloads: list[dict] = []

    for source_file in iter_source_files(include_generated=include_generated):
        title, chunks = chunks_for_file(source_file)
        logger.info("Built %d chunks from %s", len(chunks), source_file)
        for position, chunk in enumerate(chunks):
            try:
                source_path = source_file.relative_to(PROJECT_ROOT)
            except ValueError:
                source_path = source_file
            payloads.append(
                {
                    "id": chunk_id_for(source_path, position, chunk),
                    "_embed_text": f"{title}\n{chunk.section_heading or ''}\n\n{chunk.content}",
                    "payload": {
                        "title": title,
                        "source": source_file.name,
                        "source_path": source_path.as_posix(),
                        "section_heading": chunk.section_heading,
                        "page": chunk.page,
                        "position": position,
                        "content": chunk.content,
                        "content_hash": content_hash(chunk.content),
                        "embedding_model": settings.QDRANT.EMBEDDING_MODEL,
                        "ingested_at": ingested_at,
                    },
                }
            )
    return payloads


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild the consultant RAG collection from local resources.")
    parser.add_argument(
        "--collection",
        default=settings.QDRANT.COLLECTION,
        help="Qdrant collection to rebuild.",
    )
    parser.add_argument(
        "--skip-generated",
        action="store_true",
        help="Only ingest original files under ressources/.",
    )
    args = parser.parse_args()

    payloads = build_payloads(include_generated=not args.skip_generated)
    if not payloads:
        logger.error("No chunks built. Refusing to rebuild collection.")
        return 1

    vector_service = VectorService()
    if not vector_service.rebuild_collection(args.collection):
        logger.error("Failed to rebuild collection %s", args.collection)
        return 1

    points = []
    for item in payloads:
        vector = vector_service.get_embedding(item["_embed_text"])
        points.append(
            {
                "id": item["id"],
                "vector": vector,
                "payload": item["payload"],
            }
        )

    if not vector_service.upsert_chunks(args.collection, points):
        logger.error("Upsert failed.")
        return 1

    logger.info("Ingested %d chunks into %s", len(points), args.collection)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
