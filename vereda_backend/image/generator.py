"""Geração de imagem no backend — delega ao mesmo pipeline que /v1/media (GPU local / fila / política de provedor)."""
from __future__ import annotations

from typing import Any, Dict

from vereda_backend.core.job_queue import run_image_job_sync


def generate_image_backend(prompt: str) -> Dict[str, Any]:
    return run_image_job_sync((prompt or "").strip())
