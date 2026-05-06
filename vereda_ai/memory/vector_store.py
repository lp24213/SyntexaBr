import math
from typing import Any, Callable, Dict, List, Optional

from vereda_ai.knowledge.vector_db import VectorDB


def _cosine_vec(a: List[float], b: List[float]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    if n <= 0:
        return 0.0
    dot = sum(float(a[i]) * float(b[i]) for i in range(n))
    na = math.sqrt(sum(float(a[i]) ** 2 for i in range(n)))
    nb = math.sqrt(sum(float(b[i]) ** 2 for i in range(n)))
    if na <= 0.0 or nb <= 0.0:
        return 0.0
    return dot / (na * nb)


class InMemoryVectorStore(VectorDB):
    """
    Vector store em RAM: com `embed_batch_fn` usa similaridade coseno (open-source);
    sem função, mantém heurística de overlap de tokens (legado).
    """

    def __init__(
        self,
        embed_batch_fn: Optional[Callable[[List[str]], List[List[float]]]] = None,
    ) -> None:
        self._data: Dict[str, List[Dict[str, Any]]] = {}
        self._embed_batch_fn = embed_batch_fn

    def add_text(
        self,
        namespace: str,
        doc_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        emb: List[float] | None = None
        if self._embed_batch_fn and (text or "").strip():
            try:
                batch = self._embed_batch_fn([text])
                if batch and batch[0]:
                    emb = [float(x) for x in batch[0]]
            except Exception:
                emb = None
        self._data.setdefault(namespace, []).append(
            {
                "id": doc_id,
                "text": text,
                "metadata": metadata or {},
                "embedding": emb,
            }
        )

    def similarity_search(
        self, namespace: str, query: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        items = self._data.get(namespace, [])
        if not items:
            return []
        q = (query or "").strip()
        use_emb = self._embed_batch_fn is not None and any(
            isinstance(it.get("embedding"), list) and it["embedding"] for it in items
        )
        if use_emb and q:
            try:
                qv = self._embed_batch_fn([q])
                if not qv or not qv[0]:
                    use_emb = False
                else:
                    qemb = [float(x) for x in qv[0]]
                    scored: List[tuple[float, Dict[str, Any]]] = []
                    for item in items:
                        e = item.get("embedding")
                        if not isinstance(e, list) or not e:
                            continue
                        scored.append((_cosine_vec(qemb, e), item))
                    scored.sort(key=lambda x: x[0], reverse=True)
                    out: List[Dict[str, Any]] = []
                    for score, item in scored[:top_k]:
                        meta = item.get("metadata") or {}
                        out.append(
                            {
                                "text": item["text"],
                                "source": meta.get("source", "indexed"),
                                "score": float(score),
                                **meta,
                            }
                        )
                    if out:
                        return out
            except Exception:
                use_emb = False
        # Legado: overlap de tokens
        scored2: List[tuple[int, Dict[str, Any]]] = []
        for item in items:
            text = item["text"]
            score = len(set(q.split()) & set(str(text).split()))
            scored2.append((score, item))
        scored2.sort(key=lambda x: x[0], reverse=True)
        return [it for _, it in scored2[:top_k]]

