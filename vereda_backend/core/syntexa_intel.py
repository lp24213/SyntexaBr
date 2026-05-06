import math
import re
import time
from collections import Counter
from datetime import datetime
from typing import Iterable, Sequence

from sqlalchemy.orm import Session

from vereda_backend.ai_runtime import llm_engine
from vereda_backend.db import models
from vereda_backend.db.models import EMBEDDING_VECTOR_DIM


TOPIC_HINTS = {
    "matematica": ("equacao", "integral", "derivada", "algebra", "matriz", "calculo"),
    "programacao": ("python", "javascript", "codigo", "api", "sql", "bug", "deploy"),
    "negocios": ("empresa", "vendas", "marketing", "mercado", "estrategia", "receita"),
    "educacao": ("professor", "aluno", "escola", "enem", "concurso", "aula"),
    "saude": ("saude", "diagnostico", "sintoma", "tratamento", "medico"),
}


def detect_language(text: str) -> str:
    t = (text or "").strip().lower()
    if not t:
        return "pt-BR"
    pt_markers = ("ção", "você", "porque", "não", "qual", "como")
    en_markers = ("the", "what", "how", "with", "from", "where")
    pt_score = sum(1 for m in pt_markers if m in t)
    en_score = sum(1 for m in en_markers if re.search(rf"\b{m}\b", t))
    if en_score > pt_score:
        return "en-US"
    return "pt-BR"


def detect_subject(text: str) -> str:
    t = (text or "").strip().lower()
    if not t:
        return "geral"
    best = ("geral", 0)
    for subject, keys in TOPIC_HINTS.items():
        score = sum(1 for k in keys if k in t)
        if score > best[1]:
            best = (subject, score)
    return best[0]


def detect_sentiment(text: str) -> str:
    t = (text or "").lower()
    if not t:
        return "neutro"
    positive = ("obrigado", "ótimo", "excelente", "bom", "perfeito")
    negative = ("ruim", "erro", "problema", "lento", "falhou")
    pos = sum(1 for w in positive if w in t)
    neg = sum(1 for w in negative if w in t)
    if pos > neg:
        return "positivo"
    if neg > pos:
        return "negativo"
    return "neutro"


def embed_text(text: str) -> list[float]:
    if not (text or "").strip():
        return []
    try:
        vectors = llm_engine.embed([text], provider="syntexa_native")
        if vectors and isinstance(vectors[0], list):
            return [float(x) for x in vectors[0]]
    except Exception:
        return []
    return []


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    if n <= 0:
        return 0.0
    dot = sum(float(a[i]) * float(b[i]) for i in range(n))
    norm_a = math.sqrt(sum(float(a[i]) ** 2 for i in range(n)))
    norm_b = math.sqrt(sum(float(b[i]) ** 2 for i in range(n)))
    if norm_a <= 0.0 or norm_b <= 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def remember_user_preference(
    db: Session,
    *,
    user_id: int,
    key: str,
    value: str,
    language: str,
    subject: str,
    sentiment: str,
) -> models.MemoryItem:
    emb = embed_text(value)
    item = (
        db.query(models.MemoryItem)
        .filter(models.MemoryItem.user_id == user_id, models.MemoryItem.key == key)
        .first()
    )
    if item is None:
        item = models.MemoryItem(
            user_id=user_id,
            key=key,
            value=value,
            language=language,
            subject=subject,
            sentiment=sentiment,
            source="chat",
            embedding_json=emb,
        )
        if (
            hasattr(item, "embedding_vector")
            and emb
            and len(emb) == EMBEDDING_VECTOR_DIM
        ):
            item.embedding_vector = emb
        db.add(item)
    else:
        item.value = value
        item.language = language
        item.subject = subject
        item.sentiment = sentiment
        item.embedding_json = emb
        if (
            hasattr(item, "embedding_vector")
            and emb
            and len(emb) == EMBEDDING_VECTOR_DIM
        ):
            item.embedding_vector = emb
        item.last_seen_at = datetime.utcnow()
    db.flush()
    return item


def retrieve_semantic_memory(
    db: Session,
    *,
    user_id: int,
    query: str,
    top_k: int = 5,
) -> list[models.MemoryItem]:
    q_emb = embed_text(query)
    if not q_emb:
        return []
    items: Iterable[models.MemoryItem] = (
        db.query(models.MemoryItem)
        .filter(models.MemoryItem.user_id == user_id)
        .order_by(models.MemoryItem.updated_at.desc())
        .limit(300)
        .all()
    )
    ranked: list[tuple[float, models.MemoryItem]] = []
    for item in items:
        emb = item.embedding_json if isinstance(item.embedding_json, list) else []
        score = cosine_similarity(q_emb, emb)
        if score > 0:
            ranked.append((score, item))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return [x[1] for x in ranked[: max(1, top_k)]]


def top_subjects(rows: Iterable[models.Message], limit: int = 10) -> list[tuple[str, int]]:
    c = Counter((r.subject or "geral") for r in rows)
    return c.most_common(limit)


def now_ms() -> float:
    return time.perf_counter() * 1000.0
