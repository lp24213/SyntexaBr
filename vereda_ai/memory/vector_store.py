from typing import Any, Dict, List

from vereda_ai.knowledge.vector_db import VectorDB


class InMemoryVectorStore(VectorDB):
    """
    Implementação simples em memória de um "vector store".
    Ideal para desenvolvimento; troque depois por Milvus, Qdrant, etc.
    """

    def __init__(self) -> None:
        self._data: Dict[str, List[Dict[str, Any]]] = {}

    def add_text(
        self,
        namespace: str,
        doc_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._data.setdefault(namespace, []).append(
            {"id": doc_id, "text": text, "metadata": metadata or {}}
        )

    def similarity_search(
        self, namespace: str, query: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        # Heurística tosca: ordena por comprimento de overlap de substrings.
        items = self._data.get(namespace, [])
        scored = []
        for item in items:
            text = item["text"]
            score = len(set(query.split()) & set(text.split()))
            scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [it for _, it in scored[:top_k]]

