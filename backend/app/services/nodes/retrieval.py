import logging

from app.services.states.consultant_state import ConsultantState
from app.services.vector_service import VectorService
from app.settings import settings


logger = logging.getLogger(__name__)


def _format_hit(hit: dict) -> str:
    payload = hit.get("payload") or {}
    title = payload.get("title") or payload.get("source") or "source"
    section = payload.get("section_heading")
    page = payload.get("page")
    header_parts = [str(title)]
    if section:
        header_parts.append(str(section))
    if page:
        header_parts.append(f"page {page}")
    return f"## {' - '.join(header_parts)}\n{payload.get('content', '')}".strip()


async def retrieval_node(state: ConsultantState) -> ConsultantState:
    logger.info("Retrieval node invoked")
    query = (state.get("retrieval_query") or "").strip()
    if not query:
        return {"retrieved_context": "", "citations": []}

    hits = VectorService().search(
        collection_name=settings.QDRANT.COLLECTION,
        query=query,
        limit=settings.RAG.RETRIEVAL_LIMIT,
    )
    surviving = [hit for hit in hits if (hit.get("score") or 0.0) >= settings.RAG.SCORE_THRESHOLD]

    if surviving:
        logger.info("Retrieval returned %d chunk(s) above threshold:", len(surviving))
        for idx, hit in enumerate(surviving, start=1):
            payload = hit.get("payload") or {}
            title = payload.get("title") or payload.get("source") or "source"
            parts = [str(title)]
            if payload.get("section_heading"):
                parts.append(str(payload["section_heading"]))
            if payload.get("page"):
                parts.append(f"p.{payload['page']}")
            logger.info("  [%d] %.2f  %s", idx, hit.get("score") or 0.0, " · ".join(parts))
    else:
        logger.info("Retrieval returned no chunks above threshold %.2f", settings.RAG.SCORE_THRESHOLD)

    citations = []
    context_parts = []
    for hit in surviving:
        payload = hit.get("payload") or {}
        context_parts.append(_format_hit(hit))
        citations.append(
            {
                "source": payload.get("source") or payload.get("source_path") or "unknown",
                "title": payload.get("title"),
                "section_heading": payload.get("section_heading"),
                "page": payload.get("page"),
                "score": hit.get("score"),
            }
        )

    return {
        "retrieved_context": "\n\n".join(part for part in context_parts if part),
        "citations": citations,
    }
