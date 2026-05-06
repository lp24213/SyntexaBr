from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from vereda_backend.core.syntexa_intel import (
    detect_language,
    detect_sentiment,
    detect_subject,
    embed_text,
    retrieve_semantic_memory,
)
from vereda_backend.db import models
from vereda_backend.db.models import EMBEDDING_VECTOR_DIM


def ensure_v2_session(
    db: Session,
    *,
    user_id: Optional[int],
    is_anonymous: bool,
    language: str,
    source: str = "chat-api",
) -> models.Session:
    session = models.Session(
        user_id=user_id,
        channel="web",
        source=source,
        language=language or "pt-BR",
        is_anonymous=is_anonymous,
    )
    db.add(session)
    db.flush()
    return session


def ensure_conversation(
    db: Session,
    *,
    session_id: int,
    user_id: Optional[int],
    title: str,
    language: str,
    subject: str,
    sentiment: str,
) -> models.Conversation:
    c = models.Conversation(
        session_id=session_id,
        user_id=user_id,
        title=(title or "Nova conversa")[:512],
        detected_language=language,
        detected_subject=subject,
        detected_sentiment=sentiment,
        status="active",
        started_at=datetime.utcnow(),
    )
    db.add(c)
    db.flush()
    return c


def persist_input_message_batch(
    db: Session,
    *,
    conversation_id: int,
    user_id: Optional[int],
    messages: list,
) -> None:
    for m in messages:
        content = (m.content or "").strip()
        lang = detect_language(content)
        subject = detect_subject(content)
        sentiment = detect_sentiment(content)
        emb = embed_text(content)
        msg = models.Message(
            conversation_id=conversation_id,
            user_id=user_id,
            role=m.role,
            content=content,
            language=lang,
            subject=subject,
            sentiment=sentiment,
            embedding_json=emb,
        )
        if (
            hasattr(msg, "embedding_vector")
            and emb
            and len(emb) == EMBEDDING_VECTOR_DIM
        ):
            msg.embedding_vector = emb
        db.add(msg)


def persist_assistant_output(
    db: Session,
    *,
    conversation_id: int,
    user_id: Optional[int],
    content: str,
    model_used: str,
    provider: str,
    prompt_tokens: Optional[int],
    completion_tokens: Optional[int],
    total_tokens: Optional[int],
    latency_ms: Optional[float],
) -> models.Message:
    lang = detect_language(content)
    subject = detect_subject(content)
    sentiment = detect_sentiment(content)
    msg = models.Message(
        conversation_id=conversation_id,
        user_id=user_id,
        role="assistant",
        content=content,
        language=lang,
        subject=subject,
        sentiment=sentiment,
        model_used=model_used,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        latency_ms=latency_ms,
        embedding_json=embed_text(content),
    )
    emb_out = msg.embedding_json if isinstance(msg.embedding_json, list) else []
    if (
        hasattr(msg, "embedding_vector")
        and emb_out
        and len(emb_out) == EMBEDDING_VECTOR_DIM
    ):
        msg.embedding_vector = emb_out
    db.add(msg)
    db.flush()
    run = models.ModelRun(
        conversation_id=conversation_id,
        message_id=msg.id,
        provider=provider,
        model_name=model_used,
        status="success",
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        latency_ms=latency_ms,
        estimated_cost_usd=None,
    )
    db.add(run)
    return msg


def semantic_context_for_user(db: Session, *, user_id: int, query: str, top_k: int = 3) -> list[str]:
    items = retrieve_semantic_memory(db, user_id=user_id, query=query, top_k=top_k)
    return [f"{i.key}: {i.value}" for i in items]
