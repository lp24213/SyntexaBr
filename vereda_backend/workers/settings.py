"""Configuração do worker ARQ: `arq vereda_backend.workers.settings.WorkerSettings`"""
import os

from arq.connections import RedisSettings

from vereda_backend.workers.tasks import (
    arq_build_pdf,
    arq_build_xlsx,
    arq_generate_image,
    arq_generate_music,
    arq_generate_video,
    arq_long_chat,
    arq_gov_report,
)


def _require_redis_dsn() -> str:
    u = (os.getenv("REDIS_URL") or "").strip()
    if not u:
        raise RuntimeError(
            "REDIS_URL é obrigatória para o worker ARQ. Defina no servidor Hetzner (ex.: URL do Redis gerenciado ou Docker)."
        )
    return u


class WorkerSettings:
    functions = [
        arq_generate_image,
        arq_generate_video,
        arq_generate_music,
        arq_long_chat,
        arq_gov_report,
        arq_build_pdf,
        arq_build_xlsx,
    ]
    redis_settings = RedisSettings.from_dsn(_require_redis_dsn())
    job_timeout = 600
    max_tries = 2
    allow_abort_jobs = True
