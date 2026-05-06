import base64
import io
import logging
from typing import Optional

import requests

from vereda_backend.core.config import settings

logger = logging.getLogger(__name__)


def _get_preferred_endpoint() -> Optional[str]:
    # Ordem de preferência: ollama, local_llm_endpoint, exllama, azure_tgi, remote
    for attr in (
        "ollama_endpoint",
        "local_llm_endpoint",
        "exllama_endpoint",
        "azure_tgi_endpoint",
        "remote_llm_endpoint",
    ):
        val = (getattr(settings, attr, None) or "").strip()
        if val:
            return val.rstrip("/")
    return None


def ping_llm() -> dict:
    dl = (getattr(settings, "default_llm", "") or "").strip().lower()
    if dl == "syntexa_native":
        return {
            "status": "up",
            "engine": "syntexa_native",
            "note": "motor proprietário (Fase 1); sem API de modelo de terceiros",
        }
    ep = _get_preferred_endpoint()
    if not ep:
        return {"status": "not_configured"}
    headers = {}
    if dl == "ollama":
        api_key = (getattr(settings, "ollama_api_key", None) or "").strip()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
    # Try common health paths
    candidates = ["/v1/models", "/api/tags", "/"]
    for p in candidates:
        try:
            url = ep + p
            resp = requests.get(url, headers=headers, timeout=2.5)
            code = getattr(resp, "status_code", 200) or 200
            if 200 <= int(code) < 300:
                out = {"status": "up", "checked": url}
                if dl:
                    out["provider"] = dl
                return out
            return {"status": "degraded", "http": int(code), "checked": url}
        except Exception as exc:
            logger.debug("ping %s failed: %s", ep + p, exc)
            continue
    return {"status": "down", "checked": ep, "provider": dl or "unknown"}


def describe_image(file_obj, prompt: str = "") -> str:
    """
    Descreve imagem via endpoint HTTP multimodal do servidor configurado.
    Expects `file_obj` to be a file-like object (seekable).
    """
    ep = _get_preferred_endpoint()
    if not ep:
        return ""
    try:
        file_obj.seek(0)
    except Exception:
        pass
    try:
        from PIL import Image

        img = Image.open(file_obj).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:
        try:
            file_obj.seek(0)
            bts = file_obj.read()
            b64 = base64.b64encode(bts).decode("ascii")
        except Exception:
            return ""

    vm = getattr(settings, "vision_llm_model", None) or "llava:7b"
    payload = {
        "model": vm,
        "prompt": prompt.strip() or "Descreva esta imagem em detalhes objetivos.",
        "images": [b64],
        "stream": False,
    }
    # Tenta /api/generate (vários gateways locais expõem esse caminho)
    try:
        resp = requests.post(f"{ep}/api/generate", json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return str(data.get("response") or "").strip()
    except Exception as exc:
        logger.debug("api/generate failed on %s: %s", ep, exc)

    # Try generic chat-style endpoint
    try:
        resp = requests.post(
            f"{ep}/v1/chat/completions",
            json={"model": vm, "messages": [{"role": "user", "content": payload["prompt"]}]},
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        choices = data.get("choices") or []
        if choices:
            msg = choices[0].get("message") or {}
            return str(msg.get("content") or "").strip()
    except Exception as exc:
        logger.debug("v1/chat/completions failed on %s: %s", ep, exc)

    return ""


def generate_text(messages: list[dict], model: Optional[str] = None, timeout: int = 30) -> str:
    ep = _get_preferred_endpoint()
    if not ep:
        raise RuntimeError("LLM endpoint não configurado")
    def _text_model() -> str:
        return (
            (model or "").strip()
            or (getattr(settings, "remote_llm_model", None) or "").strip()
            or (getattr(settings, "local_http_llm_model", None) or "").strip()
            or "local"
        )

    try:
        payload = {
            "model": _text_model(),
            "prompt": "\n".join([f"{(m.get('role') or 'USER').upper()}: {m.get('content','')}" for m in messages]) + "\nASSISTANT:",
            "stream": False,
        }
        resp = requests.post(f"{ep}/api/generate", json=payload, timeout=timeout)
        resp.raise_for_status()
        return str(resp.json().get("response") or "")
    except Exception:
        pass

    # Try HTTP OpenAI-style
    try:
        resp = requests.post(
            f"{ep}/v1/chat/completions",
            json={"model": _text_model(), "messages": messages},
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        choices = data.get("choices") or []
        if choices:
            return str(choices[0].get("message", {}).get("content") or "")
    except Exception:
        pass

    raise RuntimeError("Falha ao gerar texto no endpoint LLM configurado")
