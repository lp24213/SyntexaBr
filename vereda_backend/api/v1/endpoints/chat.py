import asyncio
import json
import logging
import time
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from vereda_backend.core.config import settings
from vereda_backend.core.chat_context import reset_chat_request_context, set_chat_request_context
from vereda_backend.core.public_messages import MSG_TRY_AGAIN_PT
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
    describe_image_with_vision_llm,
    transcribe_audio_local,
)
from vereda_backend.services.tools import analyze_image_basic
from vereda_backend.services.chat_engine import (
    create_chat_completion,
    record_stream_chat_completion_audit,
    stream_chat_completion,
)
from vereda_backend.ai_runtime import llm_engine as runtime_llm_engine
from vereda_backend.services.conversation_store import (
    ensure_conversation,
    ensure_v2_session,
    persist_assistant_output,
    persist_input_message_batch,
)
from vereda_backend.core.syntexa_intel import detect_language, detect_sentiment, detect_subject
from vereda_backend.core.syntexa_intel import remember_user_preference
from vereda_backend.core.prom_metrics import record_chat_error, record_chat_success
from vereda_backend.core.subscription import require_subscription


router = APIRouter()
_log = logging.getLogger(__name__)

_session_create_limiter = RateLimiter(
    max_calls=max(5, int(getattr(settings, "session_create_per_ip_hour", 40) or 40)),
    window_seconds=3600,
    max_keys=15_000,
)


def _resolve_locale(preferred: Optional[str], accept_language: Optional[str]) -> str:
    raw = ((preferred or "") + "," + (accept_language or "")).lower()
    if "en" in raw:
        return "en-US"
    return "pt-BR"


def _extract_text_simple(content: bytes, filename: str) -> str:
    """Extrai texto simples de documentos para o chat."""
    suffix = filename.lower().split(".")[-1] if "." in filename else ""
    
    if suffix == "pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(content))
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text() or "")
            return "\n".join(text_parts).strip()[:8000]  # Limite de 8000 chars
        except Exception:
            return ""
    
    elif suffix in ["txt", "md", "markdown", "csv", "json", "xml"]:
        return content.decode("utf-8", errors="ignore").strip()[:8000]
    
    elif suffix == "docx":
        try:
            import docx
            doc = docx.Document(io.BytesIO(content))
            text = "\n".join([para.text for para in doc.paragraphs])
            return text.strip()[:8000]
        except Exception:
            return ""
    
    elif suffix in ["xlsx", "xls"]:
        try:
            import pandas as pd
            df = pd.read_excel(io.BytesIO(content))
            return df.to_string(index=False)[:8000]
        except Exception:
            return ""
    
    return ""


def _attachments_context(file_list: List) -> str:
    import io
    lines: List[str] = []
    for f in file_list:
        content_type = (getattr(f, "content_type", "") or "").lower()
        filename = getattr(f, "filename", "arquivo")
        try:
            if content_type.startswith("image/"):
                info = analyze_image_basic(f)
                size = info.get("size", {})
                mean = info.get("mean_rgb", {})
                vision = describe_image_with_vision_llm(f)
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
                # Tentar extrair texto de documentos
                try:
                    f.file.seek(0)
                    content = f.file.read()
                    f.file.seek(0)
                    extracted = _extract_text_simple(content, filename)
                    if extracted:
                        lines.append(f"- documento {filename}:\n```\n{extracted}\n```")
                    else:
                        lines.append(f"- arquivo {filename}: tipo={content_type or 'desconhecido'}")
                except Exception:
                    lines.append(f"- arquivo {filename}: tipo={content_type or 'desconhecido'}")
        except Exception:
            lines.append(f"- arquivo {filename}: não foi possível extrair conteúdo.")
    if not lines:
        return ""
    return "\nContexto dos anexos:\n" + "\n".join(lines)


def _validate_chat_payload(body: dict) -> None:
    """Valida tamanho e estrutura do payload antes de model_validate."""
    messages = body.get("messages") or []
    max_msgs = int(getattr(settings, "chat_max_messages", 48) or 48)
    max_chars = int(getattr(settings, "chat_max_message_chars", 12000) or 12000)
    if len(messages) > max_msgs:
        raise HTTPException(
            status_code=400,
            detail=f"Máximo de {max_msgs} mensagens por requisição.",
        )
    for msg in messages:
        content = (msg.get("content") or "") if isinstance(msg, dict) else (getattr(msg, "content", None) or "")
        if len(content) > max_chars:
            raise HTTPException(
                status_code=400,
                detail=f"Mensagem excede {max_chars} caracteres.",
            )


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
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Pedido inválido.")
        _validate_chat_payload(data)
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
    _validate_chat_payload(body)
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
    v2_conversation_id: Optional[int],
    current_user: Optional[models.User],
    client_ip: str,
):
    ctx_token = set_chat_request_context(
        session_id=sid,
        v2_conversation_id=v2_conversation_id,
        client_ip=client_ip,
    )
    t0 = time.perf_counter()
    full_content: list[str] = []
    last_ping = time.monotonic()
    try:
        for chunk in stream_chat_completion(
            db, request, user=current_user, client_ip=client_ip
        ):
            # Heartbeat SSE para manter proxies/CDN vivos em respostas longas.
            now = time.monotonic()
            if now - last_ping >= 15.0:
                yield ": keep-alive\n\n"
                last_ping = now
            full_content.append(chunk)
            yield f"data: {json.dumps({'content': chunk})}\n\n"
    except Exception:
        _log.exception("Falha no streaming do chat")
        record_chat_error(endpoint="chat_completions_stream", error_type="stream_exception")
        yield f"data: {json.dumps({'content': MSG_TRY_AGAIN_PT})}\n\n"
    finally:
        try:
            if full_content and sid:
                full_text = "".join(full_content)
                prompt_tokens = sum(len((m.content or "").split()) for m in request.messages)
                completion_tokens = len((full_text or "").split())
                record_chat_success(
                    endpoint="chat_completions_stream",
                    latency_ms=(time.perf_counter() - t0) * 1000.0,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                )
                db.add(
                    models.ConversationLog(
                        user_id=current_user.id if current_user else None,
                        session_id=sid,
                        role="assistant",
                        content=full_text,
                    )
                )
                db.commit()
                if v2_conversation_id:
                    persist_assistant_output(
                        db,
                        conversation_id=v2_conversation_id,
                        user_id=current_user.id if current_user else None,
                        content=full_text,
                        model_used=request.model,
                        provider=str(getattr(runtime_llm_engine, "_default", settings.default_llm)),
                        prompt_tokens=None,
                        completion_tokens=len(full_text.split()),
                        total_tokens=None,
                        latency_ms=None,
                    )
                    db.commit()
            if full_content:
                last_u = next((m for m in reversed(request.messages) if m.role == "user"), None)
                preview = (last_u.content or "")[:500] if last_u else ""
                record_stream_chat_completion_audit(
                    db, current_user, preview, "".join(full_content)
                )
        finally:
            reset_chat_request_context(ctx_token)


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
    request.locale = _resolve_locale(
        getattr(request, "locale", None),
        http_request.headers.get("accept-language"),
    )

    # Reconhecimento de pagamento: verificar subscription ativa
    if current_user:
        sub_check = require_subscription(db, current_user, feature="premium_ai")
        if not sub_check["allowed"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": sub_check["error"],
                    "redirect_url": sub_check["redirect_url"],
                    "required_plan": sub_check.get("required_plan"),
                },
            )
    
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
    last_user = next((m for m in reversed(request.messages) if m.role == "user"), None)
    seed_text = (last_user.content if last_user else "") if last_user else ""
    language = detect_language(seed_text)
    subject = detect_subject(seed_text)
    sentiment = detect_sentiment(seed_text)
    v2_session = ensure_v2_session(
        db,
        user_id=current_user.id if current_user else None,
        is_anonymous=current_user is None,
        language=language,
        source="v1/chat/completions",
    )
    v2_conversation = ensure_conversation(
        db,
        session_id=v2_session.id,
        user_id=current_user.id if current_user else None,
        title=(seed_text or "Nova conversa")[:120],
        language=language,
        subject=subject,
        sentiment=sentiment,
    )

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
    persist_input_message_batch(
        db,
        conversation_id=v2_conversation.id,
        user_id=current_user.id if current_user else None,
        messages=request.messages,
    )
    if current_user and seed_text:
        remember_user_preference(
            db,
            user_id=current_user.id,
            key=f"last_topic:{subject}",
            value=seed_text[:2000],
            language=language,
            subject=subject,
            sentiment=sentiment,
        )
    db.commit()

    t0 = time.perf_counter()
    ctx_token = set_chat_request_context(
        session_id=sid,
        v2_conversation_id=v2_conversation.id,
        client_ip=get_client_ip(http_request),
    )
    try:
        response = await asyncio.to_thread(
            create_chat_completion,
            db,
            request,
            current_user,
            get_client_ip(http_request),
        )
    except Exception as exc:
        record_chat_error(endpoint="chat_completions", error_type=type(exc).__name__)
        raise
    finally:
        reset_chat_request_context(ctx_token)

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
        usage = response.usage
        persist_assistant_output(
            db,
            conversation_id=v2_conversation.id,
            user_id=current_user.id if current_user else None,
            content=assistant_msg.content,
            model_used=response.model or request.model,
            provider=str(getattr(runtime_llm_engine, "_default", settings.default_llm)),
            prompt_tokens=usage.prompt_tokens if usage else None,
            completion_tokens=usage.completion_tokens if usage else None,
            total_tokens=usage.total_tokens if usage else None,
            latency_ms=(time.perf_counter() - t0) * 1000.0,
        )
        db.commit()
    usage = response.usage
    record_chat_success(
        endpoint="chat_completions",
        latency_ms=(time.perf_counter() - t0) * 1000.0,
        prompt_tokens=usage.prompt_tokens if usage else 0,
        completion_tokens=usage.completion_tokens if usage else 0,
        total_tokens=usage.total_tokens if usage else 0,
    )

    return response


@router.post("/chat/completions/stream")
async def chat_completions_stream(
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user),
):
    request, _files = await _parse_chat_body(http_request)
    request.locale = _resolve_locale(
        getattr(request, "locale", None),
        http_request.headers.get("accept-language"),
    )

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
    last_user = next((m for m in reversed(request.messages) if m.role == "user"), None)
    seed_text = (last_user.content if last_user else "") if last_user else ""
    language = detect_language(seed_text)
    subject = detect_subject(seed_text)
    sentiment = detect_sentiment(seed_text)
    v2_session = ensure_v2_session(
        db,
        user_id=current_user.id if current_user else None,
        is_anonymous=current_user is None,
        language=language,
        source="v1/chat/completions/stream",
    )
    v2_conversation = ensure_conversation(
        db,
        session_id=v2_session.id,
        user_id=current_user.id if current_user else None,
        title=(seed_text or "Nova conversa")[:120],
        language=language,
        subject=subject,
        sentiment=sentiment,
    )

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
    persist_input_message_batch(
        db,
        conversation_id=v2_conversation.id,
        user_id=current_user.id if current_user else None,
        messages=request.messages,
    )
    if current_user and seed_text:
        remember_user_preference(
            db,
            user_id=current_user.id,
            key=f"last_topic:{subject}",
            value=seed_text[:2000],
            language=language,
            subject=subject,
            sentiment=sentiment,
        )
    db.commit()

    return StreamingResponse(
        _stream_events(
            db,
            request,
            sid,
            v2_conversation.id,
            current_user,
            get_client_ip(http_request),
        ),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

