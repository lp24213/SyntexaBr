#!/usr/bin/env python3
"""
Lista o que falta no ambiente para Azure STT / filas / Redis (sem imprimir segredos).
Executar na VM: cd /opt/syntexa && source .venv/bin/activate && python scripts/check_backend_env.py

Requer PYTHONPATH ou cwd com pacote vereda_backend.
"""
from __future__ import annotations

import shutil
import sys


def main() -> int:
    try:
        from vereda_backend.core.config import settings
    except Exception as e:
        print("ERRO: não foi possível importar vereda_backend.core.config:", e)
        return 2

    checks = []

    def need(label: str, cond: bool, hint: str) -> None:
        checks.append((label, cond, hint))

    need(
        "AZURE_SPEECH_KEY + AZURE_SPEECH_REGION (STT)",
        bool((getattr(settings, "azure_speech_key", None) or "").strip())
        and bool((getattr(settings, "azure_speech_region", None) or "").strip()),
        "Portal Azure → recurso Speech → chave + região (ex. brazilsouth). pip install azure-cognitiveservices-speech",
    )
    need(
        "LOCAL_STT_ENDPOINT (fallback Whisper HTTP)",
        bool((getattr(settings, "local_stt_endpoint", None) or "").strip()),
        "Opcional se já tiver serviço Whisper na VM",
    )
    need("ffmpeg no PATH (WebM→WAV)", bool(shutil.which("ffmpeg")), "sudo apt install -y ffmpeg")
    need(
        "REDIS_URL",
        bool((getattr(settings, "redis_url", None) or "").strip()),
        "Opcional — cache/filas",
    )
    need(
        "AZURE_STORAGE_CONNECTION_STRING",
        bool((getattr(settings, "azure_storage_connection_string", None) or "").strip()),
        "Opcional — fila de imagens",
    )

    ok = 0
    for label, cond, hint in checks:
        st = "OK " if cond else "NO "
        print(f"{st}{label}")
        if not cond:
            print(f"     → {hint}")
        else:
            ok += 1

    print(f"\nResumo: {ok}/{len(checks)} itens satisfeitos (alguns são opcionais).")
    print("STT em produção exige: Azure Speech OU LOCAL_STT_ENDPOINT + ffmpeg para gravações do browser.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
