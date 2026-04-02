# -*- coding: utf-8 -*-
"""
POST /v1/chat: fluxo modular Router -> Agent -> Tools -> Resposta.
Body: { "message": "..." } ou { "messages": [...] }. Retorna { "response": "...", "category": "..." }.
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from vereda_backend.ai_runtime import chat_history_db, modular_engine
from vereda_backend.core.security import get_current_user_optional
from vereda_backend.db import models
from vereda_backend.db.session import get_db
from vereda_backend.ai_runtime import memory_system, rag_engine
from vereda_ai.router.prompt_router import PromptRouter, RouteCategory
from vereda_backend.services.chat_engine import (
    _is_longest_word_question,
    _longest_word_response_text,
)


router = APIRouter()


class ChatMessageIn(BaseModel):
    role: str = "user"
    content: str


class ModularChatRequest(BaseModel):
    message: Optional[str] = None
    messages: Optional[List[ChatMessageIn]] = None
    user_id: Optional[str] = None
    use_cache: bool = True


class ModularChatResponse(BaseModel):
    response: str
    category: str


def _last_user_content(req: ModularChatRequest) -> str:
    if req.message:
        return req.message.strip()
    if req.messages:
        for m in reversed(req.messages):
            if m.role == "user":
                return (m.content or "").strip()
    return ""


@router.post("/chat", response_model=ModularChatResponse)
async def modular_chat(
    body: ModularChatRequest,
    current_user: Optional[models.User] = Depends(get_current_user_optional),
    db = Depends(get_db),
) -> ModularChatResponse:
    """
    Chat modular: prompt -> Router -> Agent -> Tools -> Resposta.
    """
    prompt = _last_user_content(body)
    if not prompt:
        return ModularChatResponse(response="Envie uma mensagem.", category="general")

    if _is_longest_word_question(prompt):
        return ModularChatResponse(
            response=_longest_word_response_text(),
            category=RouteCategory.KNOWLEDGE.value,
        )

    # Segurança: nunca aceitar user_id vindo do cliente para evitar IDOR.
    user_id = str(current_user.id) if current_user else "anon"
    history: List[dict] = []
    try:
        recent = chat_history_db.get_recent(user_id, limit=6)
        history = [{"role": r["role"], "content": r["message"]} for r in recent]
    except Exception:
        pass

    knowledge_snippets: List[str] = []
    memory_snippets: List[str] = []
    try:
        if rag_engine and hasattr(rag_engine, "db"):
            docs = rag_engine.db.similarity_search(namespace="global", query=prompt, top_k=3)
            knowledge_snippets = [d.get("text", "") for d in docs if d.get("text")]
        mem = memory_system.retrieve_context(prompt, top_k=2)
        memory_snippets = [m.get("text", "") for m in mem if m.get("text")]
    except Exception:
        pass

    category = PromptRouter().route(prompt)
    response = modular_engine.process(
        prompt=prompt,
        user_id=user_id,
        history=history,
        knowledge_snippets=knowledge_snippets,
        memory_snippets=memory_snippets,
        use_cache=body.use_cache,
    )

    try:
        chat_history_db.add(user_id, prompt, "user")
        chat_history_db.add(user_id, response, "assistant")
    except Exception:
        pass

    return ModularChatResponse(response=response, category=category.value)
