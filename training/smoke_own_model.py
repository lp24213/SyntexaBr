#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _write_tiny_dataset(path: Path) -> None:
    rows = [
        {"text": "A Syntexa é uma plataforma de inteligência artificial proprietária."},
        {"text": "Modelos autoregressivos preveem o próximo token de uma sequência."},
        {"text": "Treinamento envolve otimização de perda de entropia cruzada."},
        {"text": "A IA deve responder com clareza, objetividade e contexto."},
    ]
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def main() -> None:
    try:
        import torch  # noqa: F401
    except Exception:
        raise SystemExit("Torch não instalado. Rode: pip install -r requirements-research.txt")

    from training.train_small_model import main as train_main

    with tempfile.TemporaryDirectory(prefix="syntexa-smoke-") as td:
        root = Path(td)
        data = root / "tiny.jsonl"
        ckpt = root / "ckpt"
        _write_tiny_dataset(data)

        argv = [
            "train_small_model.py",
            "--data",
            str(data),
            "--checkpoints",
            str(ckpt),
            "--epochs",
            "1",
            "--steps-per-epoch",
            "5",
            "--batch-size",
            "2",
            "--hidden-size",
            "128",
            "--layers",
            "2",
            "--heads",
            "4",
            "--seq-len",
            "16",
            "--vocab-size",
            "512",
            "--model-name",
            "syntexa_smoke",
            "--device",
            "cpu",
        ]
        prev = sys.argv[:]
        try:
            sys.argv = argv
            train_main()
        finally:
            sys.argv = prev

        mf = ckpt / "manifest.json"
        if not mf.is_file():
            raise SystemExit("Smoke falhou: manifest não foi gerado.")
        print("Smoke test concluído com sucesso.")
        print(f"Artefatos em: {ckpt}")


if __name__ == "__main__":
    main()
