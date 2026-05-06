# -*- coding: utf-8 -*-
"""Orçamento aproximado de contexto (estilo janela longa): corta do início preservando o fim."""
from __future__ import annotations

from typing import List, Optional

from vereda_backend.core.config import settings
from vereda_backend.db import models
from vereda_backend.schemas.chat import ChatMessage


def approx_tokens_for_message(msg: ChatMessage, *, chars_per_token: float) -> int:
    try:
        return max(2, int(len(msg.model_dump_json()) / max(1.5, chars_per_token)))
    except Exception:
        raw = msg.content or ""
        return max(2, int(len(raw) / max(1.5, chars_per_token)))


def context_token_budget_for_user(user: Optional[models.User]) -> int:
    if user and bool(getattr(user, "is_admin", False)):
        return max(2048, int(getattr(settings, "chat_context_approx_tokens_admin", 22000) or 22000))
    if user:
        return max(2048, int(getattr(settings, "chat_context_approx_tokens_auth", 14000) or 14000))
    return max(2048, int(getattr(settings, "chat_context_approx_tokens_public", 8000) or 8000))


def trim_chat_messages_by_approx_tokens(
    messages: List[ChatMessage],
    budget_tokens: int,
    *,
    chars_per_token: float | None = None,
) -> List[ChatMessage]:
    if not messages or budget_tokens <= 0:
        return messages
    cpt = float(
        chars_per_token
        if chars_per_token is not None
        else float(getattr(settings, "chat_approx_chars_per_token", 4.0) or 4.0)
    )
    cpt = max(2.0, cpt)
    total = sum(approx_tokens_for_message(m, chars_per_token=cpt) for m in messages)
    if total <= budget_tokens:
        return messages
    drop = 0
    while drop < len(messages) - 1 and total > budget_tokens:
        total -= approx_tokens_for_message(messages[drop], chars_per_token=cpt)
        drop += 1
    return messages[drop:]
