"""
Geração de mídia via Replicate (https://replicate.com) quando REPLICATE_API_TOKEN está definido.
Requer conta Replicate e créditos; modelos padrão são leves o suficiente para testes.
"""
from __future__ import annotations

import base64
import logging
import os
import threading
import uuid
from typing import Any, Dict, Optional

import requests

from vereda_backend.core.config import settings

logger = logging.getLogger(__name__)

_lock = threading.Lock()


def _replicate_run(model: str, input_data: dict[str, Any]) -> Any:
    token = (settings.replicate_api_token or "").strip()
    if not token:
        return None
    import replicate

    with _lock:
        old = os.environ.get("REPLICATE_API_TOKEN")
        os.environ["REPLICATE_API_TOKEN"] = token
        try:
            return replicate.run(model, input=input_data)
        finally:
            if old is None:
                os.environ.pop("REPLICATE_API_TOKEN", None)
            else:
                os.environ["REPLICATE_API_TOKEN"] = old


def _output_to_first_url(output: Any) -> Optional[str]:
    """Extrai a primeira URL http(s) devolvida pelo Replicate (flux, etc.)."""
    if output is None:
        return None
    if isinstance(output, str) and output.startswith("http"):
        return output
    if isinstance(output, (list, tuple)) and output:
        return _output_to_first_url(output[0])
    url_attr = getattr(output, "url", None)
    if isinstance(url_attr, str) and url_attr.startswith("http"):
        return url_attr
    return None


def _normalize_to_bytes_and_mime(output: Any) -> tuple[Optional[bytes], str]:
    if output is None:
        return None, "application/octet-stream"
    if isinstance(output, str):
        if output.startswith("http"):
            r = requests.get(output, timeout=300)
            r.raise_for_status()
            ct = (r.headers.get("content-type") or "application/octet-stream").split(";")[0].strip()
            return r.content, ct
        return None, "application/octet-stream"
    if isinstance(output, (list, tuple)) and output:
        return _normalize_to_bytes_and_mime(output[0])
    read_fn = getattr(output, "read", None)
    if callable(read_fn):
        data = read_fn()
        if isinstance(data, str):
            data = data.encode("utf-8")
        return data, "application/octet-stream"
    return None, "application/octet-stream"


def try_replicate_image(prompt: str) -> Optional[Dict[str, Any]]:
    model = (settings.replicate_image_model or "black-forest-labs/flux-schnell").strip()
    try:
        out = _replicate_run(model, {"prompt": (prompt or "").strip()})
        raw, mime = _normalize_to_bytes_and_mime(out)
        if not raw:
            return None
        b64 = base64.b64encode(raw).decode("ascii")
        if "png" in mime:
            out_mime = "image/png"
        elif "webp" in mime:
            out_mime = "image/webp"
        elif "jpeg" in mime or "jpg" in mime:
            out_mime = "image/jpeg"
        else:
            out_mime = "image/png"
        return {
            "ok": True,
            "id": f"img-repl-{uuid.uuid4()}",
            "provider": "replicate",
            "prompt": prompt,
            "image_base64": b64,
            "mime": out_mime,
        }
    except Exception as exc:
        logger.warning("Replicate imagem falhou: %s", exc)
        return None


def _try_pruna_p_video(prompt: str) -> Optional[Dict[str, Any]]:
    """
    prunaai/p-video exige uma imagem inicial + prompt (I2V).
    Gera um frame com o mesmo modelo de imagem configurado e encadeia.
    """
    p = (prompt or "").strip()
    seed = (settings.replicate_video_seed_image_url or "").strip()
    image_url = seed or None
    if not image_url:
        img_model = (settings.replicate_image_model or "black-forest-labs/flux-schnell").strip()
        img_out = _replicate_run(img_model, {"prompt": p})
        image_url = _output_to_first_url(img_out)
    if not image_url:
        logger.warning("prunaai/p-video: sem URL de imagem (flux não retornou URL).")
        return None

    duration = max(1, min(60, int(settings.replicate_pvideo_duration or 5)))
    resolution = (settings.replicate_pvideo_resolution or "720p").strip() or "720p"

    out = _replicate_run(
        "prunaai/p-video",
        {
            "fps": 24,
            "draft": False,
            "image": image_url,
            "no_op": False,
            "prompt": p,
            "duration": duration,
            "resolution": resolution,
            "save_audio": True,
            "aspect_ratio": "16:9",
            "prompt_upsampling": False,
            "disable_safety_filter": True,
        },
    )
    url = _output_to_first_url(out)
    if url and url.startswith("http"):
        return {
            "ok": True,
            "id": f"vid-repl-{uuid.uuid4()}",
            "provider": "replicate-pruna-p-video",
            "prompt": prompt,
            "url": url,
            "mime": "video/mp4",
            "seed_image_url": image_url,
        }
    raw, mime = _normalize_to_bytes_and_mime(out)
    if raw:
        b64 = base64.b64encode(raw).decode("ascii")
        m = mime if "video" in mime or "mp4" in mime else "video/mp4"
        return {
            "ok": True,
            "id": f"vid-repl-{uuid.uuid4()}",
            "provider": "replicate-pruna-p-video",
            "prompt": prompt,
            "url": f"data:{m};base64,{b64}",
            "mime": m,
            "seed_image_url": image_url,
        }
    return None


def try_replicate_video(prompt: str) -> Optional[Dict[str, Any]]:
    model = (settings.replicate_video_model or "prunaai/p-video").strip()
    try:
        if "prunaai/p-video" in model or model.endswith("p-video"):
            return _try_pruna_p_video(prompt)

        out = _replicate_run(model, {"prompt": (prompt or "").strip()})
        if isinstance(out, str) and out.startswith("http"):
            return {
                "ok": True,
                "id": f"vid-repl-{uuid.uuid4()}",
                "provider": "replicate",
                "prompt": prompt,
                "url": out,
                "mime": "video/mp4",
            }
        url = _output_to_first_url(out)
        if url:
            return {
                "ok": True,
                "id": f"vid-repl-{uuid.uuid4()}",
                "provider": "replicate",
                "prompt": prompt,
                "url": url,
                "mime": "video/mp4",
            }
        raw, mime = _normalize_to_bytes_and_mime(out)
        if raw:
            b64 = base64.b64encode(raw).decode("ascii")
            m = mime if "video" in mime or "mp4" in mime else "video/mp4"
            return {
                "ok": True,
                "id": f"vid-repl-{uuid.uuid4()}",
                "provider": "replicate",
                "prompt": prompt,
                "url": f"data:{m};base64,{b64}",
                "mime": m,
            }
    except Exception as exc:
        logger.warning("Replicate vídeo falhou: %s", exc)
    return None


def try_replicate_music(prompt: str) -> Optional[Dict[str, Any]]:
    model = (settings.replicate_music_model or "meta/musicgen-small").strip()
    try:
        p = (prompt or "").strip()
        try:
            out = _replicate_run(model, {"prompt": p, "duration": 8})
        except Exception:
            out = _replicate_run(model, {"prompt": p})
        if isinstance(out, str) and out.startswith("http"):
            return {
                "ok": True,
                "id": f"music-repl-{uuid.uuid4()}",
                "provider": "replicate",
                "prompt": prompt,
                "audio_url": out,
                "mime": "audio/wav",
            }
        raw, mime = _normalize_to_bytes_and_mime(out)
        if raw:
            b64 = base64.b64encode(raw).decode("ascii")
            m = mime if "audio" in mime else "audio/wav"
            return {
                "ok": True,
                "id": f"music-repl-{uuid.uuid4()}",
                "provider": "replicate",
                "prompt": prompt,
                "audio_url": f"data:{m};base64,{b64}",
                "mime": m,
            }
    except Exception as exc:
        logger.warning("Replicate música falhou: %s", exc)
    return None
