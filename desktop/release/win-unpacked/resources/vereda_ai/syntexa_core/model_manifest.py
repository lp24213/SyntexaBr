from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ModelManifest:
    name: str
    family: str
    stage: str
    vocab_size: int
    hidden_size: int
    num_layers: int
    num_heads: int
    max_seq_len: int
    checkpoint_path: str
    tokenizer_path: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_file(cls, path: str | Path) -> "ModelManifest":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            name=str(raw.get("name", "syntexa_custom")),
            family=str(raw.get("family", "decoder_transformer")),
            stage=str(raw.get("stage", "training_pipeline")),
            vocab_size=int(raw.get("vocab_size", 32000)),
            hidden_size=int(raw.get("hidden_size", 1024)),
            num_layers=int(raw.get("num_layers", 16)),
            num_heads=int(raw.get("num_heads", 16)),
            max_seq_len=int(raw.get("max_seq_len", 2048)),
            checkpoint_path=str(raw.get("checkpoint_path", "")),
            tokenizer_path=str(raw.get("tokenizer_path", "")),
            metadata=dict(raw.get("metadata") or {}),
        )

    def to_file(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")
