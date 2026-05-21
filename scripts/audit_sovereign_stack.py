#!/usr/bin/env python3
"""
SYNTEXA SOVEREIGN STACK AUDITOR
================================
Script de auditoria da arquitetura soberana.
Verifica integridade completa da stack e reporta violações.

Uso:
    python scripts/audit_sovereign_stack.py
    python scripts/audit_sovereign_stack.py --full  # scan completo de todos os .py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Adiciona root
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Importa diretamente do arquivo para evitar cascade de imports pelo __init__.py
import importlib.util
_spec = importlib.util.spec_from_file_location(
    "sovereign_guard",
    str(_ROOT / "vereda_ai" / "syntexa_core" / "sovereign_guard.py")
)
_sovereign_guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sovereign_guard)
SovereignGuard = _sovereign_guard.SovereignGuard


def main() -> None:
    ap = argparse.ArgumentParser(description="Auditoria da Stack Soberana Syntexa")
    ap.add_argument("--full", action="store_true", help="Scan completo de todos os arquivos Python")
    args = ap.parse_args()

    print("=" * 70)
    print("  SYNTEXA SOVEREIGN STACK AUDITOR")
    print("  Arquitetura V41 | Governança Absoluta")
    print("=" * 70)

    guard = SovereignGuard(root_dir=str(_ROOT))
    ok, violations = guard.audit(scan_python_files=args.full)

    print()
    if ok:
        print("[PASS] Stack soberana INTACTA")
        print("  - Foundation Model: OK")
        print("  - Tokenizer Soberano: OK")
        print("  - Inference Engine: OK")
        print("  - Quantum Layer: OK")
        print("  - Multimodal: OK")
        print("  - Memory/RAG: OK")
        print("  - No external providers: OK")
        print("  - NeuralEngine discontinued: OK")
        print()
        print("=" * 70)
        sys.exit(0)
    else:
        print(f"[FAIL] {len(violations)} VIOLAÇÃO(ÕES) DETECTADA(S)")
        print()
        for i, v in enumerate(violations, 1):
            print(f"  {i}. {v}")
        print()
        print("=" * 70)
        print("AÇÃO: Corrija as violações antes de continuar.")
        print("A arquitetura soberana NÃO PODE ser comprometida.")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
