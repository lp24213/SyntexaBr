"""
Fila ARQ (Redis) para tarefas pesadas. Sem Redis, as funções abaixo levantam RuntimeError
e o chamador deve usar o caminho síncrono (comportamento atual).
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

from vereda_backend.core.config import settings

logger = logging.getLogger(__name__)

_pool = None


async def _get_pool():
    global _pool
    if _pool is not None:
        return _pool
    url = (getattr(settings, "redis_url", None) or "").strip()
    if not url:
        raise RuntimeError("REDIS_URL não configurada")
    from arq import create_pool
    from arq.connections import RedisSettings

    _pool = await create_pool(RedisSettings.from_dsn(url))
    return _pool


def _run_coro(coro):
    """Executa corrotina a partir de endpoint síncrono (novo loop isolado)."""
    return asyncio.run(coro)


async def enqueue_image_generation(prompt: str) -> Dict[str, Any]:
    pool = await _get_pool()
    job = await pool.enqueue_job("arq_generate_image", prompt)
    return await job.result(timeout=360)


async def enqueue_gov_report(req_messages_json: str, user_id: int) -> str:
    pool = await _get_pool()
    job = await pool.enqueue_job("arq_gov_report", req_messages_json, user_id)
    return await job.result(timeout=600)


async def enqueue_long_chat(req_json: str, user_id: Optional[int]) -> str:
    pool = await _get_pool()
    job = await pool.enqueue_job("arq_long_chat", req_json, user_id)
    return await job.result(timeout=600)


def job_queue_enabled() -> bool:
    return bool((getattr(settings, "redis_url", None) or "").strip())


def run_image_job_sync(prompt: str) -> Dict[str, Any]:
    if not job_queue_enabled():
        from vereda_backend.services.media_engine import generate_image_from_prompt

        return generate_image_from_prompt(prompt)
    try:
        return _run_coro(enqueue_image_generation(prompt))
    except Exception as exc:
        logger.warning("Fila imagem falhou, fallback síncrono: %s", exc)
        from vereda_backend.services.media_engine import generate_image_from_prompt

        return generate_image_from_prompt(prompt)


def run_gov_report_sync(req_messages_json: str, user_id: int) -> str:
    if not job_queue_enabled():
        raise RuntimeError("queue_disabled")
    return _run_coro(enqueue_gov_report(req_messages_json, user_id))


def run_long_chat_sync(req_json: str, user_id: Optional[int]) -> str:
    if not job_queue_enabled():
        raise RuntimeError("queue_disabled")
    return _run_coro(enqueue_long_chat(req_json, user_id))
