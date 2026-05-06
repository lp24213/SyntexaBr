"""API multimodal: análise de ficheiros, OCR, STT, exportação PDF/XLSX/DOCX, geração de imagem no servidor."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from starlette.responses import Response

from vereda_backend.audio.stt import transcribe_bytes
from vereda_backend.audio.tts import synthesize_text
from vereda_backend.audio.voice_router import route_voice_intent
from vereda_backend.cache.media_cache import cache_key, get_cached, set_cached
from vereda_backend.core.config import settings
from vereda_backend.core.rate_limit import get_client_ip
from vereda_backend.core.security import get_current_user_optional
from vereda_backend.db import models
from vereda_backend.db.session import get_db
from vereda_backend.schemas.chat import ChatMessage, ChatRequest
from vereda_backend.services.chat_engine import create_chat_completion
from vereda_backend.services.media_engine import (
    generate_music_from_prompt,
    generate_tts_from_text,
    generate_video_from_prompt,
)
from vereda_backend.image.generator import generate_image_backend
from vereda_backend.multimodal.smart_export import run_smart_export
from vereda_backend.image.ocr import extract_text
from vereda_backend.multimodal.router import process_bytes
from vereda_backend.queues.media_jobs import run_pdf_export_sync, run_xlsx_export_sync
from vereda_backend.docs.docx_builder import build_docx_bytes

router = APIRouter(prefix="/multimodal")
_log = logging.getLogger(__name__)


class PdfExportBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    subtitle: Optional[str] = Field(None, max_length=500)
    sections: List[Dict[str, Any]] = Field(default_factory=list)


class XlsxExportBody(BaseModel):
    sheet_title: str = Field(default="Dados", max_length=31)
    rows: List[List[Any]] = Field(default_factory=list)
    header: bool = True
    document_title: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Faixa de título opcional no topo da folha (openpyxl).",
    )


class DocxExportBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    sections: List[Dict[str, Any]] = Field(default_factory=list)


class TxtExportBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    body: str = Field(default="", max_length=500_000)


class SmartExportBody(BaseModel):
    user_message: str = Field(..., min_length=2, max_length=12000)
    generate_audio: bool = True
    assistant_reply: str | None = Field(
        default=None,
        max_length=500_000,
        description="Última resposta do assistente no chat — usada como corpo do PDF/planilha quando o pedido é só comando de exportação.",
    )


@router.get("/capabilities")
def multimodal_capabilities() -> Dict[str, Any]:
    _az = bool((getattr(settings, "azure_speech_key", None) or "").strip()) and bool(
        (getattr(settings, "azure_speech_region", None) or "").strip()
    )
    return {
        "stt": bool((settings.local_stt_endpoint or "").strip()) or _az,
        "tts": True,
        "tts_azure": _az,
        "vision_llm": bool(
            (settings.local_llm_endpoint or settings.azure_tgi_endpoint or settings.exllama_endpoint or settings.remote_llm_endpoint or "").strip()
        ),
        "image_gen_server": bool((settings.local_image_gen_endpoint or "").strip())
        or bool(getattr(settings, "media_use_pollinations", False)),
        "redis_queue": bool((settings.redis_url or "").strip()),
        "azure_blob_queue": bool((settings.azure_storage_connection_string or "").strip()),
    }


@router.post("/analyze")
async def multimodal_analyze(
    request: Request,
    file: UploadFile = File(...),
    deep: str = Form("false"),
    current_user: models.User | None = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    deep_flag = (deep or "").strip().lower() in ("1", "true", "yes", "on")
    data = await file.read()
    if len(data) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Ficheiro demasiado grande (máx. 25 MB).")
    uid = str(current_user.id) if current_user else get_client_ip(request)
    ck = cache_key("analyze", data, f"deep={deep_flag}:{file.filename}:u={uid}")
    hit = get_cached(ck)
    if hit:
        hit["cache"] = "hit"
        return hit
    out = process_bytes(file.filename or "upload.bin", data, file.content_type or "", deep=deep_flag)
    out["cache"] = "miss"
    set_cached(ck, out, ttl_sec=180)
    _log.debug("multimodal analyze user=%s bytes=%s", uid, len(data))
    return out


@router.post("/ocr")
async def multimodal_ocr(
    file: UploadFile = File(...),
    kind: str = Form("auto"),
) -> Dict[str, Any]:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Ficheiro vazio.")
    k = kind if kind in ("auto", "pdf", "image") else "auto"
    return extract_text(data, kind=k)  # type: ignore[arg-type]


@router.post("/transcribe")
async def multimodal_transcribe(
    file: UploadFile = File(...),
) -> Dict[str, Any]:
    data = await file.read()
    return transcribe_bytes(
        data,
        filename=file.filename or "audio.bin",
        content_type=file.content_type or "application/octet-stream",
    )


@router.post("/voice/conversation")
async def multimodal_voice_conversation(
    request: Request,
    file: UploadFile = File(...),
    max_tokens: int = Form(8192),
    db: Session = Depends(get_db),
    current_user: models.User | None = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    """
    STT → mesmas intenções que o chat em texto (imagem, vídeo, áudio, ficheiros reais) → TTS quando fizer sentido.
    """
    data = await file.read()
    if len(data) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Áudio demasiado grande (máx. 25 MB).")
    stt_out = transcribe_bytes(
        data,
        filename=file.filename or "audio.bin",
        content_type=file.content_type or "application/octet-stream",
    )
    transcript = str(stt_out.get("text") or "").strip()
    if not transcript:
        raise HTTPException(
            status_code=400,
            detail=stt_out.get("detail") or "Transcrição vazia.",
        )

    routed = route_voice_intent(transcript)
    intent = str(routed.get("intent") or "chat")
    payload = routed.get("payload") if isinstance(routed.get("payload"), dict) else {}

    def _chat_reply() -> Dict[str, Any]:
        req = ChatRequest(
            model="syntexa-large",
            messages=[ChatMessage(role="user", content=transcript)],
            max_tokens=min(max(16, max_tokens), 8192),
        )
        chat_resp = create_chat_completion(
            db,
            req,
            current_user,
            get_client_ip(request),
        )
        reply = ""
        if chat_resp.choices:
            reply = (chat_resp.choices[0].message.content or "").strip()
        if not reply:
            reply = "Não obtive uma resposta do modelo."
        tts_out = generate_tts_from_text(reply)
        return {
            "ok": True,
            "transcript": transcript,
            "reply": reply,
            "stt": stt_out,
            "tts": tts_out,
            "voice_intent": intent,
        }

    if intent == "generate_image":
        prompt = str(payload.get("prompt") or transcript).strip()
        try:
            img = generate_image_backend(prompt)
            ok = bool(img.get("ok")) or bool(
                img.get("image_base64") or img.get("url") or img.get("image_url")
            )
            if not ok:
                raise RuntimeError("imagem_sem_payload")
            reply = "Imagem gerada."
            tts_out = generate_tts_from_text(reply)
            return {
                "ok": True,
                "transcript": transcript,
                "reply": reply,
                "stt": stt_out,
                "tts": tts_out,
                "voice_intent": "generate_image",
                "image_base64": img.get("image_base64"),
                "mime": img.get("mime") or "image/png",
                "image_url": img.get("url") or img.get("image_url"),
                "provider": img.get("provider"),
            }
        except Exception as exc:
            _log.warning("Voz → imagem falhou: %s", exc)

    if intent == "generate_video":
        prompt = str(payload.get("prompt") or transcript).strip()
        try:
            vid = generate_video_from_prompt(prompt)
            url = vid.get("url") or vid.get("video_url") or ""
            reply = "Vídeo gerado." if url else "Pedido de vídeo registado."
            tts_out = generate_tts_from_text(reply)
            return {
                "ok": True,
                "transcript": transcript,
                "reply": reply,
                "stt": stt_out,
                "tts": tts_out,
                "voice_intent": "generate_video",
                "video_url": url,
                "media": {"type": "video", "url": url},
            }
        except Exception as exc:
            _log.warning("Voz → vídeo falhou: %s", exc)

    if intent == "generate_music":
        prompt = str(payload.get("prompt") or transcript).strip()
        try:
            mus = generate_music_from_prompt(prompt)
            url = mus.get("audio_url") or mus.get("url") or ""
            reply = "Áudio gerado." if url else "Pedido de áudio registado."
            tts_out = generate_tts_from_text(reply)
            return {
                "ok": True,
                "transcript": transcript,
                "reply": reply,
                "stt": stt_out,
                "tts": tts_out,
                "voice_intent": "generate_music",
                "audio_url": url,
                "media": {"type": "audio", "url": url},
            }
        except Exception as exc:
            _log.warning("Voz → música falhou: %s", exc)

    try:
        sxp = run_smart_export(transcript, generate_audio=True, assistant_reply=None)
    except Exception as exc:
        _log.exception("Voz → smart_export")
        sxp = {"ok": False}
    if isinstance(sxp, dict) and sxp.get("ok"):
        summary = str(sxp.get("summary") or "").strip()
        tts_out = generate_tts_from_text((summary or "Ficheiros gerados.")[:3500])
        return {
            "ok": True,
            "transcript": transcript,
            "reply": summary or "Ficheiros gerados.",
            "stt": stt_out,
            "tts": tts_out,
            "voice_intent": str(sxp.get("intent") or "smart_export"),
            "files": sxp.get("files") or [],
        }

    try:
        return _chat_reply()
    except Exception as exc:
        _log.exception("voice conversation chat")
        raise HTTPException(
            status_code=503, detail="Falha ao gerar resposta de texto."
        ) from exc


@router.post("/voice/intent")
def multimodal_voice_intent(transcript: str = Form(...)) -> Dict[str, Any]:
    return route_voice_intent(transcript)


@router.post("/tts")
def multimodal_tts(
    text: str = Form(...),
    voice: str | None = Form(None),
) -> Dict[str, Any]:
    return synthesize_text(text, voice=voice)


@router.post("/export/pdf")
def multimodal_export_pdf(body: PdfExportBody) -> Response:
    try:
        raw = run_pdf_export_sync(body.title, body.sections, body.subtitle)
    except Exception as exc:
        _log.exception("pdf export")
        raise HTTPException(status_code=503, detail="Falha ao gerar PDF.") from exc
    fn = "".join(c for c in body.title[:60] if c.isalnum() or c in (" ", "-", "_")).strip() or "documento"
    return Response(
        content=raw,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{fn}.pdf"'},
    )


@router.post("/export/xlsx")
def multimodal_export_xlsx(body: XlsxExportBody) -> Response:
    try:
        raw = run_xlsx_export_sync(
            body.sheet_title,
            body.rows,
            body.header,
            document_title=body.document_title,
        )
    except Exception as exc:
        _log.exception("xlsx export")
        raise HTTPException(status_code=503, detail="Falha ao gerar planilha.") from exc
    st = "".join(c for c in body.sheet_title[:40] if c.isalnum() or c in (" ", "-", "_")) or "dados"
    return Response(
        content=raw,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{st}.xlsx"'},
    )


@router.post("/export/docx")
def multimodal_export_docx(body: DocxExportBody) -> Response:
    try:
        raw = build_docx_bytes(body.title, body.sections)
    except Exception as exc:
        _log.exception("docx export")
        raise HTTPException(status_code=503, detail="Falha ao gerar DOCX.") from exc
    fn = "".join(c for c in body.title[:60] if c.isalnum() or c in (" ", "-", "_")).strip() or "documento"
    return Response(
        content=raw,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{fn}.docx"'},
    )


@router.post("/smart-export")
def multimodal_smart_export(body: SmartExportBody) -> Dict[str, Any]:
    from vereda_backend.multimodal.smart_export import run_smart_export

    out = run_smart_export(
        body.user_message,
        generate_audio=body.generate_audio,
        assistant_reply=body.assistant_reply,
    )
    if not out.get("ok"):
        raise HTTPException(
            status_code=400,
            detail=str(out.get("detail") or "Pedido não suportado."),
        )
    return out


@router.post("/export/txt")
def multimodal_export_txt(body: TxtExportBody) -> Response:
    raw = (body.body or "").encode("utf-8")
    fn = "".join(c for c in body.title[:60] if c.isalnum() or c in (" ", "-", "_")).strip() or "documento"
    return Response(
        content=raw,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{fn}.txt"'},
    )


@router.post("/image/generate")
def multimodal_image_generate(
    prompt: str = Form(...),
) -> Dict[str, Any]:
    try:
        return generate_image_backend(prompt)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc)[:500],
        ) from exc


@router.post("/json/export")
def multimodal_json_export(payload: Dict[str, Any] = Body(...)) -> Response:
    """Exporta JSON formatado como ficheiro .json (útil no chat)."""
    raw = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    return Response(
        content=raw,
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="syntexa-export.json"'},
    )
