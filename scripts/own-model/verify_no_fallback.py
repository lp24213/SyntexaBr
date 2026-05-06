#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vereda_ai.core.config import settings
from vereda_ai.syntexa_core.runtime_model import runtime_ready_for_active_model
from vereda_ai.syntexa_core.model_registry import get_registry


def main() -> None:
    reg = get_registry()
    active = reg.get_active()
    strict = bool(getattr(settings, "own_model_strict_no_fallback", False))
    env = str(getattr(settings, "environment", "") or "").lower()
    prod = env in {"prod", "production"}
    ok, reason = runtime_ready_for_active_model()
    print(f"environment={env or 'local'} strict={strict} active={active.name if active else 'none'}")
    print(f"runtime_check={ok} detail={reason}")
    if (strict or prod) and not ok:
        raise SystemExit(2)
    raise SystemExit(0)


if __name__ == "__main__":
    main()
