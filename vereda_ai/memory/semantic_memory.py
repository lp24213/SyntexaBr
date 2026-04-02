from typing import Any, List

from vereda_ai.memory.vector_store import InMemoryVectorStore


class SemanticMemory:
    """
    Memória semântica: conceitos, fatos científicos, documentação técnica.
    """

    def __init__(self, store: InMemoryVectorStore | None = None) -> None:
        self.store = store or InMemoryVectorStore()

    def add_fact(self, fact_id: str, text: str, metadata: dict[str, Any]) -> None:
        self.store.add_text(
            namespace="semantic",
            doc_id=fact_id,
            text=text,
            metadata=metadata,
        )

    def recall(self, query: str, top_k: int = 5) -> List[dict[str, Any]]:
        return self.store.similarity_search(
            namespace="semantic", query=query, top_k=top_k
        )

