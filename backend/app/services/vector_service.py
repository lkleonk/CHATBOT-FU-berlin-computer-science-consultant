import logging
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

from app.settings import settings


logger = logging.getLogger(__name__)


class VectorService:
    """Qdrant-backed vector search for consultant knowledge chunks."""

    def __init__(self):
        self.client = QdrantClient(host=settings.QDRANT.HOST, port=settings.QDRANT.PORT)
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info("Loading embedding model: %s", settings.QDRANT.EMBEDDING_MODEL)
            self._model = SentenceTransformer(settings.QDRANT.EMBEDDING_MODEL)
        return self._model

    def check_connection(self) -> bool:
        try:
            self.client.get_collections()
            return True
        except Exception as exc:
            logger.error("Qdrant connection error: %s", exc)
            return False

    def get_embedding(self, text: str) -> list[float]:
        return self.model.encode(text).tolist()

    def create_collection(self, collection_name: str) -> bool:
        try:
            if self.client.collection_exists(collection_name=collection_name):
                return True
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=settings.QDRANT.VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )
            return True
        except Exception as exc:
            logger.error("Error creating collection %s: %s", collection_name, exc)
            return False

    def delete_collection(self, collection_name: str) -> bool:
        try:
            if self.client.collection_exists(collection_name=collection_name):
                self.client.delete_collection(collection_name=collection_name)
            return True
        except Exception as exc:
            logger.error("Error deleting collection %s: %s", collection_name, exc)
            return False

    def rebuild_collection(self, collection_name: str) -> bool:
        return self.delete_collection(collection_name) and self.create_collection(collection_name)

    def upsert_chunks(self, collection_name: str, chunks: list[dict[str, Any]]) -> bool:
        try:
            points = [
                PointStruct(
                    id=chunk["id"],
                    vector=chunk["vector"],
                    payload=chunk["payload"],
                )
                for chunk in chunks
            ]
            result = self.client.upsert(collection_name=collection_name, points=points)
            return result.status == "completed"
        except Exception as exc:
            logger.error("Error upserting chunks into %s: %s", collection_name, exc)
            return False

    def search(self, collection_name: str, query: str, limit: int) -> list[dict[str, Any]]:
        try:
            vector = self.get_embedding(query)
            results = self.client.query_points(
                collection_name=collection_name,
                query=vector,
                limit=limit,
            ).points
            return [
                {
                    "id": point.id,
                    "score": point.score,
                    "payload": point.payload or {},
                }
                for point in results
            ]
        except Exception as exc:
            logger.error("Vector search failed for %s: %s", collection_name, exc)
            return []
