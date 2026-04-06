import asyncio
import json
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from vereda_backend.core.config import settings
from vereda_backend.core.plan_limits import (
    count_user_messages_this_month,
    get_message_limit,
)
from vereda_backend.core.rate_limit import RateLimiter, get_client_ip
from vereda_backend.core.security import get_current_user
from vereda_backend.db import models
from vereda_backend.db.session import get_db
from vereda_backend.schemas.chat import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatSessionSummary,
    ChatMessageItem,
)
from vereda_backend.services.media_engine import (
    analyze_video_basic,
    describe_image_with_ollama,
    transcribe_audio_local,
)
from vereda_backend.services.tools import analyze_image_basic
from vereda_backend.services.chat_engine import create_chat_completion, stream_chat_completion


router = APIRouter()

_session_create_limiter = RateLimiter(
    max_calls=max(5, int(getattr(settings, "session_create_per_ip_hour", 40) or 40)),
    window_seconds=3600,
    max_keys=15_000,
)


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


async def _parse_chat_body(request: Request) -> Tuple[ChatRequest, List]:
    """Aceita application/json ou multipart/form-data (payload + files)."""
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
    return ChatRequest.model_validate(body), []


def _get_or_create_session(
    db: Session,
    user_id: Optional[int],
    session_id: Optional[int],
    http_request: Optional[Request] = None,
) -> Optional[models.ChatSession]:
    if session_id:
        s = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()
        if s:
            return s
    if http_request is not None:
        _session_create_limiter.check(
            get_client_ip(http_request),
            detail="Muitas conversas novas deste IP nesta hora. Aguarde ou continue uma sessão existente.",
        )
    session = models.ChatSession(user_id=user_id, title="Nova conversa")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/chat/sessions", response_model=List[ChatSessionSummary])
def list_chat_sessions(
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user),
) -> List[ChatSessionSummary]:
    """
    Lista as últimas sessões de chat do usuário autenticado para exibir no histórico.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação necessária para listar histórico de conversas.",
        )
    sessions = (
        db.query(models.ChatSession)
        .filter(models.ChatSession.user_id == current_user.id)
        .order_by(models.ChatSession.updated_at.desc())
        .limit(50)
        .all()
    )
    return [
        ChatSessionSummary(
            id=s.id,
            title=s.title or "Nova conversa",
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in sessions
    ]


@router.get("/chat/sessions/{session_id}/messages", response_model=List[ChatMessageItem])
def list_chat_session_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user),
) -> List[ChatMessageItem]:
    """
    Retorna as mensagens de uma sessão específica do usuário autenticado.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação necessária para carregar histórico de conversa.",
        )
    session = (
        db.query(models.ChatSession)
        .filter(models.ChatSession.id == session_id)
        .filter(models.ChatSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sessão não encontrada.")

    logs = (
        db.query(models.ConversationLog)
        .filter(models.ConversationLog.session_id == session.id)
        .order_by(models.ConversationLog.created_at.asc())
        .all()
    )
    items: List[ChatMessageItem] = []
    for log in logs:
        role: str = log.role or "assistant"
        if role not in ("system", "user", "assistant"):
            role = "assistant"
        items.append(
            ChatMessageItem(
                id=log.id,
                role=role,  # type: ignore[arg-type]
                content=log.content,
                created_at=log.created_at,
            )
        )
    return items


def _stream_events(
    db: Session,
    request: ChatRequest,
    sid: Optional[int],
    current_user: Optional[models.User],
    client_ip: str,
):
    full_content: list[str] = []
    try:
        for chunk in stream_chat_completion(
            db, request, user=current_user, client_ip=client_ip
        ):
            full_content.append(chunk)
            yield f"data: {json.dumps({'content': chunk})}\n\n"
    finally:
        if full_content and sid:
            full_text = "".join(full_content)
            db.add(
                models.ConversationLog(
                    user_id=current_user.id if current_user else None,
                    session_id=sid,
                    role="assistant",
                    content=full_text,
                )
            )
            db.commit()


@router.post("/chat/completions", response_model=ChatResponse)
async def chat_completions(
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user),
) -> ChatResponse:
    """
    Chat Completions. Aceita JSON ou multipart (payload + files). Cria/usa sessão e grava logs.
    """
    request, _files = await _parse_chat_body(http_request)

    # Reconhecimento de pagamento: aplicar limite de mensagens por plano
    if current_user:
        plan = getattr(current_user, "subscription_plan", None) or "free"
        limit = get_message_limit(plan)
        if limit is not None:
            count = count_user_messages_this_month(db, current_user.id)
            new_user_msgs = sum(1 for m in request.messages if getattr(m, "role", None) == "user")
            if count + new_user_msgs > limit:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Você atingiu o limite de mensagens do seu plano neste mês. Faça upgrade para continuar usando a IA sem interrupções.",
                )

    session = _get_or_create_session(
        db,
        current_user.id if current_user else None,
        getattr(request, "session_id", None),
        http_request,
    )
    sid = session.id if session else None

    for msg in request.messages:
        db.add(
            models.ConversationLog(
                user_id=current_user.id if current_user else None,
                session_id=sid,
                role=msg.role,
                content=msg.content,
            )
        )
    db.commit()

    response = await asyncio.to_thread(
        create_chat_completion,
        db,
        request,
        current_user,
        get_client_ip(http_request),
    )

    if response.choices:
        assistant_msg = response.choices[0].message
        db.add(
            models.ConversationLog(
                user_id=current_user.id if current_user else None,
                session_id=sid,
                role=assistant_msg.role,
                content=assistant_msg.content,
            )
        )
        db.commit()

    return response


@router.post("/chat/completions/stream")
async def chat_completions_stream(
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user),
):
    request, _files = await _parse_chat_body(http_request)

    if current_user:
        plan = getattr(current_user, "subscription_plan", None) or "free"
        limit = get_message_limit(plan)
        if limit is not None:
            count = count_user_messages_this_month(db, current_user.id)
            new_user_msgs = sum(
                1 for m in request.messages if getattr(m, "role", None) == "user"
            )
            if count + new_user_msgs > limit:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Você atingiu o limite de mensagens do seu plano neste mês. Faça upgrade para continuar usando a IA sem interrupções.",
                )

    session = _get_or_create_session(
        db,
        current_user.id if current_user else None,
        getattr(request, "session_id", None),
        http_request,
    )
    sid = session.id if session else None

    for msg in request.messages:
        db.add(
            models.ConversationLog(
                user_id=current_user.id if current_user else None,
                session_id=sid,
                role=msg.role,
                content=msg.content,
            )
        )
    db.commit()

    return StreamingResponse(
        _stream_events(db, request, sid, current_user, get_client_ip(http_request)),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

