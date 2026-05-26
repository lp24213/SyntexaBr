import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import hashlib
import json
import logging
import threading
import time
import unicodedata
from typing import Any, Iterator, List, Optional

from sqlalchemy.orm import Session

from vereda_backend.ai_runtime import (
    conversation_memory,
    llm_engine,
    memory_system,
    rag_engine,
)
from vereda_backend.core.deep_run import user_requests_deep_answer
from vereda_backend.core.query_profile import analyze_query_profile, build_profile_directives
from vereda_backend.core.syntexa_identity import build_system_prompt_from_identity
from vereda_backend.core.syntexa_modes import (
    detect_mode,
    infer_auto_mode,
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
from vereda_backend.services.conversation_store import semantic_context_for_user
from vereda_backend.core.answer_engine import build_augmented_web_context, confidence_prompt_line
from vereda_backend.core.access_control import audit_log
from vereda_backend.core.chat_context import get_chat_request_context
from vereda_backend.core.chat_policy import get_policy_snapshot
from vereda_backend.core.config import settings
from vereda_backend.core.llm_message_adapter import adapt_messages_for_llm_provider
from vereda_backend.core.cache_redis import (
    cache_get as redis_cache_get,
    cache_set as redis_cache_set,
    shared_question_cache_get,
    shared_question_cache_set,
)
from vereda_backend.core.text_sanitize import fix_text_encoding, sanitize_for_stream
from vereda_backend.core.cognitive_layer import CognitiveContext, cognitive_refine


_CHAT_CACHE_LOCK = threading.Lock()
_CHAT_CACHE: dict[str, tuple[float, str]] = {}
_INFLIGHT: dict[str, threading.Event] = {}
logger = logging.getLogger(__name__)
_RUNTIME_ALERT_LOCK = threading.Lock()
_LAST_RUNTIME_ALERT_AT = 0.0


def _is_english_locale(locale: Optional[str]) -> bool:
    return str(locale or "").lower().startswith("en")


def _localized_text(locale: Optional[str], pt: str, en: str) -> str:
    return en if _is_english_locale(locale) else pt


def _locale_instruction(locale: Optional[str]) -> str:
    return _localized_text(
        locale,
        "Responda em português do Brasil (pt-BR), com tom claro e prático.",
        "Respond in English (en-US), with a clear and practical tone.",
    )


def _chat_with_retry(
    messages: list[dict[str, Any]],
    *,
    temperature: float,
    max_tokens: int,
    domain: str | None = None,
) -> str:
    retries = max(1, int(getattr(settings, "chat_llm_retries", 4) or 4))
    backoff_base = max(0.05, float(getattr(settings, "chat_llm_retry_backoff_sec", 0.5) or 0.5))
    last_exc: Exception | None = None
    prov_name = str(getattr(llm_engine, "_default", "syntexa_native"))
    adapted = adapt_messages_for_llm_provider(messages, prov_name)
    for attempt in range(retries):
        try:
            out = llm_engine.chat(
                adapted,
                temperature=temperature,
                max_tokens=max_tokens,
                domain=domain,
            )
            if not str(out or "").strip():
                raise RuntimeError("[Syntexa V45] Resposta vazia do provedor LLM.")
            return str(out)
        except Exception as exc:
            last_exc = exc
            if attempt >= retries - 1:
                raise RuntimeError(
                    f"[Syntexa V45] Inferência falhou após {retries} tentativas. "
                    f"Último erro: {type(exc).__name__}: {exc}"
                ) from exc
            sleep_s = backoff_base * (2 ** attempt)
            logger.warning(
                "Falha LLM (tentativa %s/%s), retry em %.2fs: %s",
                attempt + 1,
                retries,
                sleep_s,
                exc,
            )
            time.sleep(sleep_s)
    if last_exc:
        raise RuntimeError(
            f"[Syntexa V45] Falha persistente no LLM: {type(last_exc).__name__}: {last_exc}"
        ) from last_exc
    raise RuntimeError("[Syntexa V45] Falha inesperada no retry do LLM")


def _maybe_alert_runtime_failure(user: Optional[models.User], exc: Exception) -> None:
    global _LAST_RUNTIME_ALERT_AT
    env = str(getattr(settings, "environment", "") or "").lower()
    strict = bool(getattr(settings, "chat_strict_real_providers", True))
    if env not in {"prod", "production"} or not strict:
        return
    now = time.time()
    cooldown = max(30.0, float(getattr(settings, "chat_runtime_alert_cooldown_sec", 120.0) or 120.0))
    with _RUNTIME_ALERT_LOCK:
        if now - _LAST_RUNTIME_ALERT_AT < cooldown:
            return
        _LAST_RUNTIME_ALERT_AT = now
    events.notify_chat_runtime_unavailable(
        error_text=str(exc),
        user=user,
        provider=str(getattr(settings, "default_llm", "unknown")),
    )


def _normalize_for_dedup(text: str) -> str:
    s = (text or "").strip().lower()
    s = "".join(
        ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch)
    )
    return " ".join(s.split())


def _trim_messages(
    messages: List[ChatMessage], *, max_messages: int, max_chars: int
) -> List[ChatMessage]:
    max_messages = max(2, max_messages)
    slice_msgs = messages[-max_messages:] if len(messages) > max_messages else messages
    out: List[ChatMessage] = []
    for m in slice_msgs:
        c = m.content or ""
        if len(c) > max_chars:
            c = c[:max_chars] + "\n…"
        data = m.model_dump()
        data["content"] = c
        out.append(ChatMessage.model_validate(data))
    return out


def _last_user_text_for_budget(req: ChatRequest) -> str:
    for m in reversed(req.messages):
        if (m.role or "").lower() == "user":
            return (m.content or "").strip()
    return ""


def _llm_output_cap_tokens(*, deep_run: bool) -> int:
    base = max(256, int(getattr(settings, "chat_max_model_tokens", 8192) or 8192))
    if not deep_run:
        return base
    dr = int(getattr(settings, "chat_deep_run_max_model_tokens", 0) or 0)
    if dr <= 0:
        return base
    return max(base, max(256, dr))


def _llm_output_cap_tokens_for_user(*, deep_run: bool, user: Optional[models.User]) -> int:
    """
    Admin: libera teto maior (sem corte artificial), mas ainda respeita limites do modelo real.
    """
    if user and bool(getattr(user, "is_admin", False)):
        base = max(256, int(getattr(settings, "chat_max_model_tokens_admin", 16384) or 16384))
        if not deep_run:
            return base
        dr = int(getattr(settings, "chat_deep_run_max_model_tokens", 0) or 0)
        return max(base, max(256, dr)) if dr > 0 else base
    return _llm_output_cap_tokens(deep_run=deep_run)


def _effective_chat_temperature(req: ChatRequest, *, deep_run: bool) -> float:
    """Temperatura enviada ao LLM; em deep_run reduz variância para aproximar respostas longas estáveis."""
    t = float(req.temperature)
    t = max(0.0, min(2.0, t))
    if not deep_run:
        return t
    if not bool(getattr(settings, "chat_deep_run_temperature_adjust_enabled", True)):
        return t
    cap = float(getattr(settings, "chat_deep_run_temperature_cap", 0.62) or 0.62)
    cap = max(0.0, min(2.0, cap))
    return min(t, cap)


def _effective_mode(content: str) -> Optional[str]:
    explicit = detect_mode(content)
    if explicit:
        return explicit
    if not bool(getattr(settings, "chat_auto_domain_modes_enabled", True)):
        return None
    return infer_auto_mode(content)


def _retrieval_knobs_for_message(content: str) -> dict[str, int | float | bool]:
    """KB / memória / RAG / web / semântico — reforço só quando `user_requests_deep_answer`."""
    deep = user_requests_deep_answer(content)
    mem_k = max(1, int(getattr(settings, "chat_memory_top_k", 1) or 1))
    rag_k = max(1, int(getattr(settings, "chat_rag_top_k", 1) or 1))
    kb_limit = 1
    web_def, web_gen = 8, 10
    semantic_k = 3
    web_timeout_extra = 0.0
    if deep:
        kb_limit = max(
            1,
            min(8, int(getattr(settings, "chat_deep_run_knowledge_limit", 3) or 3)),
        )
        mem_k += max(0, int(getattr(settings, "chat_deep_run_memory_top_k_extra", 0) or 0))
        rag_k += max(0, int(getattr(settings, "chat_deep_run_rag_top_k_extra", 0) or 0))
        extra_wm = max(0, int(getattr(settings, "chat_deep_run_web_max_extra", 0) or 0))
        web_def = min(24, 8 + extra_wm)
        web_gen = min(28, 10 + extra_wm)
        semantic_k = min(
            12,
            3 + max(0, int(getattr(settings, "chat_deep_run_semantic_top_k_extra", 0) or 0)),
        )
        web_timeout_extra = float(
            getattr(settings, "chat_deep_run_web_timeout_extra_sec", 0.0) or 0.0
        )
    return {
        "deep": deep,
        "kb_limit": kb_limit,
        "mem_k": mem_k,
        "rag_k": rag_k,
        "web_max_def": web_def,
        "web_max_gen": web_gen,
        "semantic_k": semantic_k,
        "web_timeout_extra": web_timeout_extra,
    }


def prepare_chat_request(
    req: ChatRequest,
    stress_scale: float = 1.0,
    user: Optional[models.User] = None,
) -> ChatRequest:
    """
    Orçamento fixo de contexto/saída: menos tokens por requisição = mais throughput no mesmo hardware.
    stress_scale < 1 encurta respostas sob carga (Fase 3).
    """
    stress_scale = max(
        float(getattr(settings, "load_degrade_scale_min", 0.52) or 0.52),
        min(1.0, float(stress_scale)),
    )
    max_msg = max(4, int(getattr(settings, "chat_max_messages", 12) or 12))
    if user and bool(getattr(user, "is_admin", False)):
        admin_floor = int(getattr(settings, "chat_max_messages_admin_floor", 36) or 36)
        max_msg = max(max_msg, admin_floor)
    max_msg = max(3, int(max_msg * (0.72 + 0.28 * stress_scale)))
    max_chars = max(500, int(getattr(settings, "chat_max_message_chars", 6000) or 6000))
    max_chars = int(max(400, max_chars * (0.78 + 0.22 * stress_scale)))
    last_u = _last_user_text_for_budget(req)
    deep_run = bool(last_u) and user_requests_deep_answer(last_u)
    if deep_run:
        dr_mc = int(getattr(settings, "chat_deep_run_message_chars_extra", 0) or 0)
        if dr_mc > 0:
            max_chars = min(96000, max_chars + dr_mc)
    cap_long = int(getattr(settings, "chat_max_output_tokens_long", 8192) or 8192)
    if user and bool(getattr(user, "is_admin", False)):
        cap_long = max(cap_long, int(getattr(settings, "chat_max_output_tokens_admin", 16384) or 16384))
    if deep_run:
        dr_cap = int(getattr(settings, "chat_deep_run_max_output_tokens", 0) or 0)
        if dr_cap > 0:
            cap_long = max(cap_long, dr_cap)
    incoming = max(1, int(req.max_tokens))
    # Pedidos com teto 1024 (schema antigo / clientes em cache) — evita resposta cortada no meio.
    floor_out = min(
        cap_long,
        int(getattr(settings, "chat_max_output_tokens_default", 4096) or 4096),
    )
    if incoming <= 1024:
        incoming = max(incoming, floor_out)
    # Não multiplicar max_tokens por stress_scale — isso cortava respostas longas em produção.
    mt = min(incoming, cap_long)
    mt = max(256, mt)
    if deep_run:
        dr_min = int(getattr(settings, "chat_deep_run_min_output_tokens", 0) or 0)
        if dr_min > 0:
            dr_min = max(256, min(dr_min, cap_long))
            mt = max(mt, dr_min)
    trimmed = _trim_messages(req.messages, max_messages=max_msg, max_chars=max_chars)
    from vereda_backend.core.context_budget import (
        context_token_budget_for_user,
        trim_chat_messages_by_approx_tokens,
    )

    budget = context_token_budget_for_user(user)
    if deep_run:
        extra = int(getattr(settings, "chat_deep_run_context_extra_tokens", 0) or 0)
        if extra > 0:
            budget = budget + extra
    trimmed = trim_chat_messages_by_approx_tokens(trimmed, budget)
    return req.model_copy(update={"messages": trimmed, "max_tokens": mt})


def _shared_question_digest(content: str, model: str, temperature: float) -> str:
    n = _normalize_for_dedup(content)
    raw = f"{n}|{model}|{round(float(temperature), 2)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


_WEB_CACHE_LOCK = threading.Lock()
_WEB_CACHE: dict[str, tuple[float, str]] = {}


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
    """Quase sempre pesquisa fontes públicas; só evita comando local !calc (já tratado antes)."""
    if lower_text.strip().startswith("!calc "):
        return False
    return bool(lower_text.strip())


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


def _maybe_get_web_bundle(
    query: str,
    *,
    web_max: int = 8,
    timeout_sec: float | None = None,
    timeout_extra_sec: float = 0.0,
    ttl_sec: int = 1800,
) -> tuple[str, str, str]:
    """
    Agrega fontes públicas (DDG/Wikipedia/notícias/CSE opcional) com timeout real.
    Resultado alimenta o núcleo Syntexa via prompt de sistema — sem APIs de LLM de terceiros.
    """
    q = (query or "").strip()
    if not q:
        return "", "", ""

    lower = q.lower()
    if not _should_try_web_search(lower):
        return "", "", ""

    if timeout_sec is None:
        timeout_sec = float(getattr(settings, "chat_web_search_timeout_sec", 22.0) or 22.0)
    timeout_sec = max(
        3.0, min(90.0, float(timeout_sec) + max(0.0, float(timeout_extra_sec or 0.0)))
    )

    cache_key = _normalize_pt(q)[:200]
    cached = _web_cache_get(cache_key)
    if cached:
        try:
            data = json.loads(cached)
            if isinstance(data, list) and len(data) == 3:
                return str(data[0] or ""), str(data[1] or ""), str(data[2] or "")
        except Exception:
            pass

    def _run_search() -> tuple[str, str, str]:
        aug = build_augmented_web_context(q, max_results=web_max)
        conf_line = confidence_prompt_line(aug.confidence, aug.confidence_note, aug.topic)
        slice_cap = 14000 if int(web_max) >= 14 else 8000
        return (aug.web_text or "")[:slice_cap], aug.citations_block or "", conf_line or ""

    try:
        with ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(_run_search)
            web_t, cit, cl = fut.result(timeout=timeout_sec)
    except Exception as exc:
        logger.warning("Busca web indisponível ou timeout (%s): %s", timeout_sec, exc)
        return "", "", ""

    if web_t or cit:
        try:
            _web_cache_set(
                cache_key,
                json.dumps([web_t, cit, cl], ensure_ascii=False),
                ttl_sec,
            )
        except Exception:
            pass
    return web_t, cit, cl


def _make_cache_key(req: ChatRequest, user: Optional[models.User]) -> str:
    # Cache por conteúdo recente para reduzir custo de perguntas repetidas.
    history = [{"role": m.role, "content": m.content} for m in req.messages[-8:]]
    payload = {
        "uid": user.id if user else 0,
        "model": req.model,
        "temperature": req.temperature,
        "max_tokens": min(req.max_tokens, 8192),
        "history": history,
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _cache_get(key: str) -> Optional[str]:
    now = time.time()
    with _CHAT_CACHE_LOCK:
        item = _CHAT_CACHE.get(key)
        if item:
            exp, value = item
            if exp >= now:
                return value
            _CHAT_CACHE.pop(key, None)
    rv = redis_cache_get(key)
    if rv is not None:
        ttl = max(1, int(getattr(settings, "redis_chat_cache_ttl_sec", 120) or 120))
        exp = time.time() + ttl
        with _CHAT_CACHE_LOCK:
            _CHAT_CACHE[key] = (exp, rv)
    return rv


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
    redis_ttl = int(getattr(settings, "redis_chat_cache_ttl_sec", 120) or 120)
    redis_cache_set(key, value, ttl_sec=redis_ttl)


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


def _audit_chat_resource() -> str:
    ctx = get_chat_request_context()
    sid = ctx.get("session_id")
    if sid is not None:
        return f"chat_session:{int(sid)}"
    return "chat"


def _audit_chat_detail(*, preview: str, **extra: Any) -> str:
    ctx = get_chat_request_context()
    snap = get_policy_snapshot()
    body: dict[str, Any] = {
        "session_id": ctx.get("session_id"),
        "v2_conversation_id": ctx.get("v2_conversation_id"),
        "policy_version": snap.get("policy_version"),
        "policy_sha256_prefix": str(snap.get("policy_sha256", ""))[:48],
        "policy_profile": snap.get("policy_profile"),
        "preview": (preview or "")[:500],
    }
    for k, v in extra.items():
        if v is not None:
            body[k] = v
    return json.dumps(body, ensure_ascii=False)[:1900]


def _audit_admin_chat_if_needed(db: Session, user: Optional[models.User], content: str) -> None:
    if not user or not bool(getattr(user, "is_admin", False)):
        return
    try:
        audit_log(
            db,
            action="chat_admin_request",
            user_id=user.id,
            resource=_audit_chat_resource(),
            detail=_audit_chat_detail(preview=content or ""),
            ip_address=get_chat_request_context().get("client_ip"),
        )
    except Exception:
        pass


def _build_system_prompt(
    user: Optional[models.User],
    kb_text: str,
    memory_snippets: List[dict],
    user_text: str = "",
    web_context: str = "",
    citations_block: str = "",
    confidence_line: str = "",
    profile_directives: str = "",
) -> str:
    access_tier = "public"
    if user and bool(getattr(user, "is_admin", False)):
        access_tier = "admin"
    elif user:
        access_tier = "authenticated"
    return build_system_prompt_from_identity(
        user_text=user_text,
        admin=bool(user and user.is_admin),
        access_tier=access_tier,
        kb_text=kb_text,
        memory_snippets=memory_snippets,
        web_context=web_context,
        citations_block=citations_block,
        confidence_line=confidence_line,
        deep_run=user_requests_deep_answer(user_text),
        profile_directives=profile_directives,
    )


def create_chat_completion(
    db: Session,
    req: ChatRequest,
    user: Optional[models.User],
    client_ip: Optional[str] = None,
) -> ChatResponse:
    from vereda_backend.core import load_monitor
    from vereda_backend.core.concurrency_control import SlotTimeoutError, llm_execution_slot
    from vereda_backend.core.priority import TrafficPriority, priority_for_user

    stress = load_monitor.stress_level()
    scale = load_monitor.stress_to_output_scale(stress)
    if priority_for_user(user) == TrafficPriority.GOV:
        scale = min(
            1.0,
            scale + float(getattr(settings, "load_gov_boost_scale", 0.12) or 0.12),
        )
    req = prepare_chat_request(req, stress_scale=scale, user=user)
    reply_text = ""
    locale = getattr(req, "locale", None)
    # Localiza última mensagem do usuário
    last_user = next((m for m in reversed(req.messages) if m.role == "user"), None)
    if not last_user:
        raise RuntimeError(
            "[Syntexa V45] Nenhuma mensagem do usuário no payload. "
            "Envie pelo menos uma mensagem de usuário para iniciar o chat."
        )
    content = last_user.content.strip()
    if not content:
        raise RuntimeError(
            "[Syntexa V45] Mensagem do usuário está vazia. "
            "Envie conteúdo válido para processar a inferência."
        )

    shared_hit = None
    if user is None:
        _sd = _shared_question_digest(content, req.model, req.temperature)
        shared_hit = shared_question_cache_get(_sd)
    if shared_hit is not None:
        reply_text = shared_hit
    else:
        cache_key = _make_cache_key(req, user)
        cached = _cache_get(cache_key)
        if cached is not None:
            reply_text = cached
        else:
            from vereda_backend.core.job_queue import job_queue_enabled, run_long_chat_sync

            threshold = int(getattr(settings, "chat_long_job_threshold_tokens", 2500) or 2500)
            queued = False
            if job_queue_enabled() and req.max_tokens >= threshold:
                try:
                    remote = run_long_chat_sync(
                        req.model_dump_json(), user.id if user else None
                    )
                    if remote:
                        reply_text = remote
                        _cache_set(cache_key, reply_text)
                        queued = True
                except Exception as exc:
                    logger.warning("Fila chat longo indisponível, síncrono: %s", exc)
            if (
                not queued
                and user is None
                and job_queue_enabled()
                and load_monitor.should_offload_public_to_queue(stress)
                and req.max_tokens < threshold
            ):
                try:
                    remote = run_long_chat_sync(
                        req.model_dump_json(), user.id if user else None
                    )
                    if remote:
                        reply_text = remote
                        _cache_set(cache_key, reply_text)
                        queued = True
                except Exception as exc:
                    logger.warning("Fila sob carga (público) indisponível: %s", exc)
            if not queued:

                def _run_llm() -> str:
                    with llm_execution_slot(user, client_ip or "unknown"):
                        return _compute_chat_reply(db, req, user, content)

                event, owns_singleflight = _singleflight_enter(cache_key)
                if not owns_singleflight:
                    wait_sec = float(getattr(settings, "chat_singleflight_wait_sec", 8.0))
                    event.wait(timeout=max(0.2, wait_sec))
                    cached_after_wait = _cache_get(cache_key)
                    if cached_after_wait is not None:
                        reply_text = cached_after_wait
                    else:
                        reply_text = _run_llm()
                        _cache_set(cache_key, reply_text)
                else:
                    try:
                        reply_text = _run_llm()
                        _cache_set(cache_key, reply_text)
                    finally:
                        _singleflight_leave(cache_key, event)
    if (
        reply_text
        and user is None
        and content
        and shared_hit is None
    ):
        _sd = _shared_question_digest(content, req.model, req.temperature)
        ttl = int(getattr(settings, "chat_shared_cache_ttl_sec", 300) or 300)
        shared_question_cache_set(_sd, reply_text, ttl_sec=ttl)
    reply_text = fix_text_encoding(reply_text)
    if not reply_text:
        raise RuntimeError(
            "[Syntexa V45] Inference retornou resposta vazia após todos os retries. "
            "Nenhum fallback textual é permitido. Verifique disponibilidade do runtime LLM local."
        )

    assistant_message = ChatMessage(role="assistant", content=fix_text_encoding(reply_text))
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
    _audit_admin_chat_if_needed(db, user, content)
    # Armazena turnos na memória vetorial
    conv_id = str(user.id) if user else "anon"
    for msg in req.messages:
        conversation_memory.add_turn(conv_id, msg.role, msg.content)

    mode = _effective_mode(content)
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
    elif mode == "copiloto":
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
            resource=_audit_chat_resource(),
            detail=_audit_chat_detail(preview=content[:500], mode="copiloto"),
            ip_address=get_chat_request_context().get("client_ip"),
        )
    elif mode == "lab":
        history = [{"role": m.role, "content": m.content} for m in req.messages[:-1]]
        reply_text = run_lab(content, llm_engine, history=history, max_tokens=req.max_tokens)
        events.notify_chat_completion(
            user, prompt_preview=content, reply_preview=reply_text
        )
        audit_log(
            db,
            action="chat_lab",
            user_id=user.id if user else None,
            resource=_audit_chat_resource(),
            detail=_audit_chat_detail(preview=content[:500], mode="lab"),
            ip_address=get_chat_request_context().get("client_ip"),
        )
    elif mode == "cientifico":
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
            resource=_audit_chat_resource(),
            detail=_audit_chat_detail(preview=content[:500], mode="cientifico"),
            ip_address=get_chat_request_context().get("client_ip"),
        )
    elif mode == "juridico":
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
            resource=_audit_chat_resource(),
            detail=_audit_chat_detail(preview=content[:500], mode="juridico"),
            ip_address=get_chat_request_context().get("client_ip"),
        )
    elif mode == "estrategico":
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
            resource=_audit_chat_resource(),
            detail=_audit_chat_detail(preview=content[:500], mode="estrategico"),
            ip_address=get_chat_request_context().get("client_ip"),
        )
    else:
        _rk = _retrieval_knobs_for_message(content)
        _query_profile = analyze_query_profile(content)
        _profile_block = build_profile_directives(_query_profile)
        _domain_hint = _query_profile.domains[0] if _query_profile.domains else None
        knowledge_items = _find_relevant_knowledge(db, content, limit=_rk["kb_limit"])
        kb_text = ""
        if knowledge_items:
            kb_text = "\n".join(
                f"- {it.title}: {it.answer}" for it in knowledge_items
            )
        mem_k = _rk["mem_k"]
        rag_k = _rk["rag_k"]
        memory_docs = memory_system.retrieve_context(content, top_k=mem_k)
        if user:
            try:
                semantic_docs = semantic_context_for_user(
                    db, user_id=user.id, query=content, top_k=_rk["semantic_k"]
                )
                if semantic_docs:
                    memory_docs = memory_docs + [{"text": d} for d in semantic_docs]
            except Exception:
                pass
        rag_context = rag_engine.db.similarity_search(
            namespace="global", query=content, top_k=rag_k
        )
        web_context = ""
        citations_block = ""
        confidence_line = ""
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
        # Busca híbrida: timeout de CHAT_WEB_SEARCH_TIMEOUT_SEC (p.ex. 22s) — sub-segundo quebrava
        # a agregação e o núcleo nativo ficava sem factos reais.
        try:
            if is_definition:
                web_context, citations_block, confidence_line = _maybe_get_web_bundle(
                    content,
                    web_max=_rk["web_max_def"],
                    timeout_sec=None,
                    timeout_extra_sec=float(_rk["web_timeout_extra"]),
                    ttl_sec=1800,
                )
            else:
                web_context, citations_block, confidence_line = _maybe_get_web_bundle(
                    content,
                    web_max=_rk["web_max_gen"],
                    timeout_sec=None,
                    timeout_extra_sec=float(_rk["web_timeout_extra"]),
                    ttl_sec=1800,
                )
        except Exception:
            web_context, citations_block, confidence_line = "", "", ""

        system_prompt = _build_system_prompt(
            user,
            kb_text,
            memory_docs + rag_context,
            user_text=content,
            web_context=web_context,
            citations_block=citations_block,
            confidence_line=confidence_line,
            profile_directives=_profile_block,
        )
        system_prompt = f"{_locale_instruction(getattr(req, 'locale', None))}\n\n{system_prompt}"
        messages = [
            {"role": "system", "content": system_prompt},
            *[m.model_dump() for m in req.messages],
        ]
        _deep = bool(_rk["deep"])
        _cap = _llm_output_cap_tokens_for_user(deep_run=_deep, user=user)
        _max_tokens = min(req.max_tokens, max(256, _cap))
        _eff_temp = _effective_chat_temperature(req, deep_run=_deep)
        reply_text = _chat_with_retry(
            messages,
            temperature=_eff_temp,
            max_tokens=_max_tokens,
            domain=_domain_hint,
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
            resource=_audit_chat_resource(),
            detail=_audit_chat_detail(preview=content or ""),
            ip_address=get_chat_request_context().get("client_ip"),
        )
    # ── Cognitive layer: post-processing pipeline (anti-generic, humanization, entropy)
    locale_val = str(getattr(req, "locale", None) or "pt-BR")
    _cog_ctx = CognitiveContext(
        user_name=str(getattr(user, "name", None) or getattr(user, "username", None) or "") or None,
        locale=locale_val,
    )
    reply_text = cognitive_refine(reply_text, _cog_ctx)
    return reply_text


def record_stream_chat_completion_audit(
    db: Session,
    user: Optional[models.User],
    user_message_preview: str,
    assistant_text: str,
) -> None:
    """Auditoria do fluxo streaming (o caminho síncrono já audita em chat_completion)."""
    try:
        audit_log(
            db,
            action="chat_completion_stream",
            user_id=user.id if user else None,
            resource=_audit_chat_resource(),
            detail=_audit_chat_detail(
                preview=user_message_preview or "",
                reply_preview=(assistant_text or "")[:600],
            ),
            ip_address=get_chat_request_context().get("client_ip"),
        )
    except Exception:
        pass


def stream_chat_completion(
    db: Session,
    req: ChatRequest,
    user: Optional[models.User],
    client_ip: Optional[str] = None,
) -> Iterator[str]:
    """Gera chunks de texto para resposta imediata (streaming). Mesma lógica do create_chat_completion."""
    from vereda_backend.core import load_monitor
    from vereda_backend.core.concurrency_control import SlotTimeoutError, llm_execution_slot
    from vereda_backend.core.priority import TrafficPriority, priority_for_user

    stress = load_monitor.stress_level()
    scale = load_monitor.stress_to_output_scale(stress)
    if priority_for_user(user) == TrafficPriority.GOV:
        scale = min(
            1.0,
            scale + float(getattr(settings, "load_gov_boost_scale", 0.12) or 0.12),
        )
    req = prepare_chat_request(req, stress_scale=scale, user=user)
    locale = getattr(req, "locale", None)
    last_user = next((m for m in reversed(req.messages) if m.role == "user"), None)
    if not last_user:
        raise RuntimeError(
            "[Syntexa V45] Nenhuma mensagem do usuário no payload. "
            "Envie pelo menos uma mensagem de usuário para iniciar o chat."
        )
    content = last_user.content.strip()
    if not content:
        raise RuntimeError(
            "[Syntexa V45] Mensagem do usuário está vazia. "
            "Envie conteúdo válido para processar a inferência."
        )
    _audit_admin_chat_if_needed(db, user, content)
    conv_id = str(user.id) if user else "anon"
    for msg in req.messages:
        conversation_memory.add_turn(conv_id, msg.role, msg.content)

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
    mode = _effective_mode(content)
    try:
        with llm_execution_slot(user, client_ip or "unknown"):
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
            _rk = _retrieval_knobs_for_message(content)
            _query_profile = analyze_query_profile(content)
            _profile_block = build_profile_directives(_query_profile)
            _domain_hint = _query_profile.domains[0] if _query_profile.domains else None
            knowledge_items = _find_relevant_knowledge(db, content, limit=_rk["kb_limit"])
            kb_text = (
                "\n".join(f"- {it.title}: {it.answer}" for it in knowledge_items)
                if knowledge_items
                else ""
            )
            mem_k = _rk["mem_k"]
            rag_k = _rk["rag_k"]
            memory_docs = memory_system.retrieve_context(content, top_k=mem_k)
            if user:
                try:
                    semantic_docs = semantic_context_for_user(
                        db, user_id=user.id, query=content, top_k=_rk["semantic_k"]
                    )
                    if semantic_docs:
                        memory_docs = memory_docs + [{"text": d} for d in semantic_docs]
                except Exception:
                    pass
            rag_context = rag_engine.db.similarity_search(namespace="global", query=content, top_k=rag_k)
            web_context = ""
            citations_block = ""
            confidence_line = ""
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
            try:
                if is_definition:
                    web_context, citations_block, confidence_line = _maybe_get_web_bundle(
                        content,
                        web_max=_rk["web_max_def"],
                        timeout_sec=None,
                        timeout_extra_sec=float(_rk["web_timeout_extra"]),
                        ttl_sec=1800,
                    )
                else:
                    web_context, citations_block, confidence_line = _maybe_get_web_bundle(
                        content,
                        web_max=_rk["web_max_gen"],
                        timeout_sec=None,
                        timeout_extra_sec=float(_rk["web_timeout_extra"]),
                        ttl_sec=1800,
                    )
            except Exception:
                web_context, citations_block, confidence_line = "", "", ""
            system_prompt = _build_system_prompt(
                user,
                kb_text,
                memory_docs + rag_context,
                user_text=content,
                web_context=web_context,
                citations_block=citations_block,
                confidence_line=confidence_line,
                profile_directives=_profile_block,
            )
            system_prompt = f"{_locale_instruction(locale)}\n\n{system_prompt}"
            messages = [
                {"role": "system", "content": system_prompt},
                *[m.model_dump() for m in req.messages],
            ]
            prov_name = str(getattr(llm_engine, "_default", "syntexa_native"))
            stream_payload = adapt_messages_for_llm_provider(messages, prov_name)
            _deep = bool(_rk["deep"])
            _cap = _llm_output_cap_tokens(deep_run=_deep)
            _max_tokens = min(req.max_tokens, max(256, _cap))
            _eff_temp = _effective_chat_temperature(req, deep_run=_deep)
            retries = max(1, int(getattr(settings, "chat_llm_retries", 4) or 4))
            backoff_base = max(
                0.05, float(getattr(settings, "chat_llm_retry_backoff_sec", 0.5) or 0.5)
            )
            last_exc: Exception | None = None
            for attempt in range(retries):
                yielded = False
                raw_acc = ""
                sent_acc = ""
                try:
                    for chunk in llm_engine.chat_stream(
                        stream_payload,
                        temperature=_eff_temp,
                        max_tokens=_max_tokens,
                        domain=_domain_hint,
                    ):
                        yielded = True
                        raw_acc += chunk or ""
                        stream_view = sanitize_for_stream(raw_acc)
                        if len(stream_view) > len(sent_acc):
                            delta = stream_view[len(sent_acc) :]
                            if delta:
                                yield delta
                            sent_acc = stream_view
                    final_text = fix_text_encoding(raw_acc)
                    if len(final_text) > len(sent_acc):
                        tail = final_text[len(sent_acc) :]
                        if tail:
                            yield tail
                        sent_acc = final_text
                    last_exc = None
                    break
                except Exception as exc:
                    last_exc = exc
                    logger.exception(
                        "Falha LLM stream (tentativa %s/%s)",
                        attempt + 1,
                        retries,
                    )
                    _maybe_alert_runtime_failure(user, exc)
                    if attempt >= retries - 1:
                        raise
                    sleep_s = backoff_base * (2 ** attempt)
                    logger.warning("Retry stream LLM em %.2fs", sleep_s)
                    time.sleep(sleep_s)
            if last_exc:
                raise last_exc
            if not yielded:
                raise RuntimeError("Streaming vazio do provedor LLM.")
            if not (raw_acc or "").strip():
                raise RuntimeError(
                    "[Syntexa V45] Streaming retornou resposta vazia. "
                    "Nenhum fallback é permitido. Verifique o runtime LLM local."
                )
    except SlotTimeoutError as exc:
        logger.error("[Syntexa V45] SlotTimeoutError no streaming: %s", exc)
        raise RuntimeError(
            "[Syntexa V45] Sistema em alta demanda — inference slot indisponível. "
            "Nenhum fallback textual é permitido. "
            f"Erro técnico: {type(exc).__name__}: {exc}"
        ) from exc

