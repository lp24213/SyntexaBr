"""
VEREDA / SYNTEXA — Sovereign Orchestrator
==========================================
Camada de orquestração production-grade para o motor neural.
Inclui: circuit breaker, retry exponencial, health checks,
model fallback chain, métricas e graceful degradation.
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Iterator, Optional

logger = logging.getLogger(__name__)


# ── Circuit Breaker ────────────────────────────────────────────
class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject fast
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker para proteger o motor neural contra cascata de falhas.
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 2,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = threading.RLock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._last_failure_time and (time.time() - self._last_failure_time) >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    logger.info("[CircuitBreaker] HALF_OPEN — testando recuperação")
            return self._state

    def call(self, fn: Callable, *args, **kwargs) -> Any:
        st = self.state
        if st == CircuitState.OPEN:
            raise RuntimeError("[CircuitBreaker] OPEN — motor neural temporariamente indisponível")

        if st == CircuitState.HALF_OPEN:
            with self._lock:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise RuntimeError("[CircuitBreaker] HALF_OPEN limite atingido")
                self._half_open_calls += 1

        try:
            result = fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.half_open_max_calls:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    logger.info("[CircuitBreaker] CLOSED — recuperação confirmada")
            else:
                self._failure_count = max(0, self._failure_count - 1)

    def _on_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.warning("[CircuitBreaker] OPEN — falha em HALF_OPEN")
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning("[CircuitBreaker] OPEN — threshold de falhas atingido (%d)", self._failure_count)


# ── Retry with Exponential Backoff ───────────────────────────────
def retry_with_backoff(
    fn: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    exceptions: tuple = (Exception,),
) -> Any:
    """Executa fn com retry e backoff exponencial."""
    last_exc: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except exceptions as e:
            last_exc = e
            if attempt == max_retries:
                break
            delay = min(base_delay * (2 ** attempt), max_delay)
            logger.warning("[Retry] Tentativa %d falhou, aguardando %.1fs: %s", attempt + 1, delay, e)
            time.sleep(delay)
    raise last_exc if last_exc else RuntimeError("Retry falhou")


# ── Metrics ─────────────────────────────────────────────────────
@dataclass
class InferenceMetrics:
    total_calls: int = 0
    total_errors: int = 0
    total_tokens: int = 0
    total_latency_ms: float = 0.0
    model_load_time_ms: float = 0.0
    last_error: Optional[str] = None
    last_success_time: Optional[float] = None

    @property
    def avg_latency_ms(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.total_latency_ms / self.total_calls

    @property
    def error_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.total_errors / self.total_calls

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_calls": self.total_calls,
            "total_errors": self.total_errors,
            "total_tokens": self.total_tokens,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "error_rate": round(self.error_rate, 4),
            "model_load_time_ms": round(self.model_load_time_ms, 2),
            "last_error": self.last_error,
            "last_success_time": self.last_success_time,
        }


# ── Health Checker ──────────────────────────────────────────────
class HealthChecker:
    """Verifica saúde periódica do motor neural."""

    def __init__(self, check_interval: float = 30.0):
        self.check_interval = check_interval
        self._healthy = True
        self._last_check: Optional[float] = None
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self, check_fn: Callable[[], bool]) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()

        def _loop():
            while not self._stop_event.is_set():
                try:
                    healthy = check_fn()
                    with self._lock:
                        self._healthy = healthy
                        self._last_check = time.time()
                    if not healthy:
                        logger.warning("[HealthChecker] Motor neural não saudável")
                except Exception as e:
                    logger.error("[HealthChecker] Erro na verificação: %s", e)
                    with self._lock:
                        self._healthy = False
                self._stop_event.wait(self.check_interval)

        self._thread = threading.Thread(target=_loop, daemon=True, name="health-checker")
        self._thread.start()
        logger.info("[HealthChecker] Iniciado (intervalo=%.0fs)", self.check_interval)

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5.0)

    @property
    def is_healthy(self) -> bool:
        with self._lock:
            return self._healthy


# ── Model Fallback Chain ──────────────────────────────────────
class ModelFallbackChain:
    """
    Cadeia de fallback: tenta modelos grandes primeiro,
    cai para menores se houver falha de memória ou timeout.
    """

    FALLBACK_CHAIN = [
        "Qwen/Qwen2.5-32B-Instruct",
        "Qwen/Qwen2.5-14B-Instruct",
        "microsoft/phi-4",
        "meta-llama/Llama-3.1-8B-Instruct",
    ]

    def __init__(self):
        self._engines: dict[str, Any] = {}
        self._current_index = 0
        self._lock = threading.RLock()

    def get_engine(self) -> tuple[str, Any]:
        """Retorna o próximo motor disponível na cadeia."""
        from vereda_ai.syntexa_core.neural_engine import NeuralEngine

        with self._lock:
            for i in range(self._current_index, len(self.FALLBACK_CHAIN)):
                model_name = self.FALLBACK_CHAIN[i]
                if model_name not in self._engines:
                    try:
                        logger.info("[FallbackChain] Tentando carregar: %s", model_name)
                        engine = NeuralEngine(model_name=model_name, load_in_4bit=True)
                        if engine.is_available():
                            self._engines[model_name] = engine
                            self._current_index = i
                            logger.info("[FallbackChain] Usando: %s", model_name)
                            return model_name, engine
                    except Exception as e:
                        logger.warning("[FallbackChain] %s indisponível: %s", model_name, e)
                        continue
                else:
                    return model_name, self._engines[model_name]
            raise RuntimeError("[FallbackChain] Nenhum modelo disponível na cadeia de fallback")

    def downgrade(self) -> None:
        """Força downgrade para o próximo modelo."""
        with self._lock:
            if self._current_index < len(self.FALLBACK_CHAIN) - 1:
                self._current_index += 1
                logger.info("[FallbackChain] Downgrade para: %s", self.FALLBACK_CHAIN[self._current_index])


# ── Sovereign Orchestrator (Singleton) ───────────────────────────
class SovereignOrchestrator:
    """
    Orquestrador soberano production-grade.
    Combina circuit breaker, retry, health checks, fallback chain e métricas.
    """

    def __init__(self):
        self._breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
        self._health = HealthChecker(check_interval=30.0)
        self._fallback = ModelFallbackChain()
        self._metrics = InferenceMetrics()
        self._lock = threading.RLock()
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return
        # Start health checking
        self._health.start(self._health_check)
        self._initialized = True
        logger.info("[SovereignOrchestrator] Inicializado")

    def _health_check(self) -> bool:
        try:
            _, engine = self._fallback.get_engine()
            return engine.is_available()
        except Exception:
            return False

    def generate(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        self.initialize()
        t0 = time.time()

        def _do_generate():
            _, engine = self._fallback.get_engine()
            return engine.generate(messages, **kwargs)

        try:
            result = self._breaker.call(
                lambda: retry_with_backoff(_do_generate, max_retries=2, base_delay=0.5)
            )
            latency = (time.time() - t0) * 1000
            with self._lock:
                self._metrics.total_calls += 1
                self._metrics.total_latency_ms += latency
                self._metrics.last_success_time = time.time()
            logger.info("[SovereignOrchestrator] Geração OK em %.0fms", latency)
            return result
        except Exception as e:
            with self._lock:
                self._metrics.total_errors += 1
                self._metrics.last_error = str(e)
            logger.error("[SovereignOrchestrator] Falha após retry: %s", e)
            raise

    def generate_stream(self, messages: list[dict[str, Any]], **kwargs: Any) -> Iterator[str]:
        self.initialize()
        t0 = time.time()

        def _do_stream():
            _, engine = self._fallback.get_engine()
            return engine.generate_stream(messages, **kwargs)

        try:
            # Circuit breaker para stream (one-shot)
            st = self._breaker.state
            if st == CircuitState.OPEN:
                raise RuntimeError("Circuit breaker OPEN")

            _, engine = self._fallback.get_engine()
            tokens = 0
            for token in engine.generate_stream(messages, **kwargs):
                tokens += 1
                yield token

            latency = (time.time() - t0) * 1000
            with self._lock:
                self._metrics.total_calls += 1
                self._metrics.total_tokens += tokens
                self._metrics.total_latency_ms += latency
                self._metrics.last_success_time = time.time()
            self._breaker._on_success()
            logger.info("[SovereignOrchestrator] Stream OK: %d tokens em %.0fms", tokens, latency)
        except Exception as e:
            with self._lock:
                self._metrics.total_errors += 1
                self._metrics.last_error = str(e)
            self._breaker._on_failure()
            logger.error("[SovereignOrchestrator] Stream falhou: %s", e)
            raise

    def get_metrics(self) -> dict[str, Any]:
        with self._lock:
            return self._metrics.to_dict()

    def get_health(self) -> dict[str, Any]:
        return {
            "healthy": self._health.is_healthy,
            "circuit_state": self._breaker.state.value,
            "current_model": self._fallback.FALLBACK_CHAIN[self._fallback._current_index],
            "metrics": self.get_metrics(),
        }

    def shutdown(self) -> None:
        self._health.stop()
        logger.info("[SovereignOrchestrator] Encerrado")


# ── Singleton ────────────────────────────────────────────────
_orchestrator: Optional[SovereignOrchestrator] = None
_orchestrator_lock = threading.Lock()


def get_orchestrator() -> SovereignOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        with _orchestrator_lock:
            if _orchestrator is None:
                _orchestrator = SovereignOrchestrator()
    return _orchestrator


def orchestrated_generate(messages: list[dict[str, Any]], **kwargs: Any) -> str:
    """Geração via orquestrador production-grade."""
    return get_orchestrator().generate(messages, **kwargs)


def orchestrated_generate_stream(messages: list[dict[str, Any]], **kwargs: Any) -> Iterator[str]:
    """Streaming via orquestrador production-grade."""
    return get_orchestrator().generate_stream(messages, **kwargs)


def get_system_health() -> dict[str, Any]:
    """Retorna health check completo do sistema."""
    return get_orchestrator().get_health()


def get_system_metrics() -> dict[str, Any]:
    """Retorna métricas de inferência."""
    return get_orchestrator().get_metrics()
