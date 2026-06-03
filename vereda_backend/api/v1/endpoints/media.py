import hashlib
import json
import logging
import time
from typing import Any, Dict

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse

from vereda_backend.core.plan_limits import (
    count_media_usage_this_month,
    get_effective_plan,
    get_media_limit,
)
from vereda_backend.services.media_engine import (
    analyze_video_basic,
    fetch_whitelisted_image_url_to_base64,
    generate_tts_from_text,
)
from vereda_backend.core.job_queue import (
    abort_media_job_sync,
    enqueue_media_job_id_sync,
    inspect_job_sync,
    job_queue_enabled,
    run_image_job_sync,
    run_music_job_sync,
    run_video_job_sync,
)
from vereda_backend.core.redis_app import get_redis
from vereda_backend.core.rate_limit import get_client_ip
from vereda_backend.core.security import get_current_user, get_current_user_optional
from vereda_backend.core.subscription import require_subscription
from vereda_backend.db import models
from vereda_backend.db.session import get_db
from vereda_backend.core.public_messages import MSG_TRY_AGAIN_PT
from vereda_backend.cache.media_cache import cache_key, get_cached, set_cached
from vereda_backend.core.config import settings


router = APIRouter(prefix="/media")
_log = logging.getLogger(__name__)

_MEDIA_RL_PREFIX = "syntexa:media:async:rl:v2:"
_MEDIA_IDEMP_PREFIX = "syntexa:media:idemp:v1:"
_MEDIA_JOBCTX_PREFIX = "syntexa:media:jobctx:v1:"


def _assert_media_limit(
    db,
    request: Request,
    media_kind: str,
    current_user: models.User | None,
) -> None:
    user_plan = getattr(current_user, "subscription_plan", None) if current_user else None
    plan = get_effective_plan(user_plan)
    limit = get_media_limit(plan, media_kind)
    if limit is None:
        return
    ip = get_client_ip(request) if request else "unknown"
    used = count_media_usage_this_month(
        db,
        media_kind=media_kind,
        user_id=(current_user.id if current_user else None),
        ip_address=ip,
    )
    if used >= limit:
        who = "IP atual" if not current_user else "sua conta"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Limite mensal de {media_kind} atingido para o plano '{plan}' "
                f"({used}/{limit}) em {who}. Faça upgrade para continuar."
            ),
        )


def _register_media_usage(
    db,
    request: Request,
    media_kind: str,
    current_user: models.User | None,
) -> None:
    ip = get_client_ip(request) if request else "unknown"
    db.add(
        models.AuditLog(
            action=f"media_generate_{media_kind}",
            user_id=(current_user.id if current_user else None),
            resource="/v1/media",
            detail=f"{media_kind} generation",
            ip_address=ip,
        )
    )
    db.commit()


def _media_generation_cache_get(kind: str, prompt: str) -> Dict[str, Any] | None:
    if not bool(getattr(settings, "media_generation_cache_enabled", True)):
        return None
    p = (prompt or "").strip()
    if len(p) < 3:
        return None
    key = cache_key(f"gen-{kind}", p.encode("utf-8"), extra="v1")
    hit = get_cached(key)
    if isinstance(hit, dict) and hit.get("ok"):
        return hit
    return None


def _media_generation_cache_set(kind: str, prompt: str, result: Dict[str, Any]) -> None:
    if not bool(getattr(settings, "media_generation_cache_enabled", True)):
        return
    if not isinstance(result, dict) or not result.get("ok"):
        return
    p = (prompt or "").strip()
    if len(p) < 3:
        return
    ttl = int(getattr(settings, "media_generation_cache_ttl_sec", 300) or 300)
    key = cache_key(f"gen-{kind}", p.encode("utf-8"), extra="v1")
    set_cached(key, result, ttl_sec=max(30, ttl))


def _async_job_cache_key(kind: str, prompt: str) -> str:
    p = (prompt or "").strip()
    return cache_key(f"gen-{kind}-async", p.encode("utf-8"), extra="v1")


def _job_state_pending(state: str) -> bool:
    s = (state or "").strip().lower()
    return s in {"queued", "deferred", "running", "in_progress", "pending"}


def _job_state_done(state: str) -> bool:
    s = (state or "").strip().lower()
    return s in {"complete", "completed"}


def _job_state_failed(state: str) -> bool:
    s = (state or "").strip().lower()
    return s in {"failed", "cancelled", "not_found"}


def _prompt_fingerprint(prompt: str) -> str:
    return hashlib.sha256((prompt or "").strip().encode("utf-8")).hexdigest()


def _media_arq_defer_for_user(current_user: models.User | None) -> float | None:
    if current_user and getattr(current_user, "is_admin", False):
        v = float(getattr(settings, "media_arq_defer_sec_admin", 0) or 0)
        return v if v > 0 else None
    user_plan = getattr(current_user, "subscription_plan", None) if current_user else None
    plan = get_effective_plan(user_plan)
    if plan in ("medium", "master"):
        v = float(getattr(settings, "media_arq_defer_sec_paid", 0) or 0)
    elif plan == "basic":
        v = float(getattr(settings, "media_arq_defer_sec_basic", 0) or 0)
    elif plan == "anon":
        v = float(getattr(settings, "media_arq_defer_sec_anon", 0) or 0)
    else:
        v = float(getattr(settings, "media_arq_defer_sec_free", 0) or 0)
    return v if v > 0 else None


def _media_async_rate_check(request: Request, current_user: models.User | None) -> None:
    if not bool(getattr(settings, "media_async_rate_limit_enabled", True)):
        return
    if current_user and getattr(current_user, "is_admin", False):
        return
    r = get_redis()
    if not r:
        return
    user_plan = getattr(current_user, "subscription_plan", None) if current_user else None
    plan = get_effective_plan(user_plan)
    lim_map = {
        "anon": int(getattr(settings, "media_async_rate_limit_anon", 24) or 24),
        "free": int(getattr(settings, "media_async_rate_limit_free", 40) or 40),
        "basic": int(getattr(settings, "media_async_rate_limit_basic", 60) or 60),
        "medium": int(getattr(settings, "media_async_rate_limit_paid", 120) or 120),
        "master": int(getattr(settings, "media_async_rate_limit_paid", 120) or 120),
    }
    limit = lim_map.get(plan, lim_map["free"])
    window = int(getattr(settings, "media_async_rate_limit_window_sec", 60) or 60)
    ip = get_client_ip(request)
    uid = current_user.id if current_user else 0
    bucket = int(time.time() // max(1, window))
    digest = hashlib.sha256(f"{ip}|{uid}|{plan}|{bucket}".encode("utf-8")).hexdigest()[:40]
    key = f"{_MEDIA_RL_PREFIX}{digest}"
    try:
        n = int(r.incr(key))
        if n == 1:
            r.expire(key, window + 2)
        if n > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitos pedidos de geração assíncrona. Aguarde e tente novamente.",
            )
    except HTTPException:
        raise
    except Exception:
        _log.debug("media async rate limit skip", exc_info=True)


def _idempotency_get_stored(idem_key: str) -> dict | None:
    r = get_redis()
    if not r or not (idem_key or "").strip():
        return None
    k = hashlib.sha256(idem_key.strip()[:256].encode("utf-8")).hexdigest()[:48]
    try:
        raw = r.get(f"{_MEDIA_IDEMP_PREFIX}{k}")
        if raw:
            return json.loads(raw)
    except Exception:
        _log.debug("idempotency get", exc_info=True)
    return None


def _idempotency_resolve_or_raise(idem_key: str | None, kind: str, prompt: str) -> str | None:
    if not (idem_key or "").strip():
        return None
    row = _idempotency_get_stored(idem_key)
    if not row:
        return None
    knd = (kind or "").strip().lower()
    ph = _prompt_fingerprint(prompt)
    if row.get("kind") != knd or row.get("prompt_fp") != ph:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="X-Idempotency-Key já usada com outro tipo de mídia ou prompt.",
        )
    jid = str(row.get("job_id") or "").strip()
    return jid or None


def _idempotency_store(idem_key: str | None, kind: str, prompt: str, job_id: str) -> None:
    if not (idem_key or "").strip():
        return
    r = get_redis()
    if not r:
        return
    k = hashlib.sha256(idem_key.strip()[:256].encode("utf-8")).hexdigest()[:48]
    ttl = int(getattr(settings, "media_idempotency_ttl_sec", 86400) or 86400)
    payload = {
        "kind": (kind or "").strip().lower(),
        "prompt_fp": _prompt_fingerprint(prompt),
        "job_id": job_id,
    }
    try:
        r.setex(
            f"{_MEDIA_IDEMP_PREFIX}{k}",
            max(60, ttl),
            json.dumps(payload, ensure_ascii=False),
        )
    except Exception:
        _log.debug("idempotency set", exc_info=True)


def _job_ctx_store(job_id: str, kind: str, prompt: str, current_user: models.User | None) -> None:
    r = get_redis()
    if not r:
        return
    p = (prompt or "").strip()
    if len(p) > 32000:
        p = p[:32000]
    ttl = int(getattr(settings, "media_job_context_ttl_sec", 7200) or 7200)
    payload = {
        "kind": (kind or "").strip().lower(),
        "prompt": p,
        "uid": current_user.id if current_user else None,
    }
    try:
        r.setex(
            f"{_MEDIA_JOBCTX_PREFIX}{(job_id or '').strip()}",
            max(120, ttl),
            json.dumps(payload, ensure_ascii=False),
        )
    except Exception:
        _log.debug("job ctx set", exc_info=True)


def _job_ctx_get(job_id: str) -> dict | None:
    r = get_redis()
    if not r:
        return None
    try:
        raw = r.get(f"{_MEDIA_JOBCTX_PREFIX}{(job_id or '').strip()}")
        if raw:
            return json.loads(raw)
    except Exception:
        _log.debug("job ctx get", exc_info=True)
    return None


def _can_user_abort_job(ctx: dict | None, user: models.User | None) -> bool:
    if not ctx:
        return True
    uid = ctx.get("uid")
    if uid is None:
        return True
    if not user:
        return False
    if getattr(user, "is_admin", False):
        return True
    return int(user.id) == int(uid)


def _media_generate_async_core(
    request: Request,
    db,
    current_user: models.User | None,
    kind: str,
    prompt: str,
) -> Dict[str, Any]:
    k = (kind or "").strip().lower()
    idem_hdr = (request.headers.get("X-Idempotency-Key") or "").strip()

    if idem_hdr:
        reused_id = _idempotency_resolve_or_raise(idem_hdr, k, prompt)
        if reused_id:
            try:
                st = inspect_job_sync(reused_id)
            except Exception:
                _log.exception("idempotency inspect job")
                raise HTTPException(status_code=503, detail=MSG_TRY_AGAIN_PT) from None
            _register_media_usage(db, request, k, current_user)
            return JSONResponse(
                status_code=202,
                content={
                    "ok": True,
                    "job_id": reused_id,
                    "state": st.get("state"),
                    "idempotent": True,
                },
            )

    _assert_media_limit(db, request, k, current_user)
    cached = _media_generation_cache_get(k, prompt)
    if cached is not None:
        _register_media_usage(db, request, k, current_user)
        return {"ok": True, "state": "completed", "result": cached, "from_cache": True}

    if not job_queue_enabled():
        sync_fn = {
            "image": run_image_job_sync,
            "video": run_video_job_sync,
            "music": run_music_job_sync,
        }[k]
        result = sync_fn(prompt)
        if not result.get("ok"):
            raise HTTPException(status_code=503, detail=MSG_TRY_AGAIN_PT)
        _media_generation_cache_set(k, prompt, result)
        _register_media_usage(db, request, k, current_user)
        return {"ok": True, "state": "completed", "result": result}

    _media_async_rate_check(request, current_user)

    key = _async_job_cache_key(k, prompt)
    prev = get_cached(key) or {}
    prev_id = str(prev.get("job_id") or "").strip()
    if prev_id:
        st = inspect_job_sync(prev_id)
        if _job_state_pending(str(st.get("state") or "")):
            _register_media_usage(db, request, k, current_user)
            return JSONResponse(
                status_code=202,
                content={"ok": True, "job_id": prev_id, "state": st.get("state")},
            )

    defer = _media_arq_defer_for_user(current_user)
    job_id = enqueue_media_job_id_sync(k, prompt, defer_by=defer)
    if idem_hdr:
        _idempotency_store(idem_hdr, k, prompt, job_id)
    _job_ctx_store(job_id, k, prompt, current_user)
    set_cached(key, {"job_id": job_id}, ttl_sec=300)
    _register_media_usage(db, request, k, current_user)
    return JSONResponse(
        status_code=202,
        content={"ok": True, "job_id": job_id, "state": "queued"},
    )


@router.post("/images/generate")
def images_generate(
    request: Request,
    prompt: str = Form(...),
    db=Depends(get_db),
    current_user: models.User | None = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    _assert_media_limit(db, request, "image", current_user)
    cached = _media_generation_cache_get("image", prompt)
    if cached is not None:
        _register_media_usage(db, request, "image", current_user)
        return cached
    try:
        result = run_image_job_sync(prompt)
    except RuntimeError:
        _log.exception("Geração de imagem falhou")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=MSG_TRY_AGAIN_PT,
        ) from None
    if not result.get("ok"):
        raise HTTPException(status_code=503, detail=MSG_TRY_AGAIN_PT)
    _media_generation_cache_set("image", prompt, result)
    _register_media_usage(db, request, "image", current_user)
    return result


@router.post("/images/fetch-url")
def images_fetch_url(
    url: str = Form(...),
) -> Dict[str, Any]:
    """
    Baixa bytes de uma URL de imagem em lista branca (Pollinations / Replicate delivery)
    e devolve base64 — o chat não carrega o domínio externo no browser (evita 502/cloudflared).
    """
    try:
        return fetch_whitelisted_image_url_to_base64(url)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pedido inválido.") from None
    except Exception:
        _log.exception("fetch-url imagem")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=MSG_TRY_AGAIN_PT,
        ) from None


@router.post("/videos/analyze")
async def videos_analyze(
    request: Request,
    file: UploadFile = File(...),
    db=Depends(get_db),
    current_user: models.User | None = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    _assert_media_limit(db, request, "video", current_user)
    _register_media_usage(db, request, "video", current_user)
    return analyze_video_basic(file)


@router.post("/videos/generate")
def videos_generate(
    request: Request,
    prompt: str = Form(...),
    db=Depends(get_db),
    current_user: models.User | None = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    _assert_media_limit(db, request, "video", current_user)
    cached = _media_generation_cache_get("video", prompt)
    if cached is not None:
        _register_media_usage(db, request, "video", current_user)
        return cached
    try:
        result = run_video_job_sync(prompt)
    except Exception:
        _log.exception("Geração de vídeo falhou")
        raise HTTPException(status_code=503, detail=MSG_TRY_AGAIN_PT) from None
    if not result.get("ok"):
        raise HTTPException(status_code=503, detail=MSG_TRY_AGAIN_PT)
    _media_generation_cache_set("video", prompt, result)
    _register_media_usage(db, request, "video", current_user)
    return result


@router.post("/music/generate")
def music_generate(
    request: Request,
    prompt: str = Form(...),
    db=Depends(get_db),
    current_user: models.User | None = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    _assert_media_limit(db, request, "music", current_user)
    cached = _media_generation_cache_get("music", prompt)
    if cached is not None:
        _register_media_usage(db, request, "music", current_user)
        return cached
    try:
        result = run_music_job_sync(prompt)
    except Exception:
        _log.exception("Geração de áudio falhou")
        raise HTTPException(status_code=503, detail=MSG_TRY_AGAIN_PT) from None
    if not result.get("ok"):
        raise HTTPException(status_code=503, detail=MSG_TRY_AGAIN_PT)
    _media_generation_cache_set("music", prompt, result)
    _register_media_usage(db, request, "music", current_user)
    return result


@router.post("/tts/generate")
def tts_generate(
    request: Request,
    text: str = Form(...),
    voice: str | None = Form(None),
    db=Depends(get_db),
    current_user: models.User | None = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    # Microfone/Audio SEM limite de plano - funciona em TODOS os planos
    result = generate_tts_from_text(text, voice=voice)
    if not result.get("ok"):
        raise HTTPException(status_code=503, detail=MSG_TRY_AGAIN_PT)
    # Registrar uso sem bloquear
    try:
        _register_media_usage(db, request, "tts", current_user)
    except:
        pass  # Não bloquear mesmo se falhar registro
    return result


@router.post("/images/generate-async")
def images_generate_async(
    request: Request,
    prompt: str = Form(...),
    db=Depends(get_db),
    current_user: models.User | None = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    return _media_generate_async_core(request, db, current_user, "image", prompt)


@router.post("/videos/generate-async")
def videos_generate_async(
    request: Request,
    prompt: str = Form(...),
    db=Depends(get_db),
    current_user: models.User | None = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    return _media_generate_async_core(request, db, current_user, "video", prompt)


@router.post("/music/generate-async")
def music_generate_async(
    request: Request,
    prompt: str = Form(...),
    db=Depends(get_db),
    current_user: models.User | None = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    return _media_generate_async_core(request, db, current_user, "music", prompt)


@router.get("/jobs/{job_id}")
def media_job_status(job_id: str) -> Dict[str, Any]:
    if not (job_id or "").strip():
        raise HTTPException(status_code=400, detail="job_id inválido.")
    if not job_queue_enabled():
        raise HTTPException(status_code=503, detail="Fila indisponível.")
    try:
        st = inspect_job_sync(job_id.strip())
    except Exception:
        _log.exception("status job mídia")
        raise HTTPException(status_code=503, detail=MSG_TRY_AGAIN_PT) from None
    state = str(st.get("state") or "").lower()
    result = st.get("result")
    if _job_state_done(state) and isinstance(result, dict) and result.get("ok"):
        ctx = _job_ctx_get(job_id.strip())
        if ctx and ctx.get("kind") and ctx.get("prompt") is not None:
            _media_generation_cache_set(str(ctx["kind"]), str(ctx["prompt"]), result)
        return {"ok": True, "job_id": job_id, "state": "completed", "result": result}
    if _job_state_failed(state):
        return {"ok": False, "job_id": job_id, "state": state}
    return {"ok": True, "job_id": job_id, "state": state or "queued"}


@router.delete("/jobs/{job_id}")
def media_job_abort(
    job_id: str,
    current_user: models.User | None = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    if not (job_id or "").strip():
        raise HTTPException(status_code=400, detail="job_id inválido.")
    if not job_queue_enabled():
        raise HTTPException(status_code=503, detail="Fila indisponível.")
    ctx = _job_ctx_get(job_id.strip())
    if not _can_user_abort_job(ctx, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não autorizado a cancelar este job.",
        )
    try:
        out = abort_media_job_sync(job_id.strip())
    except Exception:
        _log.exception("abort job mídia")
        raise HTTPException(status_code=503, detail=MSG_TRY_AGAIN_PT) from None
    err = out.get("error")
    if err == "not_found":
        raise HTTPException(status_code=404, detail="Job não encontrado.")
    if err == "already_complete":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job já concluído.",
        )
    if out.get("ok"):
        return {"ok": True, "job_id": job_id, "state": out.get("state")}
    raise HTTPException(status_code=503, detail=MSG_TRY_AGAIN_PT)

