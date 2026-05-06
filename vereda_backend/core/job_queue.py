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


async def enqueue_video_generation(prompt: str) -> Dict[str, Any]:
    pool = await _get_pool()
    job = await pool.enqueue_job("arq_generate_video", prompt)
    timeout = int(getattr(settings, "media_queue_video_timeout_sec", 900) or 900)
    return await job.result(timeout=max(120, timeout))


async def enqueue_music_generation(prompt: str) -> Dict[str, Any]:
    pool = await _get_pool()
    job = await pool.enqueue_job("arq_generate_music", prompt)
    timeout = int(getattr(settings, "media_queue_music_timeout_sec", 900) or 900)
    return await job.result(timeout=max(120, timeout))


async def enqueue_media_generation_job_id(
    kind: str, prompt: str, defer_by: float | None = None
) -> str:
    pool = await _get_pool()
    fn_map = {
        "image": "arq_generate_image",
        "video": "arq_generate_video",
        "music": "arq_generate_music",
    }
    fn = fn_map.get((kind or "").strip().lower())
    if not fn:
        raise RuntimeError(f"media_kind_unsupported:{kind}")
    enqueue_kw: Dict[str, Any] = {}
    if defer_by is not None and float(defer_by) > 0:
        enqueue_kw["_defer_by"] = float(defer_by)
    job = await pool.enqueue_job(fn, prompt, **enqueue_kw)
    return str(job.job_id)


async def inspect_job(job_id: str) -> Dict[str, Any]:
    pool = await _get_pool()
    from arq.jobs import Job

    j = Job(job_id, pool)
    status = await j.status()
    status_name = str(getattr(status, "name", str(status)) or "").lower()
    out: Dict[str, Any] = {"job_id": job_id, "state": status_name}
    if status_name in {"complete", "completed"}:
        try:
            out["result"] = await j.result(timeout=1)
        except Exception:
            out["result"] = None
    return out


async def abort_media_generation_job(job_id: str) -> Dict[str, Any]:
    """Cancela job na fila ARQ (requer worker com allow_abort_jobs)."""
    from arq.jobs import Job, JobStatus

    pool = await _get_pool()
    jid = (job_id or "").strip()
    if not jid:
        return {"ok": False, "error": "invalid_id", "state": None}
    j = Job(jid, pool)
    st = await j.status()
    state = st.value if isinstance(st, JobStatus) else str(st).lower()
    if st == JobStatus.not_found:
        return {"ok": False, "error": "not_found", "state": state}
    if st == JobStatus.complete:
        return {"ok": False, "error": "already_complete", "state": state}
    try:
        aborted = await asyncio.wait_for(j.abort(), timeout=20.0)
    except asyncio.TimeoutError:
        return {"ok": True, "error": None, "state": "abort_pending"}
    if aborted:
        return {"ok": True, "error": None, "state": "cancelled"}
    st2 = await j.status()
    state2 = st2.value if isinstance(st2, JobStatus) else str(st2).lower()
    if st2 == JobStatus.complete:
        return {"ok": False, "error": "already_complete", "state": state2}
    return {"ok": False, "error": "abort_failed", "state": state2}


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


def _after_image_ok(result: Dict[str, Any], prompt: str) -> None:
    if not isinstance(result, dict) or not result.get("ok"):
        return
    try:
        from vereda_backend.core.azure_media import publish_image_job_result

        publish_image_job_result(result, prompt)
    except Exception:
        logger.debug("publicação Azure pós-imagem ignorada", exc_info=True)


def run_image_job_sync(prompt: str) -> Dict[str, Any]:
    if not job_queue_enabled():
        from vereda_backend.services.media_engine import generate_image_from_prompt

        out = generate_image_from_prompt(prompt)
        _after_image_ok(out, prompt)
        return out
    try:
        out = _run_coro(enqueue_image_generation(prompt))
        _after_image_ok(out, prompt)
        return out
    except Exception as exc:
        logger.warning("Fila imagem falhou; nova tentativa síncrona (mesmo provedor): %s", exc)
        from vereda_backend.services.media_engine import generate_image_from_prompt

        out = generate_image_from_prompt(prompt)
        _after_image_ok(out, prompt)
        return out


def run_video_job_sync(prompt: str) -> Dict[str, Any]:
    from vereda_backend.services.media_engine import generate_video_from_prompt

    if not job_queue_enabled() or not bool(getattr(settings, "media_queue_video_enabled", True)):
        return generate_video_from_prompt(prompt)
    try:
        return _run_coro(enqueue_video_generation(prompt))
    except Exception as exc:
        logger.warning("Fila vídeo falhou; fallback síncrono: %s", exc)
        return generate_video_from_prompt(prompt)


def run_music_job_sync(prompt: str) -> Dict[str, Any]:
    from vereda_backend.services.media_engine import generate_music_from_prompt

    if not job_queue_enabled() or not bool(getattr(settings, "media_queue_music_enabled", True)):
        return generate_music_from_prompt(prompt)
    try:
        return _run_coro(enqueue_music_generation(prompt))
    except Exception as exc:
        logger.warning("Fila música falhou; fallback síncrono: %s", exc)
        return generate_music_from_prompt(prompt)


def enqueue_media_job_id_sync(
    kind: str, prompt: str, defer_by: float | None = None
) -> str:
    if not job_queue_enabled():
        raise RuntimeError("queue_disabled")
    return _run_coro(enqueue_media_generation_job_id(kind, prompt, defer_by=defer_by))


def abort_media_job_sync(job_id: str) -> Dict[str, Any]:
    if not job_queue_enabled():
        raise RuntimeError("queue_disabled")
    return _run_coro(abort_media_generation_job(job_id))


def inspect_job_sync(job_id: str) -> Dict[str, Any]:
    if not job_queue_enabled():
        raise RuntimeError("queue_disabled")
    return _run_coro(inspect_job(job_id))


def run_gov_report_sync(req_messages_json: str, user_id: int) -> str:
    if not job_queue_enabled():
        raise RuntimeError("queue_disabled")
    return _run_coro(enqueue_gov_report(req_messages_json, user_id))


def run_long_chat_sync(req_json: str, user_id: Optional[int]) -> str:
    if not job_queue_enabled():
        raise RuntimeError("queue_disabled")
    return _run_coro(enqueue_long_chat(req_json, user_id))
