"""Armazenamento temporário de ficheiros gerados + limpeza."""
from __future__ import annotations

import os
import re
import time
import uuid
from pathlib import Path

from vereda_backend.core.config import settings

_SAFE_ID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)


def get_generated_dir() -> Path:
    raw = (getattr(settings, "generated_files_dir", None) or "").strip()
    if raw:
        p = Path(raw)
    else:
        p = Path(os.environ.get("TMPDIR") or os.environ.get("TEMP") or "/tmp") / "syntexa_generated"
    p.mkdir(parents=True, exist_ok=True)
    return p


def cleanup_old_files(*, max_age_seconds: int = 86_400) -> int:
    """Remove ficheiros mais antigos que max_age_seconds (predefinição 24 h)."""
    base = get_generated_dir()
    now = time.time()
    removed = 0
    try:
        for path in base.iterdir():
            if not path.is_file():
                continue
            try:
                if now - path.stat().st_mtime > max_age_seconds:
                    path.unlink()
                    removed += 1
            except OSError:
                continue
    except OSError:
        pass
    return removed


def save_generated_bytes(content: bytes, suffix: str) -> str:
    """
    Grava bytes no disco; devolve UUID (sem sufixo) para uso em URLs.
    Executa limpeza antes de gravar.
    """
    cleanup_old_files()
    uid = str(uuid.uuid4())
    suf = suffix if suffix.startswith(".") else f".{suffix}"
    path = get_generated_dir() / f"{uid}{suf}"
    path.write_bytes(content)
    return uid


def resolve_generated_path(file_id: str, suffix: str) -> Path | None:
    if not _SAFE_ID.match(file_id or ""):
        return None
    suf = suffix if suffix.startswith(".") else f".{suffix}"
    p = get_generated_dir() / f"{file_id}{suf}"
    if p.is_file():
        return p
    return None
