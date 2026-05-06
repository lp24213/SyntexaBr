"""Tarefas executadas pelo processo worker ARQ (isoladas da API)."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


async def arq_generate_image(ctx: dict, prompt: str) -> Dict[str, Any]:
    from vereda_backend.services.media_engine import generate_image_from_prompt

    return generate_image_from_prompt(prompt)


async def arq_generate_video(ctx: dict, prompt: str) -> Dict[str, Any]:
    from vereda_backend.services.media_engine import generate_video_from_prompt

    return generate_video_from_prompt(prompt)


async def arq_generate_music(ctx: dict, prompt: str) -> Dict[str, Any]:
    from vereda_backend.services.media_engine import generate_music_from_prompt

    return generate_music_from_prompt(prompt)


async def arq_long_chat(ctx: dict, req_json: str, user_id: Optional[int]) -> str:
    from vereda_backend.db import models
    from vereda_backend.db.session import SessionLocal
    from vereda_backend.schemas.chat import ChatRequest
    from vereda_backend.services.chat_engine import _compute_chat_reply

    req = ChatRequest.model_validate_json(req_json)
    from vereda_backend.services.chat_engine import prepare_chat_request

    db = SessionLocal()
    try:
        user = None
        if user_id is not None:
            user = db.query(models.User).filter(models.User.id == user_id).first()
        req = prepare_chat_request(req, stress_scale=1.0, user=user)
        last_user = next((m for m in reversed(req.messages) if m.role == "user"), None)
        content = (last_user.content or "").strip() if last_user else ""
        return _compute_chat_reply(db, req, user, content)
    finally:
        db.close()


async def arq_build_pdf(ctx: dict, title: str, sections: list, subtitle: Optional[str]) -> bytes:
    from vereda_backend.workers.media_worker import sync_build_pdf

    return sync_build_pdf(title, sections, subtitle)


async def arq_build_xlsx(
    ctx: dict,
    sheet_title: str,
    rows: list,
    header: bool,
    document_title: Optional[str] = None,
) -> bytes:
    from vereda_backend.workers.media_worker import sync_build_xlsx

    return sync_build_xlsx(sheet_title, rows, header, document_title=document_title)


async def arq_gov_report(ctx: dict, req_messages_json: str, user_id: int) -> str:
    """Gera texto do relatório (mesma lógica que o endpoint, sem passar pelo cache de chat duas vezes)."""
    from vereda_backend.db import models
    from vereda_backend.db.session import SessionLocal
    from vereda_backend.schemas.chat import ChatRequest
    from vereda_backend.services.chat_engine import _compute_chat_reply

    req = ChatRequest.model_validate_json(req_messages_json)
    from vereda_backend.services.chat_engine import prepare_chat_request

    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise RuntimeError("usuário não encontrado")
        req = prepare_chat_request(req, stress_scale=1.0, user=user)
        last_user = next((m for m in reversed(req.messages) if m.role == "user"), None)
        content = (last_user.content or "").strip() if last_user else ""
        return _compute_chat_reply(db, req, user, content)
    finally:
        db.close()
