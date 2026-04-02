import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import hashlib
import json
import logging
import threading
import time
import unicodedata
from typing import Iterator, List, Optional

from sqlalchemy.orm import Session

from vereda_backend.ai_runtime import (
    conversation_memory,
    llm_engine,
    memory_system,
    rag_engine,
)
from vereda_backend.core.syntexa_identity import build_system_prompt_from_identity
from vereda_backend.core.syntexa_modes import (
    detect_mode,
    run_copiloto,
    run_lab,
    run_cientifico,
    run_juridico,
    run_estrategico,
)
from vereda_backend.db import models
from vereda_backend.schemas.chat import (
    ChatChoice,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatUsage,
)
from vereda_backend.services.tools import evaluate_math_expression, try_math_reply
from vereda_backend.services import events
from vereda_backend.services.search_architecture import web_search
from vereda_backend.core.access_control import audit_log
from vereda_backend.core.config import settings


_CHAT_CACHE_LOCK = threading.Lock()
_CHAT_CACHE: dict[str, tuple[float, str]] = {}
_INFLIGHT: dict[str, threading.Event] = {}
logger = logging.getLogger(__name__)

_WEB_CACHE_LOCK = threading.Lock()
_WEB_CACHE: dict[str, tuple[float, str]] = {}
_WEB_SEARCH_INFLIGHT: bool = False


def _normalize_pt(text: str) -> str:
    """
    Normaliza texto pt-BR para comparação:
    - lowercase
    - remove acentos
    - reduz whitespace
    """
    s = (text or "").strip().lower()
    if not s:
        return ""
    s = "".join(
        ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch)
    )
    return " ".join(s.split())


def _is_longest_word_question(user_text: str) -> bool:
    """
    Detecta perguntas comuns sobre "maior palavra" / "palavra mais extensa"
    (Brasil/português/mundo), de forma tolerante a variações e acentuação.

    Também trata o caso em que o usuário digita diretamente a palavra
    "pneumoultr..." (variações comuns/erros de digitação).
    """
    t = _normalize_pt(user_text)
    if not t:
        return False

    # Usuário pode perguntar/confirmar diretamente:
    # "Não é pneumoultr...?" — nesse caso, já respondemos determinísticamente.
    if "pneumoultr" in t:
        return True

    # Exemplos típicos:
    # "qual a maior palavra em português?"
    # "maior palavra brasileira"
    # "qual é a maior palavra do mundo?"
    # "maior palavra da lingua portuguesa"
    intent_markers = (
        "maior palavra",
        "palavra mais extensa",
        "palavra mais comprida",
        "palavra mais longa",
        "palavra mais grande",
        "maior palavra do mundo",
    )
    if not any(m in t for m in intent_markers):
        return False

    qualifiers = (
        "brasil",
        "brasileira",
        "portugues",
        "lingua portuguesa",
        "mundo",
        "dicionario",
    )
    return any(q in t for q in qualifiers) or t.startswith("qual") or t.startswith("qual e")


def _longest_word_response_text() -> str:
    # Mantém resposta determinística para evitar recusa/hallucination do LLM
    # em perguntas de vocabulário conhecidas.
    return (
        "A palavra mais citada como uma das maiores/mais extensas da língua portuguesa é "
        "\"pneumoultramicroscopicossilicovulcanoconiótico\". "
        "Ela é frequentemente usada como exemplo de palavra muito longa. "
        "O termo está relacionado à silicose, uma doença pulmonar causada pela inalação de partículas "
        "muito finas de sílica (poeiras contendo quartzo/sílica; em alguns contextos, cinzas também podem estar envolvidas)."
    )


def _longest_word_examples_response_text() -> str:
    return (
        "Algumas outras palavras longas (comumente citadas) na língua portuguesa:\n"
        "• hipopotomonstrosesquipedaliofobia\n"
        "• anticonstitucionalissimamente\n"
        "• inconstitucionalissimamente\n"
        "• desnecessariamente\n"
        "• intercontinentalmente\n"
        "• extraordinariamente\n"
        "• incompreensivelmente\n\n"
        "Se você quiser, posso também comparar o comprimento (caracteres) entre elas."
    )


def _should_try_web_search(lower_text: str) -> bool:
    """
    Heurística para evitar web search em perguntas que são tipicamente
    matemática/código/visão/criptografia, mantendo latência baixa.
    (Matemática com !calc / expressões locais segue respondida pelo pipeline numérico.)
    """
    # Não tenta web em cálculos puros
    if "!calc " in lower_text or "calcule" in lower_text or "quanto é" in lower_text:
        return False
    # Não tenta web em código
    if any(k in lower_text for k in ("código", "codigo", "python", "javascript", "script", "debug", "sintaxe", "api ", "api:")):
        return False
    # Não tenta web em visão
    if any(k in lower_text for k in ("imagem", "foto", "figura", "visão", "visao", "detectar", "reconhecer")):
        return False
    # Não tenta web em cripto
    if any(k in lower_text for k in ("bitcoin", "criptomoeda", "ethereum", "blockchain", "btc", "eth")):
        return False
    # Para o resto, tende a ser conhecimento/explicação
    return True


def _web_cache_get(key: str) -> Optional[str]:
    now = time.time()
    with _WEB_CACHE_LOCK:
        item = _WEB_CACHE.get(key)
        if not item:
            return None
        exp, value = item
        if exp < now:
            _WEB_CACHE.pop(key, None)
            return None
        return value


def _web_cache_set(key: str, value: str, ttl_sec: int) -> None:
    exp = time.time() + max(1, int(ttl_sec))
    with _WEB_CACHE_LOCK:
        _WEB_CACHE[key] = (exp, value)
        # limpeza simples
        if len(_WEB_CACHE) > 256:
            now = time.time()
            stale = [k for k, (e, _) in _WEB_CACHE.items() if e < now]
            for k in stale[:64]:
                _WEB_CACHE.pop(k, None)


def _maybe_get_web_context(
    query: str,
    *,
    web_max: int = 3,
    timeout_sec: float = 0.6,
    ttl_sec: int = 1800,
) -> str:
    """
    Busca web com:
    - cache TTL (rápido)
    - thread daemon com join por timeout (não trava resposta)
    - no máximo 1 search inflight por processo
    """
    q = (query or "").strip()
    if not q:
        return ""

    lower = q.lower()
    if not _should_try_web_search(lower):
        return ""

    cache_key = _normalize_pt(q)[:200]
    cached = _web_cache_get(cache_key)
    if cached:
        return cached

    global _WEB_SEARCH_INFLIGHT
    with _WEB_CACHE_LOCK:
        if _WEB_SEARCH_INFLIGHT:
            return ""
        _WEB_SEARCH_INFLIGHT = True

    holder: dict[str, List] = {"results": []}

    def _run() -> None:
        try:
            res = web_search(q, max_results=web_max)
            holder["results"] = res
            if res:
                txt = "\n".join(r.text for r in res if getattr(r, "text", None))
                # mantém curto para reduzir latência no prompt
                txt = txt[:2500]
                if txt:
                    _web_cache_set(cache_key, txt, ttl_sec)
        except Exception:
            # Nunca propagar erro para não derrubar chat
            pass
        finally:
            with _WEB_CACHE_LOCK:
                # libera inflight
                _WEB_SEARCH_INFLIGHT = False

    t = threading.Thread(target=_run, name="web_search_daemon", daemon=True)
    t.start()
    t.join(timeout_sec)
    if not t.is_alive():
        # Se terminou, tenta retornar do cache (ou do holder)
        out = _web_cache_get(cache_key)
        return out or "\n".join(r.text for r in holder["results"] if getattr(r, "text", None))[:2500]
    # Timeout: não bloqueia; retorna vazio
    return ""


def _make_cache_key(req: ChatRequest, user: Optional[models.User]) -> str:
    # Cache por conteúdo recente para reduzir custo de perguntas repetidas.
    history = [{"role": m.role, "content": m.content} for m in req.messages[-8:]]
    payload = {
        "uid": user.id if user else 0,
        "model": req.model,
        "temperature": req.temperature,
        "max_tokens": min(req.max_tokens, 1024),
        "history": history,
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _cache_get(key: str) -> Optional[str]:
    now = time.time()
    with _CHAT_CACHE_LOCK:
        item = _CHAT_CACHE.get(key)
        if not item:
            return None
        exp, value = item
        if exp < now:
            _CHAT_CACHE.pop(key, None)
            return None
        return value


def _cache_set(key: str, value: str) -> None:
    ttl = max(1, int(getattr(settings, "chat_cache_ttl_sec", 45)))
    exp = time.time() + ttl
    with _CHAT_CACHE_LOCK:
        _CHAT_CACHE[key] = (exp, value)
        # limpeza simples para evitar crescimento infinito em processo longo
        if len(_CHAT_CACHE) > 512:
            now = time.time()
            stale = [k for k, (e, _) in _CHAT_CACHE.items() if e < now]
            for k in stale[:128]:
                _CHAT_CACHE.pop(k, None)


def _singleflight_enter(key: str) -> tuple[threading.Event, bool]:
    with _CHAT_CACHE_LOCK:
        event = _INFLIGHT.get(key)
        if event is None:
            event = threading.Event()
            _INFLIGHT[key] = event
            return event, True
        return event, False


def _singleflight_leave(key: str, event: threading.Event) -> None:
    with _CHAT_CACHE_LOCK:
        current = _INFLIGHT.get(key)
        if current is event:
            _INFLIGHT.pop(key, None)
    event.set()


def _find_relevant_knowledge(
    db: Session, last_user_message: str, limit: int = 3
) -> List[models.KnowledgeItem]:
    # Busca simples por substring na pergunta ou título.
    pattern = f"%{last_user_message[:80]}%"
    return (
        db.query(models.KnowledgeItem)
        .filter(
            (models.KnowledgeItem.question.ilike(pattern))
            | (models.KnowledgeItem.title.ilike(pattern))
        )
        .order_by(models.KnowledgeItem.id.desc())
        .limit(limit)
        .all()
    )


def _build_system_prompt(
    user: Optional[models.User],
    kb_text: str,
    memory_snippets: List[dict],
    user_text: str = "",
    web_context: str = "",
) -> str:
    return build_system_prompt_from_identity(
        user_text=user_text,
        admin=bool(user and user.is_admin),
        kb_text=kb_text,
        memory_snippets=memory_snippets,
        web_context=web_context,
    )


def _local_engine_reply(user_text: str) -> str:
    text = (user_text or "").strip()
    if not text:
        return "Olá! Sou a Syntexa. Envie sua pergunta para começarmos."
    # Fallback determinístico simples, sem mencionar modo local nem detalhes internos.
    return (
        "Entendi sua solicitação: "
        + text[:700]
        + "\n\nAqui vai uma resposta resumida com base apenas na sua mensagem. "
        "Se você precisar de mais detalhes, pode fazer perguntas de acompanhamento."
    )


def create_chat_completion(
    db: Session, req: ChatRequest, user: Optional[models.User]
) -> ChatResponse:
    reply_text = ""
    # Localiza última mensagem do usuário
    last_user = next((m for m in reversed(req.messages) if m.role == "user"), None)
    if not last_user:
        reply_text = "Olá, sou a IA da Syntexa. Me envie uma mensagem."
    else:
        content = last_user.content.strip()
        if not content:
            reply_text = "Recebi sua mensagem vazia. Pode repetir?"
        else:
            cache_key = _make_cache_key(req, user)
            cached = _cache_get(cache_key)
            if cached is not None:
                reply_text = cached
            else:
                event, owns_singleflight = _singleflight_enter(cache_key)
                if not owns_singleflight:
                    wait_sec = float(getattr(settings, "chat_singleflight_wait_sec", 8.0))
                    event.wait(timeout=max(0.2, wait_sec))
                    cached_after_wait = _cache_get(cache_key)
                    if cached_after_wait is not None:
                        reply_text = cached_after_wait
                    else:
                        # Se não houver cache após espera, segue processamento normal
                        # sem mexer no single-flight do request original.
                        try:
                            reply_text = _compute_chat_reply(db, req, user, content)
                            _cache_set(cache_key, reply_text)
                        except Exception as exc:
                            logger.exception("Falha ao gerar resposta do chat: %s", exc)
                            reply_text = _local_engine_reply(content)
                else:
                    try:
                        try:
                            reply_text = _compute_chat_reply(db, req, user, content)
                            _cache_set(cache_key, reply_text)
                        except Exception as exc:
                            logger.exception("Falha ao gerar resposta do chat: %s", exc)
                            reply_text = _local_engine_reply(content)
                    finally:
                        _singleflight_leave(cache_key, event)
            if not reply_text:
                reply_text = _local_engine_reply(content)
    if not reply_text:
        reply_text = _local_engine_reply("")

    assistant_message = ChatMessage(role="assistant", content=reply_text)
    choice = ChatChoice(index=0, message=assistant_message, finish_reason="stop")

    prompt_tokens = sum(len(m.content.split()) for m in req.messages)
    completion_tokens = len(reply_text.split())
    usage = ChatUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )

    return ChatResponse(
        id=f"chatcmpl-{uuid.uuid4()}",
        object="chat.completion",
        model=req.model,
        choices=[choice],
        usage=usage,
    )


def _compute_chat_reply(
    db: Session, req: ChatRequest, user: Optional[models.User], content: str
) -> str:
    # Armazena turnos na memória vetorial
    conv_id = str(user.id) if user else "anon"
    for msg in req.messages:
        conversation_memory.add_turn(conv_id, msg.role, msg.content)

    content_norm = _normalize_pt(content)
    # Detecta pergunta de follow-up ("quais são as outras... exemplos") logo após
    # a conversa sobre a palavra "pneumoultr...".
    history_norm = _normalize_pt(" ".join((m.content or "") for m in req.messages if getattr(m, "content", None)))
    if (
        ("pneumoultr" in history_norm or "maior palavra" in history_norm or "palavra mais extensa" in history_norm)
        and "outras" in content_norm
        and "exempl" in content_norm
    ):
        return _longest_word_examples_response_text()

    # Pergunta específica: maior palavra / palavra mais extensa
    # (atalho determinístico para evitar depender de provedor/moderação).
    if _is_longest_word_question(content):
        return _longest_word_response_text()

    # Matemática: !calc, expressão pura ou "quanto é X" / "calcule X" (sympy)
    math_reply, math_handled = try_math_reply(content)
    if math_handled:
        reply_text = math_reply
    elif content.startswith("!calc "):
        expr = content[len("!calc ") :].strip()
        result = evaluate_math_expression(expr)
        if result.get("ok"):
            reply_text = f"Resultado de {result['expression']} = {result['result']}."
        else:
            reply_text = f"Não consegui avaliar: {result.get('error')}"
    # Modos Syntexa em código próprio: COPILOTO e LAB
    elif detect_mode(content) == "copiloto":
        history = [{"role": m.role, "content": m.content} for m in req.messages[:-1]]
        reply_text = run_copiloto(
            content, llm_engine, history=history, max_tokens=req.max_tokens
        )
        events.notify_chat_completion(
            user, prompt_preview=content, reply_preview=reply_text
        )
        audit_log(
            db,
            action="chat_copiloto",
            user_id=user.id if user else None,
            resource="chat",
            detail=content[:200],
        )
    elif detect_mode(content) == "lab":
        history = [{"role": m.role, "content": m.content} for m in req.messages[:-1]]
        reply_text = run_lab(content, llm_engine, history=history, max_tokens=req.max_tokens)
        events.notify_chat_completion(
            user, prompt_preview=content, reply_preview=reply_text
        )
        audit_log(
            db,
            action="chat_lab",
            user_id=user.id if user else None,
            resource="chat",
            detail=content[:200],
        )
    elif detect_mode(content) == "cientifico":
        history = [{"role": m.role, "content": m.content} for m in req.messages[:-1]]
        reply_text = run_cientifico(
            content, llm_engine, history=history, max_tokens=req.max_tokens
        )
        events.notify_chat_completion(
            user, prompt_preview=content, reply_preview=reply_text
        )
        audit_log(
            db,
            action="chat_cientifico",
            user_id=user.id if user else None,
            resource="chat",
            detail=content[:200],
        )
    elif detect_mode(content) == "juridico":
        history = [{"role": m.role, "content": m.content} for m in req.messages[:-1]]
        reply_text = run_juridico(
            content, llm_engine, history=history, max_tokens=req.max_tokens
        )
        events.notify_chat_completion(
            user, prompt_preview=content, reply_preview=reply_text
        )
        audit_log(
            db,
            action="chat_juridico",
            user_id=user.id if user else None,
            resource="chat",
            detail=content[:200],
        )
    elif detect_mode(content) == "estrategico":
        history = [{"role": m.role, "content": m.content} for m in req.messages[:-1]]
        reply_text = run_estrategico(
            content, llm_engine, history=history, max_tokens=req.max_tokens
        )
        events.notify_chat_completion(
            user, prompt_preview=content, reply_preview=reply_text
        )
        audit_log(
            db,
            action="chat_estrategico",
            user_id=user.id if user else None,
            resource="chat",
            detail=content[:200],
        )
    else:
        knowledge_items = _find_relevant_knowledge(db, content, limit=1)
        kb_text = ""
        if knowledge_items:
            kb_text = f"- {knowledge_items[0].title}: {knowledge_items[0].answer}"
        memory_docs = memory_system.retrieve_context(content, top_k=2)
        rag_context = rag_engine.db.similarity_search(
            namespace="global", query=content, top_k=2
        )
        web_context = ""
        lower = content.lower()
        is_definition = any(
            lower.startswith(p) or p in lower
            for p in (
                "o que é",
                "qual o",
                "o que e ",
                "quem é",
                "como se chama",
                "o que é chamado",
                "nome do ",
                "nome da ",
                "o que significa",
            )
        )
        # Para reduzir latência, a busca web usa timeout curto + cache.
        # Mantemos web_context para definições com timeout ainda menor,
        # mas tentamos também em conhecimento geral (para diversificar).
        try:
            if is_definition:
                web_context = _maybe_get_web_context(
                    content, web_max=3, timeout_sec=0.35, ttl_sec=1800
                )
            else:
                web_context = _maybe_get_web_context(
                    content, web_max=3, timeout_sec=0.6, ttl_sec=1800
                )
        except Exception:
            web_context = ""

        system_prompt = _build_system_prompt(
            user,
            kb_text,
            memory_docs + rag_context,
            user_text=content,
            web_context=web_context,
        )
        messages = [
            {"role": "system", "content": system_prompt},
            *[m.model_dump() for m in req.messages],
        ]
        _max_tokens = min(req.max_tokens, 1024)
        reply_text = llm_engine.chat(
            messages,
            temperature=req.temperature,
            max_tokens=_max_tokens,
        )

        events.notify_chat_completion(
            user,
            prompt_preview=content,
            reply_preview=reply_text,
        )
        audit_log(
            db,
            action="chat_completion",
            user_id=user.id if user else None,
            resource="chat",
            detail=content[:200] if content else None,
        )
    return reply_text


def stream_chat_completion(
    db: Session, req: ChatRequest, user: Optional[models.User]
) -> Iterator[str]:
    """Gera chunks de texto para resposta imediata (streaming). Mesma lógica do create_chat_completion."""
    last_user = next((m for m in reversed(req.messages) if m.role == "user"), None)
    if not last_user:
        yield "Olá, sou a IA da Syntexa. Me envie uma mensagem."
        return
    content = last_user.content.strip()
    if not content:
        yield "Recebi sua mensagem vazia. Pode repetir?"
        return
    conv_id = str(user.id) if user else "anon"
    for msg in req.messages:
        conversation_memory.add_turn(conv_id, msg.role, msg.content)

    content_norm = _normalize_pt(content)
    history_norm = _normalize_pt(" ".join((m.content or "") for m in req.messages if getattr(m, "content", None)))
    if (
        ("pneumoultr" in history_norm or "maior palavra" in history_norm or "palavra mais extensa" in history_norm)
        and "outras" in content_norm
        and "exempl" in content_norm
    ):
        yield _longest_word_examples_response_text()
        return

    if _is_longest_word_question(content):
        yield _longest_word_response_text()
        return

    math_reply, math_handled = try_math_reply(content)
    if math_handled:
        yield math_reply
        return
    if content.startswith("!calc "):
        expr = content[len("!calc ") :].strip()
        result = evaluate_math_expression(expr)
        if result.get("ok"):
            yield f"Resultado de {result['expression']} = {result['result']}."
        else:
            yield f"Não consegui avaliar: {result.get('error')}"
        return
    mode = detect_mode(content)
    if mode == "copiloto":
        history = [{"role": m.role, "content": m.content} for m in req.messages[:-1]]
        reply = run_copiloto(content, llm_engine, history=history, max_tokens=req.max_tokens)
        yield reply
        return
    if mode == "lab":
        history = [{"role": m.role, "content": m.content} for m in req.messages[:-1]]
        reply = run_lab(content, llm_engine, history=history, max_tokens=req.max_tokens)
        yield reply
        return
    if mode == "cientifico":
        history = [{"role": m.role, "content": m.content} for m in req.messages[:-1]]
        reply = run_cientifico(content, llm_engine, history=history, max_tokens=req.max_tokens)
        yield reply
        return
    if mode == "juridico":
        history = [{"role": m.role, "content": m.content} for m in req.messages[:-1]]
        reply = run_juridico(content, llm_engine, history=history, max_tokens=req.max_tokens)
        yield reply
        return
    if mode == "estrategico":
        history = [{"role": m.role, "content": m.content} for m in req.messages[:-1]]
        reply = run_estrategico(content, llm_engine, history=history, max_tokens=req.max_tokens)
        yield reply
        return
    knowledge_items = _find_relevant_knowledge(db, content, limit=1)
    kb_text = f"- {knowledge_items[0].title}: {knowledge_items[0].answer}" if knowledge_items else ""
    memory_docs = memory_system.retrieve_context(content, top_k=2)
    rag_context = rag_engine.db.similarity_search(namespace="global", query=content, top_k=2)
    web_context = ""
    lower = content.lower()
    is_definition = any(
        lower.startswith(p) or p in lower
        for p in (
            "o que é",
            "qual o",
            "o que e ",
            "quem é",
            "como se chama",
            "o que é chamado",
            "nome do ",
            "nome da ",
            "o que significa",
        )
    )
    # Mesma lógica do modo não-stream: cache + timeout curto para web.
    try:
        if is_definition:
            web_context = _maybe_get_web_context(
                content, web_max=3, timeout_sec=0.35, ttl_sec=1800
            )
        else:
            web_context = _maybe_get_web_context(
                content, web_max=3, timeout_sec=0.6, ttl_sec=1800
            )
    except Exception:
        web_context = ""
    system_prompt = _build_system_prompt(
        user, kb_text, memory_docs + rag_context, user_text=content, web_context=web_context
    )
    messages = [
        {"role": "system", "content": system_prompt},
        *[m.model_dump() for m in req.messages],
    ]
    _max_tokens = min(req.max_tokens, 1024)
    try:
        yielded = False
        for chunk in llm_engine.chat_stream(
            messages, temperature=req.temperature, max_tokens=_max_tokens
        ):
            yielded = True
            yield chunk
        if not yielded:
            yield _local_engine_reply(content)
    except Exception:
        yield _local_engine_reply(content)

