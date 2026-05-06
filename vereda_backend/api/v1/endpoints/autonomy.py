from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from vereda_backend.core.security import get_current_user_optional, get_current_admin
from vereda_backend.core.rate_limit import RateLimiter, get_client_ip
from vereda_backend.db import models
from vereda_backend.db.session import get_db
from vereda_backend.services.autonomy_manager import (
    cancel_task,
    approve_sensitive_task,
    reject_sensitive_task,
    requeue_task_manually,
)
from vereda_backend.services.autonomous_evolution import (
    get_evolution_status,
    run_evolution_cycle_once,
    start_evolution_loop,
    stop_evolution_loop,
)
from vereda_backend.ai_runtime import llm_engine


router = APIRouter(prefix="/autonomy")

_create_limiter = RateLimiter(max_calls=20, window_seconds=300, max_keys=50_000)


class AutonomyCreateRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=60_000)
    priority: int = Field(default=5, ge=1, le=10)


class AutonomyTaskOut(BaseModel):
    id: int
    status: str
    priority: int
    prompt: str
    plan_text: Optional[str] = None
    steps: Optional[List[str]] = None
    outputs: Optional[Any] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class AutonomyRejectRequest(BaseModel):
    reason: str = Field(default="Rejeitado por política de segurança.", min_length=3, max_length=500)


class AutonomyRequeueRequest(BaseModel):
    reason: str = Field(default="Reprocessamento manual do administrador.", min_length=3, max_length=500)


def _to_out(row: models.AutonomyTask) -> AutonomyTaskOut:
    return AutonomyTaskOut(
        id=row.id,
        status=row.status,
        priority=row.priority,
        prompt=row.prompt,
        plan_text=row.plan_text,
        steps=row.steps_json if isinstance(row.steps_json, list) else None,
        outputs=row.outputs_json,
        error_message=row.error_message,
        created_at=row.created_at,
        started_at=row.started_at,
        finished_at=row.finished_at,
    )


def _iter_step_outputs(row: models.AutonomyTask) -> List[dict[str, Any]]:
    payload = row.outputs_json
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        partial = payload.get("partial_outputs")
        if isinstance(partial, list):
            return [x for x in partial if isinstance(x, dict)]
        result_outputs = payload.get("result_outputs")
        if isinstance(result_outputs, list):
            return [x for x in result_outputs if isinstance(x, dict)]
    return []


def _avg(values: list[float]) -> float:
    if not values:
        return 0.0
    return float(sum(values) / len(values))


@router.post("/tasks", response_model=AutonomyTaskOut)
def create_task(
    body: AutonomyCreateRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional),
) -> AutonomyTaskOut:
    # Autonomia é recurso pesado: sem login, limita bem mais.
    ip = get_client_ip(http_request)
    key = f"{ip}:{current_user.id if current_user else 'anon'}"
    _create_limiter.check(key, detail="Muitas tarefas criadas em pouco tempo. Aguarde alguns minutos.")

    prompt = (body.prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt vazio.")

    if current_user is None:
        # Permite só uma autonomia bem simples para anônimo (evita abuso).
        pr = max(6, int(body.priority))
    else:
        pr = int(body.priority)

    row = models.AutonomyTask(
        user_id=current_user.id if current_user else None,
        status="queued",
        priority=pr,
        prompt=prompt,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_out(row)


@router.get("/tasks/{task_id}", response_model=AutonomyTaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional),
) -> AutonomyTaskOut:
    row = db.query(models.AutonomyTask).filter(models.AutonomyTask.id == task_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")
    # Dono ou admin
    if row.user_id is not None and current_user and (current_user.is_admin or row.user_id == current_user.id):
        return _to_out(row)
    if row.user_id is None and current_user and current_user.is_admin:
        return _to_out(row)
    if row.user_id is None and current_user is None:
        return _to_out(row)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão.")


@router.get("/tasks", response_model=List[AutonomyTaskOut])
def list_tasks(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional),
) -> List[AutonomyTaskOut]:
    limit = max(1, min(200, int(limit)))
    q = db.query(models.AutonomyTask).order_by(models.AutonomyTask.created_at.desc())
    if current_user and current_user.is_admin:
        rows = q.limit(limit).all()
        return [_to_out(r) for r in rows]
    if current_user:
        rows = q.filter(models.AutonomyTask.user_id == current_user.id).limit(limit).all()
        return [_to_out(r) for r in rows]
    rows = q.filter(models.AutonomyTask.user_id == None).limit(min(limit, 10)).all()
    return [_to_out(r) for r in rows]


@router.get("/tasks/pending-approvals", response_model=List[AutonomyTaskOut])
def list_pending_approvals(
    limit: int = 50,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin),
) -> List[AutonomyTaskOut]:
    limit = max(1, min(200, int(limit)))
    rows = (
        db.query(models.AutonomyTask)
        .filter(models.AutonomyTask.status == "awaiting_approval")
        .order_by(models.AutonomyTask.created_at.desc())
        .limit(limit)
        .all()
    )
    return [_to_out(r) for r in rows]


@router.get("/admin/summary")
def admin_summary(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin),
) -> dict[str, Any]:
    status_rows = (
        db.query(models.AutonomyTask.status, func.count(models.AutonomyTask.id))
        .group_by(models.AutonomyTask.status)
        .all()
    )
    by_status = {str(st or "unknown"): int(ct or 0) for st, ct in status_rows}
    pending = (
        db.query(models.AutonomyTask)
        .filter(models.AutonomyTask.status == "awaiting_approval")
        .order_by(models.AutonomyTask.created_at.asc())
        .limit(50)
        .all()
    )
    now = datetime.utcnow()
    pending_ages_sec: list[int] = []
    for row in pending:
        base_ts = row.finished_at or row.updated_at or row.created_at
        pending_ages_sec.append(max(0, int((now - base_ts).total_seconds())))
    retry_pending = (
        db.query(models.AutonomyTask)
        .filter(models.AutonomyTask.status == "queued")
        .filter(models.AutonomyTask.error_message.ilike("%reencaminhada automaticamente%"))
        .count()
    )
    avg_pending_age = int(sum(pending_ages_sec) / len(pending_ages_sec)) if pending_ages_sec else 0
    max_pending_age = max(pending_ages_sec) if pending_ages_sec else 0
    return {
        "totals": {
            "all_tasks": int(sum(by_status.values())),
            "retry_pending": int(retry_pending),
        },
        "by_status": by_status,
        "pending_approvals": {
            "count": len(pending_ages_sec),
            "avg_age_sec": avg_pending_age,
            "max_age_sec": max_pending_age,
        },
    }


@router.get("/admin/executor-observability")
def admin_executor_observability(
    limit_tasks: int = 200,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin),
) -> dict[str, Any]:
    limit_tasks = max(20, min(2000, int(limit_tasks)))
    rows = (
        db.query(models.AutonomyTask)
        .order_by(models.AutonomyTask.created_at.desc())
        .limit(limit_tasks)
        .all()
    )
    by_tool: dict[str, int] = {}
    by_domain: dict[str, int] = {}
    by_route: dict[str, int] = {}
    by_programmatic_check: dict[str, int] = {}
    by_confidence_band: dict[str, int] = {}
    confidence_sum_by_domain: dict[str, float] = {}
    confidence_count_by_domain: dict[str, int] = {}
    confidence_samples_by_domain: dict[str, list[float]] = {}
    failed_by_tool: dict[str, int] = {}
    failed_by_domain: dict[str, int] = {}
    outcomes_by_day: dict[str, dict[str, int]] = {}
    total_steps = 0
    task_outcomes = {"succeeded": 0, "failed": 0, "dead_letter": 0, "awaiting_approval": 0, "cancelled": 0, "queued": 0, "running": 0}
    for row in rows:
        st = str(row.status or "unknown")
        task_outcomes[st] = task_outcomes.get(st, 0) + 1
        day_key = (row.created_at or datetime.utcnow()).strftime("%Y-%m-%d")
        day_bucket = outcomes_by_day.setdefault(day_key, {"succeeded": 0, "failed": 0, "dead_letter": 0})
        if st in day_bucket:
            day_bucket[st] += 1
        for out in _iter_step_outputs(row):
            total_steps += 1
            tool = str(out.get("tool_used") or "unknown")
            domain = str(out.get("domain") or "unknown")
            route = str(out.get("route") or "unknown")
            pcheck = out.get("programmatic_check")
            pcheck_status = str((pcheck or {}).get("status") or "none") if isinstance(pcheck, dict) else "none"
            confidence = out.get("confidence") if isinstance(out.get("confidence"), dict) else {}
            cband = str((confidence or {}).get("band") or "unknown")
            cscore = float((confidence or {}).get("score") or 0.0)
            step_failed = not bool(out.get("ok", False)) or pcheck_status == "failed"
            by_tool[tool] = by_tool.get(tool, 0) + 1
            by_domain[domain] = by_domain.get(domain, 0) + 1
            by_route[route] = by_route.get(route, 0) + 1
            by_programmatic_check[pcheck_status] = by_programmatic_check.get(pcheck_status, 0) + 1
            by_confidence_band[cband] = by_confidence_band.get(cband, 0) + 1
            confidence_sum_by_domain[domain] = confidence_sum_by_domain.get(domain, 0.0) + cscore
            confidence_count_by_domain[domain] = confidence_count_by_domain.get(domain, 0) + 1
            confidence_samples_by_domain.setdefault(domain, []).append(cscore)
            if step_failed:
                failed_by_tool[tool] = failed_by_tool.get(tool, 0) + 1
                failed_by_domain[domain] = failed_by_domain.get(domain, 0) + 1

    top_failed_tools = sorted(failed_by_tool.items(), key=lambda it: it[1], reverse=True)[:10]
    top_failed_domains = sorted(failed_by_domain.items(), key=lambda it: it[1], reverse=True)[:10]
    avg_confidence_by_domain = {
        domain: round(confidence_sum_by_domain[domain] / max(1, confidence_count_by_domain.get(domain, 0)), 4)
        for domain in confidence_sum_by_domain
    }
    drift_by_domain: dict[str, float] = {}
    outlier_domains: list[dict[str, Any]] = []
    for domain, samples in confidence_samples_by_domain.items():
        if len(samples) < 4:
            continue
        mid = len(samples) // 2
        first_avg = _avg(samples[:mid])
        second_avg = _avg(samples[mid:])
        drift = round(second_avg - first_avg, 4)
        drift_by_domain[domain] = drift
        if second_avg < 0.45 or drift <= -0.15:
            outlier_domains.append(
                {
                    "domain": domain,
                    "latest_avg_confidence": round(second_avg, 4),
                    "drift": drift,
                    "reason": "low_confidence" if second_avg < 0.45 else "negative_drift",
                }
            )
    impact_priorities: list[dict[str, Any]] = []
    for domain, fail_count in failed_by_domain.items():
        volume = int(by_domain.get(domain, 0) or 0)
        avg_conf = float(avg_confidence_by_domain.get(domain, 0.0) or 0.0)
        impact = round(float(fail_count) * (1.0 + max(0.0, 1.0 - avg_conf)) * (1.0 + (volume / max(1, total_steps))), 4)
        impact_priorities.append(
            {
                "domain": domain,
                "failures": int(fail_count),
                "volume": volume,
                "avg_confidence": round(avg_conf, 4),
                "impact_score": impact,
            }
        )
    impact_priorities.sort(key=lambda item: item["impact_score"], reverse=True)
    dead_letters = int(task_outcomes.get("dead_letter", 0))
    succeeded = int(task_outcomes.get("succeeded", 0))
    retried_or_terminal = dead_letters + succeeded
    recovery_rate = round((succeeded / retried_or_terminal), 4) if retried_or_terminal > 0 else 0.0
    return {
        "sampled_tasks": len(rows),
        "sampled_steps": total_steps,
        "by_tool": by_tool,
        "by_domain": by_domain,
        "by_route": by_route,
        "by_programmatic_check": by_programmatic_check,
        "by_confidence_band": by_confidence_band,
        "avg_confidence_by_domain": avg_confidence_by_domain,
        "confidence_drift_by_domain": drift_by_domain,
        "outlier_domains": outlier_domains,
        "task_outcomes": task_outcomes,
        "recovery": {
            "recovery_rate": recovery_rate,
            "succeeded": succeeded,
            "dead_letter": dead_letters,
        },
        "timeline": [
            {"date": date, **outcomes_by_day[date]}
            for date in sorted(outcomes_by_day.keys())
        ],
        "top_failures": {
            "tools": [{"tool": name, "count": count} for name, count in top_failed_tools],
            "domains": [{"domain": name, "count": count} for name, count in top_failed_domains],
        },
        "impact_priorities": impact_priorities[:10],
    }


@router.post("/tasks/{task_id}/approve-sensitive", response_model=AutonomyTaskOut)
def approve_sensitive(
    task_id: int,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin),
) -> AutonomyTaskOut:
    row = db.query(models.AutonomyTask).filter(models.AutonomyTask.id == task_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")
    if row.status != "awaiting_approval":
        raise HTTPException(status_code=400, detail="Tarefa não está aguardando aprovação.")
    row = approve_sensitive_task(db, row, approver_user_id=current_admin.id)
    db.refresh(row)
    return _to_out(row)


@router.post("/tasks/{task_id}/reject-sensitive", response_model=AutonomyTaskOut)
def reject_sensitive(
    task_id: int,
    body: AutonomyRejectRequest,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin),
) -> AutonomyTaskOut:
    row = db.query(models.AutonomyTask).filter(models.AutonomyTask.id == task_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")
    if row.status != "awaiting_approval":
        raise HTTPException(status_code=400, detail="Tarefa não está aguardando aprovação.")
    row = reject_sensitive_task(
        db,
        row,
        approver_user_id=current_admin.id,
        reason=(body.reason or "").strip(),
    )
    db.refresh(row)
    return _to_out(row)


@router.post("/tasks/{task_id}/cancel", response_model=AutonomyTaskOut)
def cancel(
    task_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin),
) -> AutonomyTaskOut:
    row = db.query(models.AutonomyTask).filter(models.AutonomyTask.id == task_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")
    if row.status in {"succeeded", "failed", "cancelled"}:
        return _to_out(row)
    cancel_task(task_id)
    # marca como cancel requested; o worker finaliza.
    row.status = "cancelled"
    row.finished_at = datetime.utcnow()
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_out(row)


@router.post("/tasks/{task_id}/requeue", response_model=AutonomyTaskOut)
def requeue_task(
    task_id: int,
    body: AutonomyRequeueRequest,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin),
) -> AutonomyTaskOut:
    row = db.query(models.AutonomyTask).filter(models.AutonomyTask.id == task_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")
    if row.status not in {"failed", "dead_letter", "awaiting_approval", "cancelled"}:
        raise HTTPException(
            status_code=400,
            detail="Só é possível reprocessar tarefas failed/dead_letter/awaiting_approval/cancelled.",
        )
    row = requeue_task_manually(
        db,
        row,
        actor_user_id=current_admin.id,
        reason=(body.reason or "").strip(),
    )
    db.refresh(row)
    return _to_out(row)


@router.get("/admin/sovereign-status")
def admin_sovereign_status(
    _: models.User = Depends(get_current_admin),
) -> dict[str, Any]:
    from vereda_ai.core.config import settings as ai_settings

    providers = llm_engine.available_providers()
    return {
        "sovereign_mode": bool(getattr(ai_settings, "own_model_sovereign_mode", True)),
        "strict_no_fallback": bool(getattr(ai_settings, "own_model_strict_no_fallback", False)),
        "default_provider": llm_engine.default_provider(),
        "available_providers": providers,
        "external_dependency_detected": any(
            p in {"openai", "azure_openai", "azure_tgi", "remote", "local_http", "ollama", "exllama"}
            for p in providers
        ),
    }


@router.post("/admin/evolution/run-once")
def admin_evolution_run_once(
    _: models.User = Depends(get_current_admin),
) -> dict[str, Any]:
    return run_evolution_cycle_once()


@router.post("/admin/evolution/start-loop")
def admin_evolution_start_loop(
    _: models.User = Depends(get_current_admin),
) -> dict[str, Any]:
    return start_evolution_loop()


@router.post("/admin/evolution/stop-loop")
def admin_evolution_stop_loop(
    _: models.User = Depends(get_current_admin),
) -> dict[str, Any]:
    return stop_evolution_loop()


@router.get("/admin/evolution/status")
def admin_evolution_status(
    _: models.User = Depends(get_current_admin),
) -> dict[str, Any]:
    return get_evolution_status()

