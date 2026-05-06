#!/usr/bin/env python3
"""Exporta estado LLM local (registry + readiness + política) em JSON — útil sem token admin."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from vereda_ai.syntexa_core.promotion_attestation import (  # noqa: E402
    bundle_fingerprint_for_model,
    registry_fingerprint,
)
from vereda_ai.syntexa_core.runtime_model import runtime_readiness_report  # noqa: E402
from vereda_backend.core.chat_policy import get_policy_snapshot  # noqa: E402


def main() -> None:
    reg = registry_fingerprint()
    active = reg.get("active")
    out: dict = {
        "registry": reg,
        "runtime": runtime_readiness_report(),
        "chat_policy": get_policy_snapshot(),
    }
    if active:
        out["bundle_active"] = bundle_fingerprint_for_model(str(active))
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
