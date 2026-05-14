from dataclasses import dataclass
from time import perf_counter
from typing import Protocol


@dataclass
class RuntimeRequest:
    queue_depth: int
    expected_latency_ms: int
    complexity_score: float
    energy_budget_watts: float


class RegistryLike(Protocol):
    def active_model(self): ...


class SchedulerLike(Protocol):
    def select_target(self, request: RuntimeRequest) -> str: ...


class GuardrailsLike(Protocol):
    def inspect_prompt(self, prompt: str): ...


@dataclass
class InferenceResponse:
    text: str
    model_id: str
    runtime_target: str
    source: str
    latency_ms: int


class SovereignInferenceEngine:
    def __init__(
        self,
        registry: RegistryLike,
        scheduler: SchedulerLike,
        guardrails: GuardrailsLike,
    ) -> None:
        self.registry = registry
        self.scheduler = scheduler
        self.guardrails = guardrails

    def generate(self, prompt: str, complexity_score: float = 0.5) -> InferenceResponse:
        start = perf_counter()
        verdict = self.guardrails.inspect_prompt(prompt)
        if not verdict.allowed:
            return InferenceResponse(
                text=f"Request blocked by security policy ({verdict.reason}).",
                model_id="none",
                runtime_target="none",
                source="local",
                latency_ms=int((perf_counter() - start) * 1000),
            )

        model = self.registry.active_model()
        target = self.scheduler.select_target(
            RuntimeRequest(
                queue_depth=1,
                expected_latency_ms=180,
                complexity_score=complexity_score,
                energy_budget_watts=120,
            )
        )

        # Placeholder for local inference call (vLLM/ONNX/TensorRT path).
        text = f"[{model.model_id} @ {target}] Resposta local soberana para: {verdict.sanitized_prompt}"
        return InferenceResponse(
            text=text,
            model_id=model.model_id,
            runtime_target=target,
            source="local",
            latency_ms=int((perf_counter() - start) * 1000),
        )

