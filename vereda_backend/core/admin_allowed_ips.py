"""Lista de IPs autorizados (referência para operações administrativas — persistida em disco)."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List

# Diretório ao lado do pacote (ou em produção sob /opt/syntexa)
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_FILE = _DATA_DIR / "admin_allowed_ips.json"


def _ensure_dir() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_allowed_ips() -> List[str]:
    if not _FILE.is_file():
        return []
    try:
        raw = json.loads(_FILE.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and isinstance(raw.get("ips"), list):
            return [str(x).strip() for x in raw["ips"] if str(x).strip()]
        if isinstance(raw, list):
            return [str(x).strip() for x in raw if str(x).strip()]
    except (OSError, json.JSONDecodeError, TypeError):
        pass
    return []


def save_allowed_ips(ips: List[str]) -> List[str]:
    cleaned: List[str] = []
    for line in ips:
        s = str(line).strip()
        if s and s not in cleaned:
            cleaned.append(s)
    _ensure_dir()
    tmp = _FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps({"ips": cleaned}, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, _FILE)
    return cleaned
