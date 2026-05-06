"""
Registo de modelos Syntexa (versões internas, checkpoints Azure Blob, etc.).
Ficheiro opcional: `config/syntexa_model_registry.json` na raiz do repo (ou cwd).
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ModelEntry:
    name: str
    stage: str  # e.g. native_hybrid | syntexa_small | syntexa_medium
    checkpoint_uri: str | None = None
    params_millions: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def _registry_paths() -> list[Path]:
    root = Path(os.getenv("SYNTEXA_REPO_ROOT", ".")).resolve()
    return [
        root / "config" / "syntexa_model_registry.json",
        root / "syntexa_config" / "model_registry.json",
    ]


def load_registry_file() -> dict[str, Any]:
    for p in _registry_paths():
        if p.is_file():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
    return {
        "active": "syntexa_native",
        "models": [
            {
                "name": "syntexa_native",
                "stage": "native_hybrid",
                "params_millions": 0,
                "checkpoint_uri": None,
            }
        ],
    }


class ModelRegistry:
    def __init__(self) -> None:
        self._raw = load_registry_file()
        self.active = str(self._raw.get("active") or "syntexa_native")
        self.models: list[ModelEntry] = []
        for m in self._raw.get("models") or []:
            if not isinstance(m, dict):
                continue
            self.models.append(
                ModelEntry(
                    name=str(m.get("name", "unknown")),
                    stage=str(m.get("stage", "unknown")),
                    checkpoint_uri=m.get("checkpoint_uri"),
                    params_millions=m.get("params_millions"),
                    metadata={k: v for k, v in m.items() if k not in ("name", "stage", "checkpoint_uri", "params_millions")},
                )
            )

    def get_active(self) -> ModelEntry | None:
        for m in self.models:
            if m.name == self.active:
                return m
        return self.models[0] if self.models else None


_registry: ModelRegistry | None = None


def get_registry() -> ModelRegistry:
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry


def _primary_registry_path() -> Path:
    return _registry_paths()[0]


def save_registry_file(raw: dict[str, Any]) -> None:
    p = _primary_registry_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")


def reload_registry() -> ModelRegistry:
    global _registry
    _registry = ModelRegistry()
    return _registry


def set_active_model(name: str) -> ModelRegistry:
    raw = load_registry_file()
    models = raw.get("models") or []
    if not any(str(m.get("name", "")).strip() == name for m in models if isinstance(m, dict)):
        raise ValueError(f"Modelo '{name}' não encontrado no registry.")
    raw["active"] = name
    save_registry_file(raw)
    return reload_registry()
