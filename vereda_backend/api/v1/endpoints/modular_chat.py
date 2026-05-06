# -*- coding: utf-8 -*-
"""
POST /v1/chat: fluxo modular Router -> Agent -> Tools -> Resposta.
Body: { "message": "..." } ou { "messages": [...] }. Retorna { "response": "...", "category": "..." }.
"""
from typing import Any, List, Optional
import hashlib
import hmac
import json
import re
import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from vereda_backend.ai_runtime import chat_history_db, modular_engine
from vereda_backend.core.security import get_current_user_optional, get_current_admin
from vereda_backend.core.rate_limit import RateLimiter, get_client_ip
from vereda_backend.core.access_control import audit_log
from vereda_backend.db import models
from vereda_backend.db.session import get_db
from vereda_backend.ai_runtime import memory_system, rag_engine
from vereda_ai.router.prompt_router import PromptRouter, RouteCategory
from vereda_backend.services.chat_engine import (
    _is_longest_word_question,
    _longest_word_response_text,
)


router = APIRouter()
_pentest_admin_limiter = RateLimiter(max_calls=30, window_seconds=300, max_keys=10_000)


class ChatMessageIn(BaseModel):
    role: str = "user"
    content: str


class ModularChatRequest(BaseModel):
    message: Optional[str] = None
    messages: Optional[List[ChatMessageIn]] = None
    user_id: Optional[str] = None
    use_cache: bool = True


class ModularChatResponse(BaseModel):
    response: str
    category: str


class PentestAdminRequest(BaseModel):
    message: str
    target_scope: str
    authorization_confirmed: bool = False
    legal_ack_text: str = ""
    engagement_id: Optional[str] = None
    authorization_token: Optional[str] = None
    evidence_depth: int = 4
    use_cache: bool = False


class PentestAdminPreflightRequest(BaseModel):
    target_scope: str
    legal_ack_text: str
    engagement_id: Optional[str] = None
    expires_in_sec: int = 1800


class PentestAdminPreflightResponse(BaseModel):
    ok: bool
    authorization_token: str
    expires_at_epoch: int
    scope_fingerprint: str


class PentestAdminSuiteRequest(BaseModel):
    target_scope: str
    legal_ack_text: str
    authorization_confirmed: bool = False
    authorization_token: Optional[str] = None
    engagement_id: Optional[str] = None
    evidence_depth: int = 5
    pack_ids: List[str] = []
    include_full_response: bool = True
    use_cache: bool = False


class PentestAdminSuiteCaseResult(BaseModel):
    case_id: str
    title: str
    quality_gate_pass: bool
    quality_gate_score: int
    response: Optional[str] = None


class PentestAdminSuiteResponse(BaseModel):
    ok: bool
    total_cases: int
    passed_cases: int
    score_avg: float
    items: List[PentestAdminSuiteCaseResult]


PENTEST_ADMIN_PACKS: dict[str, dict[str, str]] = {
    "auth-session": {
        "title": "Auth/Session Hardcore",
        "prompt": (
            "Avalie autenticacao e sessao: JWT tampering, refresh replay, brute-force throttling, "
            "session fixation, account takeover e bypass de MFA."
        ),
    },
    "api-logic-idor": {
        "title": "API Logic + IDOR",
        "prompt": (
            "Avalie BOLA/BFLA, IDOR horizontal/vertical, mass assignment, enumeracao de recursos "
            "e falhas de autorizacao por objeto."
        ),
    },
    "cors-headers-hardening": {
        "title": "CORS + Headers Hardening",
        "prompt": (
            "Audite CORS, CSP, HSTS, cookies secure/httpOnly/sameSite, cache-control e exposicao de headers sensiveis."
        ),
    },
    "supply-chain-cicd": {
        "title": "Supply Chain + CI/CD",
        "prompt": (
            "Audite dependencias vulneraveis, assinatura de artefatos, segredos em pipeline, "
            "integridade de deploy e controles de promocao."
        ),
    },
    "observability-ir": {
        "title": "Observability + Incident Response",
        "prompt": (
            "Avalie lacunas de auditoria, cobertura de logs, deteccao/alerta, trilha forense, "
            "MTTD/MTTR e readiness de resposta a incidente."
        ),
    },
}


def _scope_fingerprint(scope: str) -> str:
    raw = (scope or "").strip().lower().encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:24]


def _sign_payload(payload: dict[str, Any]) -> str:
    data = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    key = str(getattr(models, "__name__", "vereda_backend")).encode("utf-8")
    # Usa segredo real do backend para impedir replay/tampering em clientes.
    from vereda_backend.core.config import settings as backend_settings

    secret = str(getattr(backend_settings, "secret_key", "") or "").encode("utf-8")
    digest = hmac.new(secret + key, data.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{data}.{digest}"


def _verify_signed_payload(token: str) -> Optional[dict[str, Any]]:
    raw = (token or "").strip()
    if "." not in raw:
        return None
    data, sig = raw.rsplit(".", 1)
    if not data or not sig:
        return None
    from vereda_backend.core.config import settings as backend_settings

    key = str(getattr(models, "__name__", "vereda_backend")).encode("utf-8")
    secret = str(getattr(backend_settings, "secret_key", "") or "").encode("utf-8")
    expected = hmac.new(secret + key, data.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return None
    try:
        payload = json.loads(data)
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _build_pentest_audit_detail(
    *,
    target_scope: str,
    prompt: str,
    engagement_id: Optional[str],
    auth_mode: str,
    evidence_depth: int,
) -> str:
    body = {
        "scope": (target_scope or "")[:500],
        "scope_fingerprint": _scope_fingerprint(target_scope),
        "prompt_preview": (prompt or "")[:800],
        "engagement_id": (engagement_id or "")[:120],
        "auth_mode": auth_mode,
        "evidence_depth": max(1, min(5, int(evidence_depth))),
        "ts": int(time.time()),
    }
    return json.dumps(body, ensure_ascii=False)[:1900]


def _parse_pentest_audit_detail(detail: str) -> dict[str, Any]:
    raw = (detail or "").strip()
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
        if isinstance(payload, dict):
            return payload
    except Exception:
        pass
    # Retrocompatibilidade com formato antigo "scope=...; prompt=..."
    scope = ""
    prompt = ""
    m_scope = re.search(r"scope=(.*?);", raw)
    if m_scope:
        scope = m_scope.group(1).strip()
    m_prompt = re.search(r"prompt=(.*)$", raw)
    if m_prompt:
        prompt = m_prompt.group(1).strip()
    return {
        "scope": scope,
        "scope_fingerprint": _scope_fingerprint(scope),
        "prompt_preview": prompt[:800],
        "legacy": True,
    }


def _build_admin_pentest_prompt(message: str, target_scope: str) -> str:
    msg = (message or "").strip()
    scope = (target_scope or "").strip()
    return (
        "Modo: Pentest Admin Controlado (defensivo e autorizado, nivel enterprise).\n"
        "Escopo autorizado: %s\n\n"
        "Framework obrigatorio: OWASP ASVS + OWASP Testing Guide + NIST 800-115.\n"
        "Regras obrigatorias:\n"
        "- Trabalhe apenas no escopo autorizado.\n"
        "- Nao inclua instrucoes para ataque ilegal, malware ou abuso fora de escopo.\n"
        "- Nao gere exploit weaponized nem payload para alvo fora de autorizacao.\n"
        "- Priorize analise defensiva, descoberta responsavel e mitigacao.\n"
        "- Sempre inclua: risco, evidencia esperada, validacao segura e plano de correcao.\n"
        "- Se o pedido for fora de escopo, recuse e peça delimitacao formal.\n\n"
        "Formato obrigatorio de resposta:\n"
        "1) Resumo executivo (impacto, probabilidade, prioridade)\n"
        "2) Matriz de superficie de ataque por componente\n"
        "3) Vetores de teste (somente seguros e autorizados)\n"
        "4) Evidencias esperadas e telemetria recomendada\n"
        "5) Plano de correcao por severidade (P0/P1/P2)\n"
        "6) Checklist de re-teste e criterios de aceite\n\n"
        "Solicitacao:\n%s"
    ) % (scope, msg)


def _quality_gate_score(text: str) -> tuple[bool, int]:
    t = (text or "").lower()
    checks = [
        "resumo executivo",
        "matriz",
        "evidenc",
        "correc",
        "reteste",
    ]
    score = 0
    for c in checks:
        if c in t:
            score += 1
    return score >= 4, score


def _resolve_suite_packs(pack_ids: list[str]) -> list[tuple[str, str, str]]:
    if not pack_ids:
        pack_ids = list(PENTEST_ADMIN_PACKS.keys())
    out: list[tuple[str, str, str]] = []
    for pid in pack_ids:
        key = (pid or "").strip().lower()
        item = PENTEST_ADMIN_PACKS.get(key)
        if not item:
            continue
        out.append((key, item["title"], item["prompt"]))
    return out


def _last_user_content(req: ModularChatRequest) -> str:
    if req.message:
        return req.message.strip()
    if req.messages:
        for m in reversed(req.messages):
            if m.role == "user":
                return (m.content or "").strip()
    return ""


@router.post("/chat", response_model=ModularChatResponse)
async def modular_chat(
    body: ModularChatRequest,
    current_user: Optional[models.User] = Depends(get_current_user_optional),
    db = Depends(get_db),
) -> ModularChatResponse:
    """
    Chat modular: prompt -> Router -> Agent -> Tools -> Resposta.
    """
    prompt = _last_user_content(body)
    if not prompt:
        return ModularChatResponse(response="Envie uma mensagem.", category="general")

    if _is_longest_word_question(prompt):
        return ModularChatResponse(
            response=_longest_word_response_text(),
            category=RouteCategory.KNOWLEDGE.value,
        )

    # Segurança: nunca aceitar user_id vindo do cliente para evitar IDOR.
    user_id = str(current_user.id) if current_user else "anon"
    history: List[dict] = []
    try:
        recent = chat_history_db.get_recent(user_id, limit=6)
        history = [{"role": r["role"], "content": r["message"]} for r in recent]
    except Exception:
        pass

    knowledge_snippets: List[str] = []
    memory_snippets: List[str] = []
    try:
        if rag_engine and hasattr(rag_engine, "db"):
            docs = rag_engine.db.similarity_search(namespace="global", query=prompt, top_k=3)
            knowledge_snippets = [d.get("text", "") for d in docs if d.get("text")]
        mem = memory_system.retrieve_context(prompt, top_k=2)
        memory_snippets = [m.get("text", "") for m in mem if m.get("text")]
    except Exception:
        pass

    category = PromptRouter().route(prompt)
    response = modular_engine.process(
        prompt=prompt,
        user_id=user_id,
        history=history,
        knowledge_snippets=knowledge_snippets,
        memory_snippets=memory_snippets,
        use_cache=body.use_cache,
    )

    try:
        chat_history_db.add(user_id, prompt, "user")
        chat_history_db.add(user_id, response, "assistant")
    except Exception:
        pass

    return ModularChatResponse(response=response, category=category.value)


@router.post("/chat/pentest-admin", response_model=ModularChatResponse)
async def pentest_admin_chat(
    body: PentestAdminRequest,
    http_request: Request,
    current_admin: models.User = Depends(get_current_admin),
    db=Depends(get_db),
) -> ModularChatResponse:
    scope = (body.target_scope or "").strip()
    prompt = (body.message or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Mensagem vazia.")
    if len(scope) < 8:
        raise HTTPException(status_code=400, detail="target_scope muito curto.")
    if not (1 <= int(body.evidence_depth) <= 5):
        raise HTTPException(status_code=400, detail="evidence_depth deve estar entre 1 e 5.")
    if not body.authorization_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirme authorization_confirmed=true para operar o modo pentest admin.",
        )
    if len((body.legal_ack_text or "").strip()) < 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="legal_ack_text insuficiente (minimo 20 caracteres).",
        )

    auth_mode = "legacy_ack_only"
    if body.authorization_token:
        payload = _verify_signed_payload(body.authorization_token)
        if not payload:
            raise HTTPException(status_code=400, detail="authorization_token invalido.")
        now = int(time.time())
        exp = int(payload.get("exp", 0) or 0)
        if exp <= now:
            raise HTTPException(status_code=400, detail="authorization_token expirado.")
        if str(payload.get("scope_fp", "")) != _scope_fingerprint(scope):
            raise HTTPException(status_code=400, detail="authorization_token nao confere com target_scope.")
        if int(payload.get("admin_id", 0) or 0) != int(current_admin.id):
            raise HTTPException(status_code=403, detail="authorization_token pertence a outro admin.")
        auth_mode = "signed_preflight_token"

    ip = get_client_ip(http_request)
    _pentest_admin_limiter.check(
        key=f"pentest:{current_admin.id}:{ip}",
        detail="Muitas solicitações de pentest em pouco tempo. Aguarde alguns minutos.",
    )
    user_id = str(current_admin.id)
    chat_user_id = "pentest-admin:%s" % user_id
    history: List[dict[str, str]] = []
    try:
        recent = chat_history_db.get_recent(chat_user_id, limit=6)
        history = [{"role": r["role"], "content": r["message"]} for r in recent]
    except Exception:
        pass
    secure_prompt = _build_admin_pentest_prompt(prompt, scope)
    response = modular_engine.process(
        prompt=secure_prompt,
        user_id=chat_user_id,
        history=history,
        knowledge_snippets=[],
        memory_snippets=[],
        use_cache=body.use_cache,
    )
    try:
        chat_history_db.add(chat_user_id, secure_prompt, "user")
        chat_history_db.add(chat_user_id, response, "assistant")
    except Exception:
        pass
    try:
        audit_log(
            db,
            action="admin_pentest_chat_used",
            user_id=current_admin.id,
            resource="modular_chat:pentest_admin",
            detail=_build_pentest_audit_detail(
                target_scope=scope,
                prompt=prompt,
                engagement_id=body.engagement_id,
                auth_mode=auth_mode,
                evidence_depth=body.evidence_depth,
            ),
            ip_address=ip,
        )
    except Exception:
        pass
    return ModularChatResponse(response=response, category="security_pentest_admin")


@router.post("/chat/pentest-admin/preflight", response_model=PentestAdminPreflightResponse)
async def pentest_admin_preflight(
    body: PentestAdminPreflightRequest,
    http_request: Request,
    current_admin: models.User = Depends(get_current_admin),
    db=Depends(get_db),
) -> PentestAdminPreflightResponse:
    scope = (body.target_scope or "").strip()
    ack = (body.legal_ack_text or "").strip()
    if len(scope) < 8:
        raise HTTPException(status_code=400, detail="target_scope muito curto.")
    if len(ack) < 20:
        raise HTTPException(status_code=400, detail="legal_ack_text insuficiente (minimo 20 caracteres).")
    ttl = max(60, min(24 * 3600, int(body.expires_in_sec or 1800)))
    now = int(time.time())
    exp = now + ttl
    payload = {
        "admin_id": int(current_admin.id),
        "scope_fp": _scope_fingerprint(scope),
        "engagement_id": (body.engagement_id or "")[:120],
        "iat": now,
        "exp": exp,
    }
    token = _sign_payload(payload)
    ip = get_client_ip(http_request)
    try:
        audit_log(
            db,
            action="admin_pentest_preflight_authorized",
            user_id=current_admin.id,
            resource="modular_chat:pentest_admin",
            detail=json.dumps(
                {
                    "scope": scope[:500],
                    "scope_fingerprint": _scope_fingerprint(scope),
                    "engagement_id": (body.engagement_id or "")[:120],
                    "ack_preview": ack[:180],
                    "exp": exp,
                },
                ensure_ascii=False,
            )[:1900],
            ip_address=ip,
        )
    except Exception:
        pass
    return PentestAdminPreflightResponse(
        ok=True,
        authorization_token=token,
        expires_at_epoch=exp,
        scope_fingerprint=_scope_fingerprint(scope),
    )


@router.get("/chat/pentest-admin/history")
async def pentest_admin_history(
    limit: int = 50,
    current_admin: models.User = Depends(get_current_admin),
    db=Depends(get_db),
) -> dict[str, Any]:
    cap = min(max(1, int(limit)), 200)
    rows = (
        db.query(models.AuditLog)
        .filter(
            models.AuditLog.resource == "modular_chat:pentest_admin",
            models.AuditLog.action.in_(
                ["admin_pentest_chat_used", "admin_pentest_preflight_authorized"]
            ),
        )
        .order_by(models.AuditLog.id.desc())
        .limit(cap)
        .all()
    )
    items = []
    for r in rows:
        items.append(
            {
                "id": r.id,
                "action": r.action,
                "user_id": r.user_id,
                "ip_address": r.ip_address,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "detail": _parse_pentest_audit_detail(r.detail or ""),
            }
        )
    return {
        "ok": True,
        "admin_id": current_admin.id,
        "count": len(items),
        "items": items,
    }


@router.post("/chat/pentest-admin/suite", response_model=PentestAdminSuiteResponse)
async def pentest_admin_suite(
    body: PentestAdminSuiteRequest,
    http_request: Request,
    current_admin: models.User = Depends(get_current_admin),
    db=Depends(get_db),
) -> PentestAdminSuiteResponse:
    scope = (body.target_scope or "").strip()
    if len(scope) < 8:
        raise HTTPException(status_code=400, detail="target_scope muito curto.")
    if not body.authorization_confirmed:
        raise HTTPException(status_code=400, detail="authorization_confirmed=true obrigatório.")
    ack = (body.legal_ack_text or "").strip()
    if len(ack) < 20:
        raise HTTPException(status_code=400, detail="legal_ack_text insuficiente.")
    if not (1 <= int(body.evidence_depth) <= 5):
        raise HTTPException(status_code=400, detail="evidence_depth deve estar entre 1 e 5.")
    payload = _verify_signed_payload(body.authorization_token or "")
    if not payload:
        raise HTTPException(status_code=400, detail="authorization_token inválido para suite.")
    now = int(time.time())
    if int(payload.get("exp", 0) or 0) <= now:
        raise HTTPException(status_code=400, detail="authorization_token expirado.")
    if str(payload.get("scope_fp", "")) != _scope_fingerprint(scope):
        raise HTTPException(status_code=400, detail="authorization_token não confere com target_scope.")
    if int(payload.get("admin_id", 0) or 0) != int(current_admin.id):
        raise HTTPException(status_code=403, detail="authorization_token pertence a outro admin.")

    ip = get_client_ip(http_request)
    _pentest_admin_limiter.check(
        key=f"pentest-suite:{current_admin.id}:{ip}",
        detail="Muitas execuções de suite em pouco tempo. Aguarde alguns minutos.",
    )
    packs = _resolve_suite_packs(body.pack_ids or [])
    if not packs:
        raise HTTPException(status_code=400, detail="Nenhum pack válido informado.")

    user_id = str(current_admin.id)
    suite_user_id = "pentest-admin-suite:%s" % user_id
    history: List[dict[str, str]] = []
    try:
        recent = chat_history_db.get_recent(suite_user_id, limit=8)
        history = [{"role": r["role"], "content": r["message"]} for r in recent]
    except Exception:
        pass

    results: list[PentestAdminSuiteCaseResult] = []
    for pack_id, title, pack_prompt in packs:
        suite_msg = (
            "Modo suite case: %s\n"
            "Evidence depth: %s\n"
            "Solicitacao base:\n%s\n\n"
            "Case prompt:\n%s"
        ) % (title, int(body.evidence_depth), "Executar auditoria ofensiva controlada.", pack_prompt)
        secure_prompt = _build_admin_pentest_prompt(suite_msg, scope)
        response = modular_engine.process(
            prompt=secure_prompt,
            user_id=suite_user_id,
            history=history,
            knowledge_snippets=[],
            memory_snippets=[],
            use_cache=body.use_cache,
        )
        try:
            chat_history_db.add(suite_user_id, secure_prompt, "user")
            chat_history_db.add(suite_user_id, response, "assistant")
        except Exception:
            pass
        ok_gate, score_gate = _quality_gate_score(response)
        results.append(
            PentestAdminSuiteCaseResult(
                case_id=pack_id,
                title=title,
                quality_gate_pass=ok_gate,
                quality_gate_score=score_gate,
                response=response if body.include_full_response else None,
            )
        )

    passed = sum(1 for x in results if x.quality_gate_pass)
    avg = (
        sum(float(x.quality_gate_score) for x in results) / len(results)
        if results
        else 0.0
    )
    try:
        audit_log(
            db,
            action="admin_pentest_suite_used",
            user_id=current_admin.id,
            resource="modular_chat:pentest_admin",
            detail=json.dumps(
                {
                    "scope_fingerprint": _scope_fingerprint(scope),
                    "engagement_id": (body.engagement_id or "")[:120],
                    "total_cases": len(results),
                    "passed_cases": passed,
                    "score_avg": round(avg, 3),
                    "pack_ids": [x.case_id for x in results],
                },
                ensure_ascii=False,
            )[:1900],
            ip_address=ip,
        )
    except Exception:
        pass
    return PentestAdminSuiteResponse(
        ok=True,
        total_cases=len(results),
        passed_cases=passed,
        score_avg=round(avg, 3),
        items=results,
    )
