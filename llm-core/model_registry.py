from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ModelSpec:
    model_id: str
    family: str
    path: str
    quantization: str
    context_window: int
    enabled: bool = True


class ModelRegistry:
    def __init__(self) -> None:
        self._models: Dict[str, ModelSpec] = {}
        self._active_model_id: str | None = None

    def register(self, spec: ModelSpec) -> None:
        self._models[spec.model_id] = spec
        if self._active_model_id is None and spec.enabled:
            self._active_model_id = spec.model_id

    def list_models(self) -> List[ModelSpec]:
        return list(self._models.values())

    def set_active_model(self, model_id: str) -> None:
        if model_id not in self._models:
            raise ValueError(f"Unknown model: {model_id}")
        if not self._models[model_id].enabled:
            raise ValueError(f"Model is disabled: {model_id}")
        self._active_model_id = model_id

    def active_model(self) -> ModelSpec:
        if not self._active_model_id:
            raise RuntimeError("No active model configured")
        return self._models[self._active_model_id]

