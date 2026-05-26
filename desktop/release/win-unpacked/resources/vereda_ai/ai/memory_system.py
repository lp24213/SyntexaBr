from typing import Any

from vereda_ai.knowledge.vector_db import VectorDB
from vereda_ai.core.logging import get_logger


logger = get_logger(__name__)


class MemorySystem:
    """
    Memória de longo prazo + contexto conversacional via VectorDB.
    """

    def __init__(self, db: VectorDB):
        self.db = db

    def store_turn(self, conv_id: str, role: str, content: str) -> None:
        logger.info("Armazenando turno de conversa em memória vetorial")
        self.db.add_text(
            namespace="conversations",
            doc_id=f"{conv_id}:{role}",
            text=content,
            metadata={"role": role},
        )

    def retrieve_context(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        return self.db.similarity_search(
            namespace="conversations", query=query, top_k=top_k
        )

