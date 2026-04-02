from abc import ABC, abstractmethod
from typing import Any, List


class VectorDB(ABC):
    """
    Interface abstrata para banco vetorial (FAISS, Chroma, etc.).
    """

    @abstractmethod
    def add_text(
        self,
        namespace: str,
        doc_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        ...

    @abstractmethod
    def similarity_search(
        self, namespace: str, query: str, top_k: int = 5
    ) -> List[dict[str, Any]]:
        ...

