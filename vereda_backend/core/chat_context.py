# -*- coding: utf-8 -*-
"""Contexto por requisição de chat (sessão legada, conversa v2) para auditoria e compliance."""
from __future__ import annotations

from contextvars import ContextVar
from typing import Any

_chat_ctx: ContextVar[dict[str, Any]] = ContextVar("syntexa_chat_ctx", default={})


def get_chat_request_context() -> dict[str, Any]:
    return dict(_chat_ctx.get() or {})


def set_chat_request_context(
    *,
    session_id: int | None = None,
    v2_conversation_id: int | None = None,
    client_ip: str | None = None,
) -> Any:
    """Retorna token para reset()."""
    payload: dict[str, Any] = {}
    if session_id is not None:
        payload["session_id"] = int(session_id)
    if v2_conversation_id is not None:
        payload["v2_conversation_id"] = int(v2_conversation_id)
    if client_ip:
        payload["client_ip"] = str(client_ip)[:128]
    return _chat_ctx.set(payload)


def reset_chat_request_context(token: Any) -> None:
    _chat_ctx.reset(token)
