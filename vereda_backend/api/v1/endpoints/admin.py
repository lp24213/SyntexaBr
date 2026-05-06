from typing import Any, List
import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from vereda_ai.core.config import settings as ai_settings
from vereda_backend.core.admin_allowed_ips import load_allowed_ips, save_allowed_ips
from vereda_backend.core.access_control import audit_log
from vereda_backend.core.config import settings as backend_settings
from vereda_backend.core.chat_policy import get_policy_snapshot, invalidate_policy_cache
from vereda_backend.core.prom_metrics import get_chat_slo_snapshot
from vereda_backend.core.security import get_current_admin
from vereda_backend.core.syntexa_intel import top_subjects
from vereda_backend.db import models
from vereda_backend.db.session import get_db
from vereda_backend.schemas.knowledge import (
    KnowledgeBaseItemCreate,
    KnowledgeBaseItemPublic,
)
from vereda_ai.syntexa_core.model_registry import (
    get_registry as get_syntexa_registry,
    reload_registry as reload_syntexa_registry,
    set_active_model as set_syntexa_active_model,
)
from vereda_ai.syntexa_core.promotion_attestation import (
    build_llm_promotion_attestation,
    compact_audit_record,
    verify_attestation_document,
)
from vereda_ai.syntexa_core.runtime_model import runtime_readiness_report


router = APIRouter(prefix="/admin")


def _ensure_llm_promotion_allowed(request: Request) -> None:
    if not bool(getattr(backend_settings, "llm_promotion_change_freeze", False)):
        return
    secret = str(
        getattr(backend_settings, "llm_promotion_freeze_bypass_secret", "") or ""
    ).strip()
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM_PROMOTION_CHANGE_FREEZE ativo sem LLM_PROMOTION_FREEZE_BYPASS_SECRET.",
        )
    bypass = (request.headers.get("x-syntexa-freeze-bypass") or "").strip()
    if bypass != secret:
        raise HTTPException(
            status_code=423,
            detail="Change freeze: envie header X-Syntexa-Freeze-Bypass com o secret configurado.",
        )


@router.get("/system/status")
def admin_system_status(_: models.User = Depends(get_current_admin)) -> dict:
    """
    Monitor interno: CPU, RAM, stress, requisições ativas, fila ARQ aproximada, slots de concorrência.
    """
    from vereda_backend.core.concurrency_control import stats as conc_stats
    from vereda_backend.core.load_monitor import snapshot

    return {"load": snapshot(), "concurrency": conc_stats()}


@router.get("/me")
def admin_me(current_admin: models.User = Depends(get_current_admin)):
    return {
        "id": current_admin.id,
        "email": current_admin.email,
        "full_name": current_admin.full_name,
        "is_admin": current_admin.is_admin,
    }


@router.post("/knowledge", response_model=KnowledgeBaseItemPublic)
def create_knowledge_item(
    payload: KnowledgeBaseItemCreate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin),
) -> KnowledgeBaseItemPublic:
    item = models.KnowledgeItem(
        title=payload.title,
        question=payload.question,
        answer=payload.answer,
        tags=payload.tags or "",
        owner_id=current_admin.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/knowledge", response_model=List[KnowledgeBaseItemPublic])
def list_knowledge_items(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin),
) -> List[KnowledgeBaseItemPublic]:
    items = db.query(models.KnowledgeItem).order_by(models.KnowledgeItem.id.desc()).all()
    return items


class AllowedIpsPayload(BaseModel):
    ips: List[str] = Field(default_factory=list)


class ActiveModelPayload(BaseModel):
    model_name: str = Field(..., min_length=2)


class PromoteModelPayload(BaseModel):
    candidate_model: str = Field(..., min_length=2)
    rollback_on_fail: bool = True


class PromoteCanaryPayload(BaseModel):
    candidate_model: str = Field(..., min_length=2)
    checks: int = Field(default=3, ge=1, le=20)
    interval_sec: float = Field(default=2.0, ge=0.2, le=30.0)
    rollback_on_fail: bool = True
    enforce_slo: bool = True
    max_error_rate: float = Field(default=0.08, ge=0.0, le=1.0)
    max_p95_latency_ms: float = Field(default=3500.0, ge=100.0, le=120000.0)
    min_requests_for_slo: int = Field(default=50, ge=0, le=100000)


class RollbackModelPayload(BaseModel):
    target_model: str = Field(..., min_length=2)
    reason: str | None = Field(default=None, max_length=500)


class VerifyAttestationPayload(BaseModel):
    document: dict[str, Any]


@router.get("/network/allowed-ips")
def get_network_allowed_ips(_: models.User = Depends(get_current_admin)) -> dict:
    """IPs cadastrados para referência (ex.: firewall/nginx na instituição)."""
    return {"ips": load_allowed_ips()}


@router.put("/network/allowed-ips")
def put_network_allowed_ips(
    body: AllowedIpsPayload,
    _: models.User = Depends(get_current_admin),
) -> dict:
    """Substitui a lista de IPs (um por linha no cliente; aqui lista normalizada)."""
    saved = save_allowed_ips(body.ips)
    return {"ok": True, "ips": saved}


@router.get("/dashboard/metrics")
def admin_dashboard_metrics(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin),
) -> dict:
    total_conversations = db.query(func.count(models.Conversation.id)).scalar() or 0
    total_messages = db.query(func.count(models.Message.id)).scalar() or 0
    total_users = db.query(func.count(models.User.id)).scalar() or 0
    model_runs = db.query(models.ModelRun).all()
    failures = sum(1 for r in model_runs if (r.status or "") != "success")
    avg_latency = (
        sum(float(r.latency_ms or 0.0) for r in model_runs) / len(model_runs)
        if model_runs
        else 0.0
    )
    quality_rows = db.query(models.FeedbackEvent).all()
    quality_avg = (
        sum(int(x.score or 0) for x in quality_rows if x.score is not None)
        / max(1, sum(1 for x in quality_rows if x.score is not None))
    )
    cost_estimate = sum(float(r.estimated_cost_usd or 0.0) for r in model_runs)
    retained_users = (
        db.query(models.Conversation.user_id)
        .filter(models.Conversation.user_id.isnot(None))
        .group_by(models.Conversation.user_id)
        .having(func.count(models.Conversation.id) >= 2)
        .count()
    )
    msg_rows = db.query(models.Message).all()
    topics = [{"name": k, "count": v} for k, v in top_subjects(msg_rows, limit=10)]
    return {
        "total_users": total_users,
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "top_topics": topics,
        "failures": failures,
        "avg_latency_ms": round(avg_latency, 2),
        "quality_score_avg": round(quality_avg, 2),
        "inference_cost_usd": round(cost_estimate, 4),
        "retained_users": retained_users,
    }


@router.get("/dataset/export")
def export_training_dataset(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin),
) -> dict:
    """
    Exporta dataset anonimizando usuário para treino futuro da Syntexa.
    """
    rows = (
        db.query(models.Message)
        .filter(models.Message.role.in_(["user", "assistant"]))
        .order_by(models.Message.created_at.asc())
        .all()
    )
    dataset: list[dict] = []
    for r in rows:
        dataset.append(
            {
                "conversation_id": r.conversation_id,
                "user_hash": f"user_{(r.user_id or 0) % 1000000}",
                "role": r.role,
                "content": r.content,
                "language": r.language,
                "subject": r.subject,
                "sentiment": r.sentiment,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
        )
    return {"items": dataset, "count": len(dataset)}


@router.get("/llm/registry")
def admin_llm_registry(_: models.User = Depends(get_current_admin)) -> dict:
    reg = get_syntexa_registry()
    return {
        "active": reg.active,
        "models": [
            {
                "name": m.name,
                "stage": m.stage,
                "checkpoint_uri": m.checkpoint_uri,
                "params_millions": m.params_millions,
                "metadata": m.metadata,
            }
            for m in reg.models
        ],
    }


@router.post("/llm/registry/reload")
def admin_llm_registry_reload(_: models.User = Depends(get_current_admin)) -> dict:
    reg = reload_syntexa_registry()
    return {"ok": True, "active": reg.active, "models_count": len(reg.models)}


@router.post("/llm/active")
def admin_set_active_llm(
    request: Request,
    body: ActiveModelPayload,
    _: models.User = Depends(get_current_admin),
) -> dict:
    _ensure_llm_promotion_allowed(request)
    reg = set_syntexa_active_model(body.model_name.strip())
    return {"ok": True, "active": reg.active}


@router.post("/llm/promote-blue-green")
def admin_promote_blue_green(
    request: Request,
    body: PromoteModelPayload,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin),
) -> dict:
    _ensure_llm_promotion_allowed(request)
    previous = get_syntexa_registry().active
    candidate = body.candidate_model.strip()
    try:
        reg = set_syntexa_active_model(candidate)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    report = runtime_readiness_report()
    if not bool(report.get("ready", False)):
        rolled_back = False
        if body.rollback_on_fail and previous and previous != candidate:
            try:
                set_syntexa_active_model(previous)
                rolled_back = True
            except Exception:
                rolled_back = False
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "promoção blue/green falhou no readiness",
                "candidate": candidate,
                "previous": previous,
                "rolled_back": rolled_back,
                "runtime": report,
            },
        )
    policy_snap = get_policy_snapshot()
    att_full, _ = build_llm_promotion_attestation(
        promotion_type="llm_promote_blue_green",
        previous_active=previous,
        candidate_model=candidate,
        active_after=reg.active,
        readiness_report=report,
        policy_snapshot=policy_snap,
        admin_user_id=current_admin.id,
    )
    resp = {
        "ok": True,
        "active": reg.active,
        "previous_active": previous,
        "runtime": report,
        "promotion_attestation": att_full,
    }
    audit_log(
        db,
        action="llm_promote_blue_green",
        user_id=current_admin.id,
        resource="llm_registry",
        detail=compact_audit_record(att_full)[:2000],
    )
    return resp


@router.post("/llm/rollback")
def admin_llm_rollback(
    body: RollbackModelPayload,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin),
) -> dict:
    """
    Volta o modelo ativo no registry. Não passa por change-freeze (resposta a incidente).
    """
    previous = get_syntexa_registry().active
    target = body.target_model.strip()
    try:
        reg = set_syntexa_active_model(target)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    report = runtime_readiness_report()
    policy_snap = get_policy_snapshot()
    att_full, _ = build_llm_promotion_attestation(
        promotion_type="llm_rollback",
        previous_active=previous,
        candidate_model=target,
        active_after=reg.active,
        readiness_report=report,
        policy_snapshot=policy_snap,
        admin_user_id=current_admin.id,
        extra={"reason": body.reason},
    )
    audit_log(
        db,
        action="llm_rollback",
        user_id=current_admin.id,
        resource="llm_registry",
        detail=compact_audit_record(att_full)[:2000],
    )
    return {
        "ok": True,
        "active": reg.active,
        "previous_active": previous,
        "runtime": report,
        "promotion_attestation": att_full,
    }


@router.post("/llm/promote-canary")
def admin_promote_canary(
    request: Request,
    body: PromoteCanaryPayload,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin),
) -> dict:
    _ensure_llm_promotion_allowed(request)
    previous = get_syntexa_registry().active
    candidate = body.candidate_model.strip()
    try:
        reg = set_syntexa_active_model(candidate)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    history: list[dict] = []
    stable = True
    for i in range(int(body.checks)):
        report = runtime_readiness_report()
        ok = bool(report.get("ready", False))
        history.append({"check": i + 1, "ready": ok, "runtime": report})
        if not ok:
            stable = False
            break
        if i < int(body.checks) - 1:
            time.sleep(float(body.interval_sec))
    slo = get_chat_slo_snapshot()
    slo_ok = True
    if body.enforce_slo:
        req_total = float(slo.get("requests_total", 0.0))
        if req_total < float(body.min_requests_for_slo):
            slo_ok = False
        else:
            slo_ok = bool(
                float(slo.get("error_rate", 0.0)) <= float(body.max_error_rate)
                and float(slo.get("p95_latency_ms", 0.0)) <= float(body.max_p95_latency_ms)
            )
    stable = stable and slo_ok
    if not stable:
        rolled_back = False
        if body.rollback_on_fail and previous and previous != candidate:
            try:
                set_syntexa_active_model(previous)
                rolled_back = True
            except Exception:
                rolled_back = False
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "canary falhou na janela de estabilidade",
                "candidate": candidate,
                "previous": previous,
                "rolled_back": rolled_back,
                "checks": history,
                "slo": slo,
            },
        )
    final_report = runtime_readiness_report()
    policy_snap = get_policy_snapshot()
    att_full, _ = build_llm_promotion_attestation(
        promotion_type="llm_promote_canary",
        previous_active=previous,
        candidate_model=candidate,
        active_after=reg.active,
        readiness_report=final_report,
        policy_snapshot=policy_snap,
        admin_user_id=current_admin.id,
        extra={
            "checks": history,
            "slo": slo,
            "enforce_slo": body.enforce_slo,
            "max_error_rate": body.max_error_rate,
            "max_p95_latency_ms": body.max_p95_latency_ms,
            "min_requests_for_slo": body.min_requests_for_slo,
        },
    )
    resp = {
        "ok": True,
        "active": reg.active,
        "previous_active": previous,
        "checks": history,
        "slo": slo,
        "promotion_attestation": att_full,
    }
    audit_log(
        db,
        action="llm_promote_canary",
        user_id=current_admin.id,
        resource="llm_registry",
        detail=compact_audit_record(att_full)[:2000],
    )
    return resp


@router.get("/llm/readiness")
def admin_llm_readiness(_: models.User = Depends(get_current_admin)) -> dict:
    env_backend = str(getattr(backend_settings, "environment", "local") or "local").lower()
    env_ai = str(getattr(ai_settings, "environment", "local") or "local").lower()
    strict_no_fallback = bool(getattr(ai_settings, "own_model_strict_no_fallback", False))
    report = runtime_readiness_report()
    return {
        "environment": {"backend": env_backend, "ai": env_ai},
        "strict_no_fallback": strict_no_fallback,
        "default_llm": str(getattr(backend_settings, "default_llm", "unknown")),
        "runtime": report,
        "chat_policy": get_policy_snapshot(),
    }


@router.get("/llm/slo-snapshot")
def admin_llm_slo_snapshot(_: models.User = Depends(get_current_admin)) -> dict:
    return {"ok": True, "slo": get_chat_slo_snapshot()}


@router.post("/llm/verify-attestation")
def admin_llm_verify_attestation(
    body: VerifyAttestationPayload,
    _: models.User = Depends(get_current_admin),
) -> dict:
    """Valida o digest SHA-256 de um documento de promoção/rollback (offline-safe após export)."""
    ok, msg, recomputed = verify_attestation_document(body.document)
    return {
        "ok": True,
        "valid": ok,
        "detail": msg,
        "recomputed_sha256": recomputed,
        "declared_sha256": body.document.get("attestation_sha256"),
    }


@router.get("/compliance/policy")
def admin_compliance_policy(_: models.User = Depends(get_current_admin)) -> dict:
    snap = get_policy_snapshot()
    return {"ok": True, **snap}


@router.post("/compliance/reload-policy")
def admin_compliance_reload_policy(_: models.User = Depends(get_current_admin)) -> dict:
    invalidate_policy_cache()
    return {"ok": True, "policy": get_policy_snapshot()}


@router.get("/compliance/audit")
def admin_compliance_audit(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin),
    action_prefix: str = "chat",
    limit: int = 100,
    resource: str | None = None,
) -> dict:
    q = db.query(models.AuditLog).order_by(models.AuditLog.id.desc())
    if resource:
        q = q.filter(models.AuditLog.resource == resource)
    if action_prefix:
        q = q.filter(models.AuditLog.action.startswith(action_prefix))
    cap = min(max(1, int(limit)), 500)
    rows = q.limit(cap).all()
    return {
        "ok": True,
        "items": [
            {
                "id": r.id,
                "action": r.action,
                "user_id": r.user_id,
                "resource": r.resource,
                "detail": r.detail,
                "ip_address": r.ip_address,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
    }


@router.get("/compliance/session/{session_id}")
def admin_compliance_session(
    session_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin),
) -> dict:
    sess = (
        db.query(models.ChatSession)
        .filter(models.ChatSession.id == session_id)
        .first()
    )
    if not sess:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    logs = (
        db.query(models.ConversationLog)
        .filter(models.ConversationLog.session_id == session_id)
        .order_by(models.ConversationLog.created_at.asc())
        .all()
    )
    res_key = f"chat_session:{session_id}"
    needle = f'%"session_id": {session_id}%'
    audits = (
        db.query(models.AuditLog)
        .filter(
            or_(
                models.AuditLog.resource == res_key,
                models.AuditLog.detail.like(needle),
            )
        )
        .order_by(models.AuditLog.id.desc())
        .limit(200)
        .all()
    )
    return {
        "ok": True,
        "session": {
            "id": sess.id,
            "user_id": sess.user_id,
            "title": sess.title,
            "created_at": sess.created_at.isoformat() if sess.created_at else None,
        },
        "policy": get_policy_snapshot(),
        "conversation": {
            "message_count": len(logs),
            "by_role": {
                "user": sum(1 for x in logs if x.role == "user"),
                "assistant": sum(1 for x in logs if x.role == "assistant"),
                "system": sum(1 for x in logs if x.role == "system"),
            },
            "first_at": logs[0].created_at.isoformat() if logs else None,
            "last_at": logs[-1].created_at.isoformat() if logs else None,
        },
        "audit_tail": [
            {
                "id": a.id,
                "action": a.action,
                "user_id": a.user_id,
                "resource": a.resource,
                "detail": a.detail,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in audits[:100]
        ],
    }

