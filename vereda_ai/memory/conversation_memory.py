from typing import Any, List

from vereda_ai.memory.vector_store import InMemoryVectorStore


class ConversationMemory:
    """
    Memória de conversação baseada em vector store.
    """

    def __init__(self, store: InMemoryVectorStore | None = None) -> None:
        self.store = store or InMemoryVectorStore()

    def add_turn(self, conversation_id: str, role: str, content: str) -> None:
        self.store.add_text(
            namespace="conversations",
            doc_id=f"{conversation_id}:{role}",
            text=content,
            metadata={"role": role},
        )

    def recall(self, query: str, top_k: int = 5) -> List[dict[str, Any]]:
        return self.store.similarity_search(
            namespace="conversations", query=query, top_k=top_k
        )

