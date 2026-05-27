import json
import hashlib
import logging
import time
from datetime import datetime
from typing import Generator, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from vereda_backend.db import models
from vereda_backend.db.session import get_db
from vereda_backend.schemas.chat import (
    ChatChoice,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatUsage,
)
from vereda_backend.core.security import get_current_user_optional
from vereda_backend.services.chat_engine import create_chat_completion, stream_chat_completion
from vereda_backend.services.conversation_store import (
    ensure_conversation,
    ensure_v2_session,
    persist_assistant_output,
    persist_input_message_batch,
)
from vereda_backend.core.syntexa_intel import detect_language, detect_sentiment, detect_subject
from vereda_backend.core.syntexa_intel import remember_user_preference
from vereda_backend.core.config import settings
from vereda_backend.services.media_engine import (
    analyze_video_basic,
    describe_image_with_vision_llm,
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
                lines.append(f"- arquivo {filename}: tipo={content_type or 'desconhecido'}.")
        except Exception:
            lines.append(f"- arquivo {filename}: não foi possível extrair metadados.")
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
    req = ChatRequest.model_validate(body)
    return req, []


async def _public_chat_impl(
    http_request: Request,
    db: Session,
    optional_user: Optional[models.User] = None,
) -> ChatResponse:
    """Implementação compartilhada para /api/public-chat e /v1/public-chat."""
    from vereda_backend.core.config import settings
    ip = _client_ip(http_request)
    check_public_chat_tier(
        ip,
        optional_user,
        detail="Limite diário de mensagens atingido. Aguarde ou use uma conta com plano adequado.",
    )
    request, _files = await _parse_public_chat_body(http_request)

    # Gateway mode: usar apenas proxy para AI Worker local/soberano.
    # PROIBIDO fallback para OpenAI/Claude/Groq (V38).
    if getattr(settings, "gateway_mode", False):
        try:
            from vereda_backend.core.ai_proxy_client import proxy_chat_completion_sync
            messages = [m.model_dump() for m in request.messages]
            result = proxy_chat_completion_sync(
                messages=messages,
                model=request.model,
                stream=False,
                temperature=0.7,
                max_tokens=min(request.max_tokens or 2048, 4096),
            )
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not content:
                content = result.get("content", "")
            if content:
                return ChatResponse(
                    id="chatcmpl-gateway-proxy",
                    object="chat.completion",
                    model=request.model,
                    choices=[
                        ChatChoice(
                            index=0,
                            message=ChatMessage(role="assistant", content=content),
                            finish_reason="stop",
                        )
                    ],
                    usage=ChatUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
                )
        except Exception as exc:
            logger.warning("[Syntexa V38] Gateway AI Worker falhou: %s — fallthrough para engine local", exc)

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
    last_user = next((m for m in reversed(request.messages) if m.role == "user"), None)
    seed_text = (last_user.content if last_user else "") if last_user else ""
    language = detect_language(seed_text)
    subject = detect_subject(seed_text)
    sentiment = detect_sentiment(seed_text)
    v2_session = ensure_v2_session(
        db,
        user_id=optional_user.id if optional_user else None,
        is_anonymous=optional_user is None,
        language=language,
        source="public-chat",
    )
    v2_conversation = ensure_conversation(
        db,
        session_id=v2_session.id,
        user_id=optional_user.id if optional_user else None,
        title=(seed_text or session_title)[:120],
        language=language,
        subject=subject,
        sentiment=sentiment,
    )
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
    persist_input_message_batch(
        db,
        conversation_id=v2_conversation.id,
        user_id=optional_user.id if optional_user else None,
        messages=request.messages,
    )
    if optional_user and seed_text:
        remember_user_preference(
            db,
            user_id=optional_user.id,
            key=f"last_topic:{subject}",
            value=seed_text[:2000],
            language=language,
            subject=subject,
            sentiment=sentiment,
        )
    db.commit()
    retries = 4
    backoff_s = 0.5
    response = None
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            response = create_chat_completion(
                db=db,
                req=request,
                user=optional_user,
                client_ip=_client_ip(http_request),
            )
            break
        except Exception as exc:
            last_exc = exc
            if attempt >= retries - 1:
                logger.exception("[Syntexa V38] Erro interno em public-chat: %s", exc)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="[Syntexa V38] Inference runtime indisponível. Verifique o estado do motor LLM local.",
                )
            logger.warning(
                "[Syntexa V38] Falha transitória public-chat (tentativa %s/%s): %s",
                attempt + 1,
                retries,
                exc,
            )
            time.sleep(backoff_s * (2**attempt))
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="[Syntexa V38] Inference runtime indisponível. Verifique o estado do motor LLM local.",
        )
    if response.choices:
        usage = response.usage
        db.add(
            models.ConversationLog(
                user_id=None,
                session_id=sid,
                role="assistant",
                content=response.choices[0].message.content,
            )
        )
        persist_assistant_output(
            db,
            conversation_id=v2_conversation.id,
            user_id=optional_user.id if optional_user else None,
            content=response.choices[0].message.content,
            model_used=response.model or request.model,
            provider="ollama" if "ollama" in request.model.lower() else "syntexa",
            prompt_tokens=usage.prompt_tokens if usage else None,
            completion_tokens=usage.completion_tokens if usage else None,
            total_tokens=usage.total_tokens if usage else None,
            latency_ms=None,
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
    v2_conversation_id: Optional[int] = None,
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
            if v2_conversation_id:
                persist_assistant_output(
                    db,
                    conversation_id=v2_conversation_id,
                    user_id=optional_user.id if optional_user else None,
                    content=full_text,
                    model_used=request.model,
                    provider="ollama" if "ollama" in request.model.lower() else "syntexa",
                    prompt_tokens=None,
                    completion_tokens=len(full_text.split()),
                    total_tokens=None,
                    latency_ms=None,
                )
            db.commit()


def _gateway_stream_stub():
    """
    PROIBIDO retornar placeholder hardcoded (V38).
    Levanta erro real para que o frontend exiba status técnico.
    """
    raise RuntimeError(
        "[Syntexa V38] Gateway stream stub invocado — nenhum runtime LLM real respondeu. "
        "Verifique disponibilidade do motor de inferência local."
    )


async def _public_chat_stream_impl(
    http_request: Request,
    db: Session,
    optional_user: Optional[models.User] = None,
):
    """Stream compartilhado para /api/public-chat/stream e /v1/public-chat/stream."""
    from vereda_backend.core.config import settings
    ip = _client_ip(http_request)
    check_public_chat_tier(
        ip,
        optional_user,
        detail="Limite diário de mensagens atingido. Aguarde ou use uma conta com plano adequado.",
    )
    request, _ = await _parse_public_chat_body(http_request)

    # Gateway mode: usar apenas proxy para AI Worker local/soberano.
    # PROIBIDO fallback para OpenAI/Claude/Groq (V38).
    if getattr(settings, "gateway_mode", False):
        try:
            from vereda_backend.core.ai_proxy_client import proxy_chat_completion_async
            messages = [m.model_dump() for m in request.messages]
            result = await proxy_chat_completion_async(
                messages=messages,
                model=request.model,
                stream=False,
                temperature=0.7,
                max_tokens=min(request.max_tokens or 2048, 4096),
            )
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not content:
                content = result.get("content", "")
            if content:
                async def _proxy_stream(content):
                    import json
                    for word in content.split():
                        yield f"data: {json.dumps({'content': word + ' '})}\n\n"
                    yield f"data: {json.dumps({'content': ''})}\n\n"
                return StreamingResponse(
                    _proxy_stream(content),
                    media_type="text/event-stream; charset=utf-8",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "X-Accel-Buffering": "no",
                    },
                )
        except Exception as exc:
            logger.warning("[Syntexa V38] Gateway AI Worker stream falhou: %s — fallthrough para engine local", exc)

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
    last_user = next((m for m in reversed(request.messages) if m.role == "user"), None)
    seed_text = (last_user.content if last_user else "") if last_user else ""
    language = detect_language(seed_text)
    subject = detect_subject(seed_text)
    sentiment = detect_sentiment(seed_text)
    v2_session = ensure_v2_session(
        db,
        user_id=optional_user.id if optional_user else None,
        is_anonymous=optional_user is None,
        language=language,
        source="public-chat/stream",
    )
    v2_conversation = ensure_conversation(
        db,
        session_id=v2_session.id,
        user_id=optional_user.id if optional_user else None,
        title=(seed_text or session_title)[:120],
        language=language,
        subject=subject,
        sentiment=sentiment,
    )
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
    persist_input_message_batch(
        db,
        conversation_id=v2_conversation.id,
        user_id=optional_user.id if optional_user else None,
        messages=request.messages,
    )
    if optional_user and seed_text:
        remember_user_preference(
            db,
            user_id=optional_user.id,
            key=f"last_topic:{subject}",
            value=seed_text[:2000],
            language=language,
            subject=subject,
            sentiment=sentiment,
        )
    db.commit()
    return StreamingResponse(
        _stream_events(db, request, sid, optional_user, ip, v2_conversation.id),
        media_type="text/event-stream; charset=utf-8",
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

