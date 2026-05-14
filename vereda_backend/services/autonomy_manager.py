import threading
import time
import json
from datetime import datetime
from typing import Any, Optional

from vereda_backend.core.config import settings
from vereda_backend.core.access_control import audit_log
from vereda_backend.core.chat_context import get_chat_request_context
from vereda_backend.db import models
from vereda_backend.db.session import SessionLocal

# Lazy import: NÃO carrega agent_system (e toda a stack de IA) no import deste módulo
_agent_system = None


def _get_agent_system():
    global _agent_system
    if _agent_system is None:
        from vereda_backend.ai_runtime import agent_system
        _agent_system = agent_system
    return _agent_system


_LOCK = threading.Lock()
_STARTED = False
_STOP = threading.Event()
_CANCEL: dict[int, threading.Event] = {}


def _now() -> datetime:
    return datetime.utcnow()


def _parse_iso_dt(value: Any) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except Exception:
        return None


def _get_cancel_event(task_id: int) -> threading.Event:
    with _LOCK:
        ev = _CANCEL.get(task_id)
        if ev is None:
            ev = threading.Event()
            _CANCEL[task_id] = ev
        return ev


def cancel_task(task_id: int) -> bool:
    ev = _get_cancel_event(task_id)
    ev.set()
    return True


def _task_has_sensitive_approval(task: models.AutonomyTask) -> bool:
    data = task.outputs_json
    if not isinstance(data, dict):
        return False
    req = data.get("approval_request")
    return bool(isinstance(req, dict) and req.get("approved") is True)


def _task_meta(task: models.AutonomyTask) -> dict[str, Any]:
    data = task.outputs_json
    if isinstance(data, dict):
        meta = data.get("_meta")
        if isinstance(meta, dict):
            return dict(meta)
    return {}


def _set_task_meta(task: models.AutonomyTask, meta: dict[str, Any]) -> None:
    data = task.outputs_json
    payload: dict[str, Any]
    if isinstance(data, dict):
        payload = dict(data)
    elif isinstance(data, list):
        payload = {"result_outputs": data}
    else:
        payload = {}
    payload["_meta"] = dict(meta or {})
    task.outputs_json = payload


def _is_retryable_error(exc: Exception) -> bool:
    txt = str(exc or "").lower()
    retry_markers = (
        "timeout",
        "temporar",
        "connection",
        "rate",
        "unavailable",
        "429",
        "502",
        "503",
        "504",
    )
    return any(k in txt for k in retry_markers)


def _approval_timeout_seconds() -> int:
    return max(60, int(getattr(settings, "autonomy_approval_timeout_sec", 3600) or 3600))


def _tier_limits(user: Optional[models.User]) -> dict[str, Any]:
    # Admin: mais agressivo; outros: limites conservadores.
    if user and bool(getattr(user, "is_admin", False)):
        return {"max_steps": 24, "min_priority": 1}
    plan = (getattr(user, "subscription_plan", None) or "free").strip().lower() if user else "anon"
    if plan in {"master", "gov", "government"}:
        return {"max_steps": 16, "min_priority": 2}
    if plan in {"medium"}:
        return {"max_steps": 12, "min_priority": 3}
    if plan in {"basic"}:
        return {"max_steps": 8, "min_priority": 4}
    return {"max_steps": 6, "min_priority": 5}


def _pick_next_task(db) -> Optional[models.AutonomyTask]:
    # Prioridade menor = mais urgente; FIFO por created_at.
    rows = (
        db.query(models.AutonomyTask)
        .filter(models.AutonomyTask.status == "queued")
        .order_by(models.AutonomyTask.priority.asc(), models.AutonomyTask.created_at.asc())
        .limit(50)
        .all()
    )
    now = _now()
    for row in rows:
        meta = _task_meta(row)
        next_attempt_at = _parse_iso_dt(meta.get("next_attempt_at"))
        if next_attempt_at and now < next_attempt_at:
            continue
        return row
    return None


def _run_once(task: models.AutonomyTask) -> None:
    db = SessionLocal()
    try:
        # Recarrega para garantir estado atual.
        task = db.query(models.AutonomyTask).filter(models.AutonomyTask.id == task.id).first()
        if not task:
            return
        if task.status != "queued":
            return

        user = db.query(models.User).filter(models.User.id == task.user_id).first() if task.user_id else None
        limits = _tier_limits(user)
        cancel_ev = _get_cancel_event(task.id)

        task.status = "running"
        task.started_at = _now()
        db.add(task)
        db.commit()

        if cancel_ev.is_set():
            task.status = "cancelled"
            task.finished_at = _now()
            db.add(task)
            db.commit()
            return

        # Pipeline: Planner -> Task decomposition -> Executor
        # (AgentSystem já encapsula isso). Guardrail: cap de passos por tier.
        allow_sensitive = bool(user and getattr(user, "is_admin", False)) or _task_has_sensitive_approval(task)
        result = _get_agent_system().handle_request(
            task.prompt,
            execution_context={
                "user_id": str(task.user_id or "autonomy-anon"),
                "is_admin": bool(user and getattr(user, "is_admin", False)),
                "subscription_plan": (getattr(user, "subscription_plan", None) or "free") if user else "anon",
                "max_steps": int(limits.get("max_steps", 0) or 0),
                "allow_sensitive_actions": allow_sensitive,
            },
        )
        steps = list(result.steps or [])
        if len(steps) > int(limits["max_steps"]):
            steps = steps[: int(limits["max_steps"])]
        outputs: list[Any] = []
        for out in (result.outputs or [])[: len(steps)]:
            if cancel_ev.is_set():
                task.status = "cancelled"
                task.finished_at = _now()
                task.plan_text = result.plan
                task.steps_json = steps
                task.outputs_json = outputs
                db.add(task)
                db.commit()
                return
            outputs.append(out)

        pending = _extract_pending_sensitive(outputs)
        if pending is not None:
            task.plan_text = result.plan
            task.steps_json = steps
            task.outputs_json = {
                "partial_outputs": outputs,
                "approval_request": pending,
            }
            task.status = "awaiting_approval"
            task.error_message = "Aguardando aprovacao para acao sensivel."
            task.finished_at = _now()
            db.add(task)
            db.commit()
            try:
                audit_log(
                    db,
                    action="autonomy_task_awaiting_approval",
                    user_id=user.id if user else None,
                    resource=f"autonomy_task:{task.id}",
                    detail=json.dumps(pending, ensure_ascii=False)[:1800],
                    ip_address=get_chat_request_context().get("client_ip"),
                )
            except Exception:
                pass
            return

        task.plan_text = result.plan
        task.steps_json = steps
        task.outputs_json = outputs
        task.status = "succeeded"
        task.finished_at = _now()
        db.add(task)
        db.commit()

        try:
            _audit_tool_trace(db, task_id=task.id, user=user, outputs=outputs)
        except Exception:
            pass
        try:
            audit_log(
                db,
                action="autonomy_task_succeeded",
                user_id=user.id if user else None,
                resource=f"autonomy_task:{task.id}",
                detail=str({"steps": len(steps)}),
                ip_address=get_chat_request_context().get("client_ip"),
            )
        except Exception:
            pass
    except Exception as exc:
        try:
            if _handle_retryable_failure(db, task, exc):
                return
            task.status = "failed"
            task.error_message = str(exc)[:1900]
            task.finished_at = _now()
            db.add(task)
            db.commit()
        except Exception:
            pass
    finally:
        db.close()


def _loop() -> None:
    poll = float(getattr(settings, "autonomy_poll_interval_sec", 1.2) or 1.2)
    poll = max(0.25, min(10.0, poll))
    while not _STOP.is_set():
        db = SessionLocal()
        try:
            _expire_pending_approvals(db)
            task = _pick_next_task(db)
        finally:
            db.close()
        if task:
            _run_once(task)
            continue
        _STOP.wait(timeout=poll)


def _handle_retryable_failure(db, task: models.AutonomyTask, exc: Exception) -> bool:
    if not _is_retryable_error(exc):
        return False
    meta = _task_meta(task)
    retry_count = int(meta.get("retry_count", 0) or 0)
    max_retries = max(0, int(getattr(settings, "autonomy_retry_max_attempts", 2) or 2))
    if retry_count >= max_retries:
        meta["dead_letter"] = True
        meta["dead_letter_at"] = _now().isoformat()
        meta["last_error"] = str(exc)[:400]
        _set_task_meta(task, meta)
        task.status = "dead_letter"
        task.error_message = "Falha transitória excedeu retries; movida para dead-letter."
        task.finished_at = _now()
        db.add(task)
        db.commit()
        try:
            audit_log(
                db,
                action="autonomy_task_dead_lettered",
                user_id=task.user_id,
                resource=f"autonomy_task:{task.id}",
                detail=json.dumps(meta, ensure_ascii=False)[:1800],
                ip_address=get_chat_request_context().get("client_ip"),
            )
        except Exception:
            pass
        return True
    backoff_base = max(2, int(getattr(settings, "autonomy_retry_backoff_base_sec", 20) or 20))
    backoff_cap = max(backoff_base, int(getattr(settings, "autonomy_retry_backoff_cap_sec", 300) or 300))
    delay = min(backoff_cap, backoff_base * (2 ** retry_count))
    meta["retry_count"] = retry_count + 1
    meta["last_retry_at"] = _now().isoformat()
    meta["last_error"] = str(exc)[:400]
    meta["next_attempt_at"] = datetime.utcfromtimestamp(_now().timestamp() + delay).isoformat()
    _set_task_meta(task, meta)
    task.status = "queued"
    task.error_message = "Falha transitória; reencaminhada automaticamente em %ss (tentativa %s/%s)." % (
        delay,
        retry_count + 1,
        max_retries,
    )
    task.finished_at = None
    task.started_at = None
    db.add(task)
    db.commit()
    try:
        audit_log(
            db,
            action="autonomy_task_retry_scheduled",
            user_id=task.user_id,
            resource=f"autonomy_task:{task.id}",
            detail=json.dumps(meta, ensure_ascii=False)[:1800],
            ip_address=get_chat_request_context().get("client_ip"),
        )
    except Exception:
        pass
    return True


def _expire_pending_approvals(db) -> None:
    timeout_s = _approval_timeout_seconds()
    now = _now()
    rows = (
        db.query(models.AutonomyTask)
        .filter(models.AutonomyTask.status == "awaiting_approval")
        .order_by(models.AutonomyTask.created_at.asc())
        .limit(100)
        .all()
    )
    for row in rows:
        data = row.outputs_json if isinstance(row.outputs_json, dict) else {}
        req = data.get("approval_request") if isinstance(data, dict) else None
        if not isinstance(req, dict):
            continue
        requested_at = req.get("requested_at")
        try:
            ts = datetime.fromisoformat(str(requested_at))
        except Exception:
            ts = row.finished_at or row.updated_at or row.created_at
        age = (now - ts).total_seconds()
        if age < timeout_s:
            continue
        req["approved"] = False
        req["expired"] = True
        req["expired_at"] = now.isoformat()
        data["approval_request"] = req
        row.outputs_json = data
        row.status = "failed"
        row.error_message = "Aprovação sensível expirou por timeout (%ss)." % timeout_s
        row.finished_at = now
        db.add(row)
        db.commit()
        try:
            audit_log(
                db,
                action="autonomy_sensitive_approval_expired",
                user_id=row.user_id,
                resource=f"autonomy_task:{row.id}",
                detail=json.dumps(req, ensure_ascii=False)[:1800],
                ip_address=get_chat_request_context().get("client_ip"),
            )
        except Exception:
            pass


def _audit_tool_trace(
    db,
    *,
    task_id: int,
    user: Optional[models.User],
    outputs: list[Any],
) -> None:
    uid = user.id if user else None
    for idx, out in enumerate(outputs or []):
        if not isinstance(out, dict):
            continue
        detail = {
            "step_index": idx,
            "route": out.get("route"),
            "tool_used": out.get("tool_used"),
            "domain": out.get("domain"),
            "tool_chain": out.get("tool_chain", []),
            "security": out.get("security"),
            "self_check": out.get("self_check"),
            "programmatic_check": out.get("programmatic_check"),
        }
        audit_log(
            db,
            action="autonomy_tool_step",
            user_id=uid,
            resource=f"autonomy_task:{task_id}",
            detail=json.dumps(detail, ensure_ascii=False)[:1800],
            ip_address=get_chat_request_context().get("client_ip"),
        )


def _extract_pending_sensitive(outputs: list[Any]) -> Optional[dict[str, Any]]:
    for idx, out in enumerate(outputs or []):
        if not isinstance(out, dict):
            continue
        sec = out.get("security")
        if not isinstance(sec, dict):
            continue
        if sec.get("reason") == "pending_sensitive_approval":
            return {
                "requested_at": _now().isoformat(),
                "step_index": idx,
                "route": out.get("route"),
                "task_message": out.get("task"),
                "tool_used": out.get("tool_used"),
                "reason": sec.get("reason"),
                "pattern": sec.get("pattern"),
                "approved": False,
                "approved_by": None,
                "approved_at": None,
            }
    return None


def approve_sensitive_task(db, task: models.AutonomyTask, approver_user_id: Optional[int]) -> models.AutonomyTask:
    data = task.outputs_json if isinstance(task.outputs_json, dict) else {}
    req = data.get("approval_request") if isinstance(data, dict) else None
    if not isinstance(req, dict):
        raise ValueError("Tarefa não possui aprovação pendente.")
    req["approved"] = True
    req["approved_by"] = approver_user_id
    req["approved_at"] = _now().isoformat()
    task.outputs_json = data
    task.status = "queued"
    task.error_message = None
    task.started_at = None
    task.finished_at = None
    db.add(task)
    db.commit()
    try:
        audit_log(
            db,
            action="autonomy_sensitive_approved",
            user_id=approver_user_id,
            resource=f"autonomy_task:{task.id}",
            detail=json.dumps(req, ensure_ascii=False)[:1800],
            ip_address=get_chat_request_context().get("client_ip"),
        )
    except Exception:
        pass
    return task


def reject_sensitive_task(
    db,
    task: models.AutonomyTask,
    approver_user_id: Optional[int],
    reason: str,
) -> models.AutonomyTask:
    data = task.outputs_json if isinstance(task.outputs_json, dict) else {}
    req = data.get("approval_request") if isinstance(data, dict) else {}
    task.status = "failed"
    task.error_message = ("Ação sensível rejeitada: %s" % (reason or "sem motivo informado"))[:1800]
    task.finished_at = _now()
    if isinstance(req, dict):
        req["approved"] = False
        req["rejected_by"] = approver_user_id
        req["rejected_at"] = _now().isoformat()
        req["rejection_reason"] = (reason or "").strip()[:500]
        data["approval_request"] = req
        task.outputs_json = data
    db.add(task)
    db.commit()
    try:
        audit_log(
            db,
            action="autonomy_sensitive_rejected",
            user_id=approver_user_id,
            resource=f"autonomy_task:{task.id}",
            detail=json.dumps(req, ensure_ascii=False)[:1800],
            ip_address=get_chat_request_context().get("client_ip"),
        )
    except Exception:
        pass
    return task


def requeue_task_manually(
    db,
    task: models.AutonomyTask,
    *,
    actor_user_id: Optional[int],
    reason: str = "",
) -> models.AutonomyTask:
    meta = _task_meta(task)
    meta["manual_requeue_at"] = _now().isoformat()
    meta["manual_requeue_by"] = actor_user_id
    if reason:
        meta["manual_requeue_reason"] = reason[:500]
    meta.pop("next_attempt_at", None)
    _set_task_meta(task, meta)
    task.status = "queued"
    task.error_message = ("Reprocessamento manual solicitado. %s" % reason).strip()[:1800]
    task.started_at = None
    task.finished_at = None
    db.add(task)
    db.commit()
    try:
        audit_log(
            db,
            action="autonomy_task_requeued_manual",
            user_id=actor_user_id,
            resource=f"autonomy_task:{task.id}",
            detail=json.dumps(meta, ensure_ascii=False)[:1800],
            ip_address=get_chat_request_context().get("client_ip"),
        )
    except Exception:
        pass
    return task


def start_autonomy_manager() -> None:
    global _STARTED
    with _LOCK:
        if _STARTED:
            return
        _STARTED = True
    t = threading.Thread(target=_loop, name="syntexa-autonomy-manager", daemon=True)
    t.start()


def stop_autonomy_manager() -> None:
    _STOP.set()

