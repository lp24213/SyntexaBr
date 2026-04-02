from typing import Any, Dict

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status

from vereda_backend.core.plan_limits import (
    count_media_usage_this_month,
    get_effective_plan,
    get_media_limit,
)
from vereda_backend.services.media_engine import (
    analyze_video_basic,
    fetch_whitelisted_image_url_to_base64,
    generate_image_from_prompt,
    generate_music_from_prompt,
    generate_tts_from_text,
    generate_video_from_prompt,
)
from vereda_backend.core.security import get_current_user_optional
from vereda_backend.db import models
from vereda_backend.db.session import get_db


router = APIRouter(prefix="/media")


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
    ip = (request.client.host if request and request.client else None) or "unknown"
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
    ip = (request.client.host if request and request.client else None) or "unknown"
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


@router.post("/images/generate")
def images_generate(
    request: Request,
    prompt: str = Form(...),
    db=Depends(get_db),
    current_user: models.User | None = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    _assert_media_limit(db, request, "image", current_user)
    try:
        result = generate_image_from_prompt(prompt)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    if not result.get("ok"):
        raise HTTPException(status_code=503, detail=result.get("detail") or "Imagem indisponivel.")
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
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Falha ao baixar imagem: {exc}",
        ) from exc


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
    result = generate_video_from_prompt(prompt)
    if not result.get("ok"):
        raise HTTPException(status_code=503, detail=result.get("detail") or "Video indisponivel.")
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
    result = generate_music_from_prompt(prompt)
    if not result.get("ok"):
        raise HTTPException(status_code=503, detail=result.get("detail") or "Audio indisponivel.")
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
    _assert_media_limit(db, request, "tts", current_user)
    result = generate_tts_from_text(text, voice=voice)
    if not result.get("ok"):
        raise HTTPException(status_code=503, detail=result.get("detail") or "TTS indisponivel.")
    _register_media_usage(db, request, "tts", current_user)
    return result

