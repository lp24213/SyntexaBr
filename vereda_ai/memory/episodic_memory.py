from typing import Any, List

from vereda_ai.memory.vector_store import InMemoryVectorStore


class EpisodicMemory:
    """
    Memória episódica: experiências, sessões de uso, execuções de agentes.
    """

    def __init__(self, store: InMemoryVectorStore | None = None) -> None:
        self.store = store or InMemoryVectorStore()

    def add_episode(self, episode_id: str, text: str, metadata: dict[str, Any]) -> None:
        self.store.add_text(
            namespace="episodes",
            doc_id=episode_id,
            text=text,
            metadata=metadata,
        )

    def recall(self, query: str, top_k: int = 5) -> List[dict[str, Any]]:
        return self.store.similarity_search(
            namespace="episodes", query=query, top_k=top_k
        )

