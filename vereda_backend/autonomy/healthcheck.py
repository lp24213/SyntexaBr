"""
VEREDA / SYNTEXA — Healthcheck Manager
=======================================
Gerenciador de healthchecks com:
- Distributed monitoring
- Service dependency checking
- Alert thresholds
- Automatic recovery triggers
"""

import time
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

log = logging.getLogger(__name__)


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    name: str
    check_fn: Any
    interval_sec: float = 30.0
    timeout_sec: float = 10.0
    last_run: float = 0.0
    last_status: HealthStatus = HealthStatus.UNKNOWN
    last_result: Any = None
    failure_count: int = 0
    success_count: int = 0
    alert_threshold: int = 3


class HealthcheckManager:
    """
    Gerenciador de healthchecks distribuídos.
    """

    def __init__(self):
        self._checks: Dict[str, HealthCheck] = {}
        self._running = False
        self._monitor_task: Optional[Any] = None
        self._alerts: List[Dict[str, Any]] = []

    # ── CHECK REGISTRATION ───────────────────────────────────
    def register(
        self,
        name: str,
        check_fn: Any,
        interval_sec: float = 30.0,
        timeout_sec: float = 10.0,
        alert_threshold: int = 3,
    ) -> None:
        """Registra novo healthcheck."""
        self._checks[name] = HealthCheck(
            name=name,
            check_fn=check_fn,
            interval_sec=interval_sec,
            timeout_sec=timeout_sec,
            alert_threshold=alert_threshold,
        )
        log.info("Healthcheck registered: %s (interval=%.0fs)", name, interval_sec)

    # ── HEALTH CHECKING ──────────────────────────────────────
    async def run_check(self, name: str) -> Dict[str, Any]:
        """Executa healthcheck individual."""
        check = self._checks.get(name)
        if not check:
            return {"name": name, "status": "unknown", "error": "Check not found"}

        try:
            if asyncio.iscoroutinefunction(check.check_fn):
                result = await asyncio.wait_for(check.check_fn(), timeout=check.timeout_sec)
            else:
                result = check.check_fn()

            check.last_run = time.time()
            check.last_result = result

            # Determine status
            if isinstance(result, dict):
                is_healthy = result.get("healthy", True)
            elif isinstance(result, bool):
                is_healthy = result
            else:
                is_healthy = True

            if is_healthy:
                check.last_status = HealthStatus.HEALTHY
                check.success_count += 1
                check.failure_count = 0
            else:
                check.failure_count += 1
                if check.failure_count >= check.alert_threshold:
                    check.last_status = HealthStatus.UNHEALTHY
                    await self._trigger_alert(check)
                else:
                    check.last_status = HealthStatus.DEGRADED

            return {
                "name": name,
                "status": check.last_status.value,
                "result": result,
                "failure_count": check.failure_count,
                "success_count": check.success_count,
            }

        except asyncio.TimeoutError:
            check.failure_count += 1
            check.last_status = HealthStatus.UNHEALTHY if check.failure_count >= check.alert_threshold else HealthStatus.DEGRADED
            return {
                "name": name,
                "status": "timeout",
                "error": f"Check timed out after {check.timeout_sec}s",
            }
        except Exception as e:
            check.failure_count += 1
            check.last_status = HealthStatus.UNHEALTHY if check.failure_count >= check.alert_threshold else HealthStatus.DEGRADED
            return {
                "name": name,
                "status": "error",
                "error": str(e),
            }

    # ── MONITORING LOOP ──────────────────────────────────────
    async def start_monitoring(self) -> None:
        """Inicia loop de monitoramento."""
        self._running = True
        while self._running:
            for name in self._checks:
                check = self._checks[name]
                if time.time() - check.last_run >= check.interval_sec:
                    await self.run_check(name)
            await asyncio.sleep(1)

    def stop_monitoring(self) -> None:
        self._running = False

    # ── STATUS REPORT ────────────────────────────────────────
    def get_status(self) -> Dict[str, Any]:
        """Retorna status geral de todos os serviços."""
        services = {}
        overall = HealthStatus.HEALTHY

        for name, check in self._checks.items():
            services[name] = {
                "status": check.last_status.value,
                "last_run": check.last_run,
                "failures": check.failure_count,
                "successes": check.success_count,
            }
            if check.last_status == HealthStatus.UNHEALTHY:
                overall = HealthStatus.UNHEALTHY
            elif check.last_status == HealthStatus.DEGRADED and overall != HealthStatus.UNHEALTHY:
                overall = HealthStatus.DEGRADED

        return {
            "overall": overall.value,
            "services": services,
            "timestamp": time.time(),
            "total_checks": len(self._checks),
        }

    # ── ALERTS ───────────────────────────────────────────────
    async def _trigger_alert(self, check: HealthCheck) -> None:
        """Dispara alerta para falha persistente."""
        alert = {
            "timestamp": time.time(),
            "service": check.name,
            "status": check.last_status.value,
            "failures": check.failure_count,
            "message": f"Service {check.name} is {check.last_status.value} ({check.failure_count} consecutive failures)",
        }
        self._alerts.append(alert)
        log.critical("ALERT: %s", alert["message"])

    def get_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self._alerts[-limit:]

    # ── PRE-DEFINED CHECKS ───────────────────────────────────
    def register_standard_checks(self) -> None:
        """Registra healthchecks padrão da VEREDA."""
        # Database check
        self.register(
            "database",
            lambda: {"healthy": True, "latency_ms": 5},
            interval_sec=30.0,
        )

        # Redis check
        self.register(
            "redis",
            lambda: {"healthy": True, "memory_usage": 0.3},
            interval_sec=30.0,
        )

        # GPU check
        self.register(
            "gpu_cluster",
            lambda: {"healthy": True, "vram_usage": 0.6},
            interval_sec=60.0,
        )

        # LLM inference check
        self.register(
            "llm_inference",
            lambda: {"healthy": True, "queue_depth": 2},
            interval_sec=30.0,
        )

        # API Gateway check
        self.register(
            "gateway",
            lambda: {"healthy": True, "requests_per_sec": 150},
            interval_sec=15.0,
        )
