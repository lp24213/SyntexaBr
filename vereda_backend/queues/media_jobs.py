"""Enfileiramento de exportações e análises pesadas (ARQ + Redis)."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from vereda_backend.core.config import settings

logger = logging.getLogger(__name__)


async def _pool():
    from arq import create_pool
    from arq.connections import RedisSettings

    url = (getattr(settings, "redis_url", None) or "").strip()
    if not url:
        raise RuntimeError("REDIS_URL não configurada")
    return await create_pool(RedisSettings.from_dsn(url))


def queue_enabled() -> bool:
    return bool((getattr(settings, "redis_url", None) or "").strip())


async def enqueue_pdf_export(
    title: str, sections: List[Dict[str, Any]], subtitle: Optional[str],
    *, styled: bool = True, include_footer: bool = False,
) -> bytes:
    pool = await _pool()
    job = await pool.enqueue_job(
        "arq_build_pdf", title, sections, subtitle,
        styled=styled, include_footer=include_footer,
    )
    return await job.result(timeout=120)


def run_pdf_export_sync(
    title: str, sections: List[Dict[str, Any]], subtitle: Optional[str],
    *, styled: bool = True, include_footer: bool = False,
) -> bytes:
    from vereda_backend.docs.pdf_builder import build_pdf_bytes

    if not queue_enabled():
        return build_pdf_bytes(title, sections, subtitle, styled=styled, include_footer=include_footer)
    return asyncio.run(enqueue_pdf_export(title, sections, subtitle, styled=styled, include_footer=include_footer))


async def enqueue_xlsx_export(
    sheet_title: str,
    rows: List[List[Any]],
    header: bool,
    document_title: Optional[str] = None,
) -> bytes:
    pool = await _pool()
    job = await pool.enqueue_job(
        "arq_build_xlsx", sheet_title, rows, header, document_title
    )
    return await job.result(timeout=120)


def run_xlsx_export_sync(
    sheet_title: str,
    rows: List[List[Any]],
    header: bool,
    *,
    document_title: Optional[str] = None,
) -> bytes:
    from vereda_backend.docs.xlsx_builder import build_xlsx_bytes

    if not queue_enabled():
        return build_xlsx_bytes(sheet_title, rows, header, document_title=document_title)
    return asyncio.run(
        enqueue_xlsx_export(sheet_title, rows, header, document_title)
    )
