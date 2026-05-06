"""
Exporta dataset anonimizado de conversas para treino futuro da Syntexa.

Uso:
  python scripts/export_training_dataset.py --output training/datasets/syntexa_dialogs.jsonl
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from vereda_backend.db.session import SessionLocal
from vereda_backend.db import models


def anonymize_user(user_id: int | None) -> str:
    return f"user_{(user_id or 0) % 1000000}"


def run(output: Path) -> int:
    db = SessionLocal()
    count = 0
    try:
        rows = (
            db.query(models.Message)
            .filter(models.Message.role.in_(["user", "assistant"]))
            .order_by(models.Message.created_at.asc())
            .all()
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as f:
            for r in rows:
                payload = {
                    "conversation_id": r.conversation_id,
                    "user_hash": anonymize_user(r.user_id),
                    "role": r.role,
                    "content": r.content,
                    "language": r.language,
                    "subject": r.subject,
                    "sentiment": r.sentiment,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
                count += 1
    finally:
        db.close()
    return count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    n = run(Path(args.output))
    print(f"exported_records={n}")


if __name__ == "__main__":
    main()
