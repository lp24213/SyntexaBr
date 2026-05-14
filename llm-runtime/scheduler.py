from dataclasses import dataclass


@dataclass
class RuntimeRequest:
    queue_depth: int
    expected_latency_ms: int
    complexity_score: float
    energy_budget_watts: float


class RuntimeScheduler:
    def select_target(self, request: RuntimeRequest) -> str:
        if request.expected_latency_ms <= 200 and request.complexity_score >= 0.7:
            return "gpu_tensorrt"
        if request.complexity_score >= 0.5:
            return "gpu_cuda"
        if request.energy_budget_watts < 80:
            return "cpu"
        return "edge_wasm"

