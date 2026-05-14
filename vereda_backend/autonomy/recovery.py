"""
VEREDA / SYNTEXA — Recovery Engine
=====================================
Engine de recuperação com:
- Retry orchestration
- Circuit breaker
- Healthcheck manager
- Intelligent rollback
- Canary deployment
"""

import time
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

log = logging.getLogger(__name__)


class RecoveryAction(Enum):
    RETRY = "retry"
    ROLLBACK = "rollback"
    FAILOVER = "failover"
    ESCALATE = "escalate"
    IGNORE = "ignore"


@dataclass
class FailureEvent:
    service: str
    error: str
    timestamp: float = field(default_factory=time.time)
    severity: str = "medium"  # low, medium, high, critical
    context: Dict[str, Any] = field(default_factory=dict)


class RecoveryEngine:
    """
    Engine de recuperação automática de falhas.
    """

    def __init__(self):
        self._failure_history: List[FailureEvent] = []
        self._recovery_handlers: Dict[str, Callable] = {}
        self._circuit_states: Dict[str, Dict[str, Any]] = {}
        self._stats = {
            "failures_detected": 0,
            "recoveries_successful": 0,
            "recoveries_failed": 0,
            "rollbacks": 0,
            "failovers": 0,
        }

    # ── FAILURE DETECTION ────────────────────────────────────
    def detect_failure(self, service: str, error: str, severity: str = "medium", context: Optional[Dict] = None) -> FailureEvent:
        """Registra e analisa uma falha."""
        event = FailureEvent(
            service=service,
            error=error,
            severity=severity,
            context=context or {},
        )
        self._failure_history.append(event)
        self._stats["failures_detected"] += 1

        # Check for pattern
        recent_failures = [e for e in self._failure_history if e.service == service and (time.time() - e.timestamp) < 300]
        if len(recent_failures) >= 5:
            event.severity = "critical"
            log.critical("Critical failure pattern detected for %s: %d failures in 5min", service, len(recent_failures))

        return event

    # ── RECOVERY ORCHESTRATION ───────────────────────────────
    def recover(self, event: FailureEvent) -> Dict[str, Any]:
        """
        Orquestra recuperação baseada na falha.
        """
        action = self._determine_action(event)
        log.info("Recovering %s with action: %s", event.service, action.value)

        if action == RecoveryAction.RETRY:
            return self._execute_retry(event)
        elif action == RecoveryAction.ROLLBACK:
            return self._execute_rollback(event)
        elif action == RecoveryAction.FAILOVER:
            return self._execute_failover(event)
        elif action == RecoveryAction.ESCALATE:
            return self._execute_escalation(event)
        else:
            return {"status": "ignored", "reason": "Action set to ignore"}

    def _determine_action(self, event: FailureEvent) -> RecoveryAction:
        """Determina ação de recuperação."""
        # Critical failures → failover
        if event.severity == "critical":
            return RecoveryAction.FAILOVER

        # Transient errors → retry
        transient_patterns = ["timeout", "connection", "temporary", "503", "502", "504"]
        if any(p in event.error.lower() for p in transient_patterns):
            return RecoveryAction.RETRY

        # Data corruption → rollback
        if any(p in event.error.lower() for p in ["corrupt", "invalid", "checksum", "integrity"]):
            return RecoveryAction.ROLLBACK

        # Default: escalate
        return RecoveryAction.ESCALATE

    def _execute_retry(self, event: FailureEvent) -> Dict[str, Any]:
        """Executa retry com backoff exponencial."""
        service = event.service
        retry_count = event.context.get("retry_count", 0)
        max_retries = event.context.get("max_retries", 3)

        if retry_count >= max_retries:
            return self._execute_failover(event)

        # Exponential backoff
        delay = min(2 ** retry_count, 60)
        time.sleep(delay)

        handler = self._recovery_handlers.get(f"{service}_retry")
        if handler:
            try:
                result = handler(event.context)
                self._stats["recoveries_successful"] += 1
                return {"status": "recovered", "method": "retry", "result": result}
            except Exception as e:
                event.context["retry_count"] = retry_count + 1
                return self._execute_retry(event)

        return {"status": "failed", "reason": "No retry handler registered"}

    def _execute_rollback(self, event: FailureEvent) -> Dict[str, Any]:
        """Executa rollback para estado anterior."""
        handler = self._recovery_handlers.get(f"{event.service}_rollback")
        if handler:
            try:
                result = handler(event.context)
                self._stats["rollbacks"] += 1
                self._stats["recoveries_successful"] += 1
                return {"status": "rolled_back", "result": result}
            except Exception as e:
                return {"status": "rollback_failed", "error": str(e)}

        return {"status": "failed", "reason": "No rollback handler registered"}

    def _execute_failover(self, event: FailureEvent) -> Dict[str, Any]:
        """Executa failover para backup."""
        handler = self._recovery_handlers.get(f"{event.service}_failover")
        if handler:
            try:
                result = handler(event.context)
                self._stats["failovers"] += 1
                self._stats["recoveries_successful"] += 1
                return {"status": "failover_complete", "result": result}
            except Exception as e:
                return {"status": "failover_failed", "error": str(e)}

        return {"status": "failed", "reason": "No failover handler registered"}

    def _execute_escalation(self, event: FailureEvent) -> Dict[str, Any]:
        """Escalation para admin/alerta."""
        log.critical("ESCALATION: Service %s failed: %s", event.service, event.error)
        return {
            "status": "escalated",
            "service": event.service,
            "error": event.error,
            "timestamp": event.timestamp,
        }

    # ── CIRCUIT BREAKER ──────────────────────────────────────
    def update_circuit(self, service: str, success: bool) -> Dict[str, Any]:
        """Atualiza estado do circuit breaker."""
        if service not in self._circuit_states:
            self._circuit_states[service] = {
                "failures": 0,
                "successes": 0,
                "state": "closed",
                "last_failure": None,
            }

        state = self._circuit_states[service]

        if success:
            state["successes"] += 1
            state["failures"] = max(0, state["failures"] - 1)
            if state["state"] == "half_open" and state["successes"] >= 3:
                state["state"] = "closed"
        else:
            state["failures"] += 1
            state["successes"] = 0
            state["last_failure"] = time.time()
            if state["failures"] >= 5:
                state["state"] = "open"
            elif state["state"] == "open" and (time.time() - state["last_failure"]) > 30:
                state["state"] = "half_open"

        return {
            "service": service,
            "circuit_state": state["state"],
            "failures": state["failures"],
            "successes": state["successes"],
        }

    def is_circuit_open(self, service: str) -> bool:
        state = self._circuit_states.get(service, {})
        return state.get("state") == "open"

    # ── HANDLER REGISTRATION ─────────────────────────────────
    def register_handler(self, action_type: str, handler: Callable) -> None:
        self._recovery_handlers[action_type] = handler

    # ── STATS ────────────────────────────────────────────────
    def get_stats(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "circuit_breakers": len(self._circuit_states),
            "failure_history_size": len(self._failure_history),
        }
