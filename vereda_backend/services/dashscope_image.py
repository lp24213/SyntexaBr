# -*- coding: utf-8 -*-
"""
Text-to-image via Alibaba DashScope (Wanx), na mesma conta/chave que o LLM na GPU.
HTTP async task + poll (sem SDK dashscope obrigatorio).
"""
from __future__ import annotations

import base64
import logging
import time
from typing import Any, Dict, Optional

import requests

from urllib.parse import urlparse

from vereda_backend.core.config import settings

logger = logging.getLogger(__name__)


def _effective_dashscope_api_v1_base() -> str:
    """
    Base HTTP para Wanx (…/api/v1). Prioridade: DASHSCOPE_API_BASE no .env;
    senao deriva de ALIBABA_COMPAT_BASE_URL (mesmo host que o chat usa).
    """
    explicit = (getattr(settings, "dashscope_api_base", None) or "").strip().rstrip("/")
    if explicit:
        return explicit
    compat = (getattr(settings, "alibaba_compat_base_url", None) or "").strip().rstrip("/")
    if compat and "dashscope" in compat.lower():
        root = compat.split("/compatible-mode")[0].strip().rstrip("/")
        if not root:
            root = compat
        parsed = urlparse(root if "://" in root else "https://" + root)
        if parsed.netloc:
            scheme = (parsed.scheme or "https").lower()
            return f"{scheme}://{parsed.netloc}".rstrip("/") + "/api/v1"
    return "https://dashscope-intl.aliyuncs.com/api/v1"


def _sniff_image_mime(data: bytes) -> Optional[str]:
    if not data or len(data) < 12:
        return None
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


_CREATE_PATH = "/services/aigc/text2image/image-synthesis"
_POLL_SLEEP_SEC = 2.0
_POLL_MAX_SEC = 120.0


def _task_id_from_body(data: dict[str, Any]) -> str:
    out = data.get("output") or {}
    tid = (out.get("task_id") or data.get("task_id") or "").strip()
    return tid


def _image_url_from_task_body(data: dict[str, Any]) -> str:
    out = data.get("output") or {}
    results = out.get("results")
    if isinstance(results, list) and results:
        first = results[0]
        if isinstance(first, dict):
            u = (first.get("url") or first.get("image_url") or "").strip()
            if u:
                return u
    # algumas respostas aninham em result / output
    for key in ("url", "image_url"):
        v = out.get(key)
        if isinstance(v, str) and v.startswith("http"):
            return v.strip()
    return ""


def try_dashscope_text2image(prompt: str) -> Optional[Dict[str, Any]]:
    """
    Cria tarefa Wanx (async) e faz poll ate SUCCEEDED; devolve dict compativel com media_engine
    (ok, image_base64, mime, provider) ou None se indisponivel/erro.
    """
    key = (getattr(settings, "alibaba_dashscope_api_key", None) or "").strip()
    if not key:
        return None

    base = _effective_dashscope_api_v1_base()

    model = (getattr(settings, "dashscope_image_model", None) or "wanx-v1").strip() or "wanx-v1"
    p = (prompt or "").strip()
    if not p:
        return None
    if len(p) > 1800:
        p = p[:1800] + "…"

    url_create = f"{base}{_CREATE_PATH}"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
    }
    body = {
        "model": model,
        "input": {"prompt": p},
        "parameters": {
            "style": "<auto>",
            "size": "1024*1024",
            "n": 1,
        },
    }

    try:
        r = requests.post(url_create, json=body, headers=headers, timeout=60)
        r.raise_for_status()
        jd = r.json() if r.content else {}
    except Exception as exc:
        logger.warning("DashScope image-synthesis create falhou: %s", exc)
        return None

    if isinstance(jd, dict) and jd.get("code"):
        logger.warning("DashScope create erro API: %s %s", jd.get("code"), jd.get("message"))
        return None

    task_id = _task_id_from_body(jd if isinstance(jd, dict) else {})
    if not task_id:
        logger.warning("DashScope create sem task_id: %s", jd)
        return None

    url_poll = f"{base}/tasks/{task_id}"
    poll_headers = {"Authorization": f"Bearer {key}"}
    deadline = time.monotonic() + _POLL_MAX_SEC
    last_status = ""

    while time.monotonic() < deadline:
        try:
            pr = requests.get(url_poll, headers=poll_headers, timeout=45)
            pr.raise_for_status()
            pd = pr.json() if pr.content else {}
        except Exception as exc:
            logger.warning("DashScope task poll falhou: %s", exc)
            time.sleep(_POLL_SLEEP_SEC)
            continue

        out = pd.get("output") if isinstance(pd, dict) else {}
        if not isinstance(out, dict):
            out = {}
        last_status = (out.get("task_status") or out.get("status") or "").upper()

        if last_status in ("FAILED", "UNKNOWN"):
            logger.warning("DashScope imagem falhou: status=%s body=%s", last_status, pd)
            return None

        if last_status == "SUCCEEDED":
            img_url = _image_url_from_task_body(pd if isinstance(pd, dict) else {})
            if not img_url:
                logger.warning("DashScope SUCCEEDED sem URL: %s", pd)
                return None
            try:
                ir = requests.get(img_url, timeout=90, headers={"User-Agent": "SyntexaMedia/1.0"})
                ir.raise_for_status()
                raw = ir.content
            except Exception as exc:
                logger.warning("DashScope download imagem falhou: %s", exc)
                return None

            mime = _sniff_image_mime(raw) or "image/png"
            b64 = base64.b64encode(raw).decode("ascii")
            return {
                "ok": True,
                "id": f"img-dashscope-{task_id[:24]}",
                "provider": "dashscope-wanx",
                "prompt": p,
                "image_base64": b64,
                "mime": mime,
                "source_url": img_url,
            }

        time.sleep(_POLL_SLEEP_SEC)

    logger.warning("DashScope imagem timeout (status ultimo=%s)", last_status)
    return None
