import json
import hashlib
import logging
from datetime import datetime
from typing import Generator, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from vereda_backend.db import models
from vereda_backend.db.session import get_db
from vereda_backend.schemas.chat import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
)
from vereda_backend.core.security import get_current_user_optional
from vereda_backend.services.chat_engine import create_chat_completion, stream_chat_completion
from vereda_backend.services.media_engine import (
    analyze_video_basic,
    describe_image_with_ollama,
    transcribe_audio_local,
)
from vereda_backend.services.tools import analyze_image_basic


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api")

# Mesmas rotas sob /v1
router_v1 = APIRouter()

# Na raiz: /public-chat e /public-chat/stream (um caminho real, sem prefixo)
router_root = APIRouter()


from vereda_backend.core.rate_limit import check_public_chat_tier, get_client_ip as _get_client_ip


def _public_session_title(ip: str) -> str:
    digest = hashlib.sha256(ip.encode("utf-8")).hexdigest()[:16]
    return f"Conversa pública {digest}"


def _client_ip(request: Request) -> str:
    return _get_client_ip(request)


def _attachments_context(file_list: List) -> str:
    lines: List[str] = []
    for f in file_list:
        content_type = (getattr(f, "content_type", "") or "").lower()
        filename = getattr(f, "filename", "arquivo")
        try:
            if content_type.startswith("image/"):
                info = analyze_image_basic(f)
                size = info.get("size", {})
                mean = info.get("mean_rgb", {})
                vision = describe_image_with_ollama(f)
                lines.append(
                    f"- imagem {filename}: {size.get('width')}x{size.get('height')}, "
                    f"cor média RGB=({mean.get('r')}, {mean.get('g')}, {mean.get('b')})."
                )
                if vision:
                    lines.append(f"  descrição IA: {vision}")
            elif content_type.startswith("video/"):
                info = analyze_video_basic(f)
                lines.append(
                    f"- vídeo {filename}: tipo={info.get('content_type') or content_type}."
                )
            elif content_type.startswith("audio/"):
                transcript = transcribe_audio_local(f)
                lines.append(
                    f"- áudio {filename}: tipo={content_type}. "
                    + (f"Transcrição: {transcript}" if transcript else "Sem transcrição disponível.")
                )
            else:
                lines.append(f"- arquivo {filename}: tipo={content_type or 'desconhecido'}.")
        except Exception:
            lines.append(f"- arquivo {filename}: não foi possível extrair metadados.")
    if not lines:
        return ""
    return "\nContexto dos anexos:\n" + "\n".join(lines)


async def _parse_public_chat_body(request: Request) -> Tuple[ChatRequest, list]:
    """
    Aceita application/json (body = ChatRequest) ou multipart/form-data
    (campo 'payload' = JSON do ChatRequest, campo 'files' = lista de arquivos).
    Retorna (ChatRequest, lista de arquivos).
    """
    content_type = (request.headers.get("content-type") or "").lower()
    if "multipart/form-data" in content_type:
        form = await request.form()
        payload_str = form.get("payload")
        if payload_str is None:
            raise HTTPException(status_code=400, detail="payload ausente em multipart")
        if hasattr(payload_str, "read"):
            payload_str = (payload_str.read() or b"").decode("utf-8")
        try:
            data = json.loads(payload_str)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"payload JSON inválido: {e}")
        req = ChatRequest.model_validate(data)
        files = form.getlist("files")
        file_list = [f for f in files if f and getattr(f, "filename", None)]
        if file_list and req.messages:
            last_user = next((m for m in reversed(req.messages) if m.role == "user"), None)
            if last_user:
                n = len(file_list)
                suffix = f" [anexos: {n} arquivo(s)]"
                context = _attachments_context(file_list)
                if not last_user.content.endswith(suffix):
                    req.messages = [
                        *req.messages[:-1],
                        ChatMessage(role=last_user.role, content=last_user.content + suffix + context),
                    ]
        return req, file_list
    try:
        body = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="JSON inválido no corpo da requisição.")
    req = ChatRequest.model_validate(body)
    return req, []


async def _public_chat_impl(
    http_request: Request,
    db: Session,
    optional_user: Optional[models.User] = None,
) -> ChatResponse:
    """Implementação compartilhada para /api/public-chat e /v1/public-chat."""
    ip = _client_ip(http_request)
    check_public_chat_tier(
        ip,
        optional_user,
        detail="Limite diário de mensagens atingido. Aguarde ou use uma conta com plano adequado.",
    )
    request, _files = await _parse_public_chat_body(http_request)
    session_title = _public_session_title(ip)
    session = (
        db.query(models.ChatSession)
        .filter(models.ChatSession.user_id.is_(None))
        .filter(models.ChatSession.title == session_title)
        .order_by(models.ChatSession.created_at.desc())
        .first()
    )
    if not session:
        session = models.ChatSession(user_id=None, title=session_title)
        db.add(session)
        db.commit()
        db.refresh(session)
    sid = session.id
    for msg in request.messages:
        db.add(
            models.ConversationLog(
                user_id=None,
                session_id=sid,
                role=msg.role,
                content=msg.content,
            )
        )
    db.commit()
    try:
        response = create_chat_completion(
            db=db,
            req=request,
            user=optional_user,
            client_ip=_client_ip(http_request),
        )
    except Exception as exc:
        logger.exception("Erro interno em public-chat: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servico de IA indisponivel no momento.",
        )
    if response.choices:
        db.add(
            models.ConversationLog(
                user_id=None,
                session_id=sid,
                role="assistant",
                content=response.choices[0].message.content,
            )
        )
        db.commit()
    return response


@router.post("/public-chat", response_model=ChatResponse)
async def public_chat(
    http_request: Request,
    db: Session = Depends(get_db),
    optional_user: Optional[models.User] = Depends(get_current_user_optional),
) -> ChatResponse:
    """Modo gratuito sem login. Aceita JSON ou multipart (payload + files)."""
    return await _public_chat_impl(http_request, db, optional_user)


@router_v1.post("/public-chat", response_model=ChatResponse)
async def public_chat_v1(
    http_request: Request,
    db: Session = Depends(get_db),
    optional_user: Optional[models.User] = Depends(get_current_user_optional),
) -> ChatResponse:
    """Mesmo que /api/public-chat, sob /v1 para proxy que só encaminha /v1."""
    return await _public_chat_impl(http_request, db, optional_user)


def _stream_events(
    db: Session,
    request: ChatRequest,
    sid: int,
    optional_user: Optional[models.User] = None,
    client_ip: str = "unknown",
) -> Generator[str, None, None]:
    """Gera eventos SSE para resposta imediata (streaming)."""
    full_content: List[str] = []
    try:
        for chunk in stream_chat_completion(
            db, request, user=optional_user, client_ip=client_ip
        ):
            full_content.append(chunk)
            yield f"data: {json.dumps({'content': chunk})}\n\n"
    finally:
        if full_content:
            full_text = "".join(full_content)
            db.add(
                models.ConversationLog(
                    user_id=None,
                    session_id=sid,
                    role="assistant",
                    content=full_text,
                )
            )
            db.commit()


async def _public_chat_stream_impl(
    http_request: Request,
    db: Session,
    optional_user: Optional[models.User] = None,
):
    """Stream compartilhado para /api/public-chat/stream e /v1/public-chat/stream."""
    ip = _client_ip(http_request)
    check_public_chat_tier(
        ip,
        optional_user,
        detail="Limite diário de mensagens atingido. Aguarde ou use uma conta com plano adequado.",
    )
    request, _ = await _parse_public_chat_body(http_request)
    session_title = _public_session_title(ip)
    session = (
        db.query(models.ChatSession)
        .filter(models.ChatSession.user_id.is_(None))
        .filter(models.ChatSession.title == session_title)
        .order_by(models.ChatSession.created_at.desc())
        .first()
    )
    if not session:
        session = models.ChatSession(user_id=None, title=session_title)
        db.add(session)
        db.commit()
        db.refresh(session)
    sid = session.id
    for msg in request.messages:
        db.add(
            models.ConversationLog(
                user_id=None,
                session_id=sid,
                role=msg.role,
                content=msg.content,
            )
        )
    db.commit()
    return StreamingResponse(
        _stream_events(db, request, sid, optional_user, ip),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/public-chat/stream")
async def public_chat_stream(
    http_request: Request,
    db: Session = Depends(get_db),
    optional_user: Optional[models.User] = Depends(get_current_user_optional),
):
    """Chat público em streaming. Body: JSON com model, messages."""
    return await _public_chat_stream_impl(http_request, db, optional_user)


@router_v1.post("/public-chat/stream")
async def public_chat_stream_v1(
    http_request: Request,
    db: Session = Depends(get_db),
    optional_user: Optional[models.User] = Depends(get_current_user_optional),
):
    """Mesmo que /api/public-chat/stream, sob /v1."""
    return await _public_chat_stream_impl(http_request, db, optional_user)


@router_root.post("/public-chat", response_model=ChatResponse)
async def public_chat_root(
    http_request: Request,
    db: Session = Depends(get_db),
    optional_user: Optional[models.User] = Depends(get_current_user_optional),
) -> ChatResponse:
    """Chat público na raiz: POST /public-chat."""
    return await _public_chat_impl(http_request, db, optional_user)


@router_root.post("/public-chat/stream")
async def public_chat_stream_root(
    http_request: Request,
    db: Session = Depends(get_db),
    optional_user: Optional[models.User] = Depends(get_current_user_optional),
):
    """Stream do chat público na raiz: POST /public-chat/stream."""
    return await _public_chat_stream_impl(http_request, db, optional_user)

