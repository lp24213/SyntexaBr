#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description="Ativa modelo proprietário no registry Syntexa")
    ap.add_argument("--name", required=True, help="Nome do modelo (ex.: syntexa_small)")
    ap.add_argument("--manifest", required=True, help="Caminho do manifest.json do modelo")
    ap.add_argument("--registry", default="config/syntexa_model_registry.json")
    args = ap.parse_args()

    reg_path = Path(args.registry)
    reg_path.parent.mkdir(parents=True, exist_ok=True)
    if reg_path.is_file():
        raw = json.loads(reg_path.read_text(encoding="utf-8"))
    else:
        raw = {"active": "", "models": []}

    models = list(raw.get("models") or [])
    name = str(args.name).strip()
    manifest = Path(args.manifest).resolve()
    found = False
    for m in models:
        if str(m.get("name", "")).strip() == name:
            m["stage"] = "training_pipeline"
            m["checkpoint_uri"] = str(manifest.parent / "weights.pt")
            m["manifest_path"] = str(manifest)
            found = True
            break
    if not found:
        models.append(
            {
                "name": name,
                "stage": "training_pipeline",
                "params_millions": None,
                "checkpoint_uri": str(manifest.parent / "weights.pt"),
                "manifest_path": str(manifest),
            }
        )

    raw["active"] = name
    raw["models"] = models
    reg_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Modelo ativo: {name}")
    print(f"Registry atualizado: {reg_path.resolve()}")


if __name__ == "__main__":
    main()
