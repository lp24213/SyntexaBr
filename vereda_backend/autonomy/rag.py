from dataclasses import dataclass


@dataclass
class RagHit:
    source_id: str
    score: float
    text: str


def retrieve(query: str, top_k: int = 5) -> list[RagHit]:
    """RAG global in-process (`rag_engine` + embeddings open-source no vector store)."""
    try:
        from vereda_backend.ai_runtime import rag_engine

        docs = rag_engine.db.similarity_search(
            namespace="global", query=query, top_k=max(1, top_k)
        )
        out: list[RagHit] = []
        for d in docs:
            meta = d.get("metadata") if isinstance(d.get("metadata"), dict) else {}
            src = str(d.get("source") or meta.get("source") or "indexed")
            out.append(
                RagHit(
                    source_id=src,
                    score=float(d.get("score", 0.0)),
                    text=str(d.get("text", "")),
                )
            )
        return out
    except Exception:
        return []
