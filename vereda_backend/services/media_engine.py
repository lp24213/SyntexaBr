import asyncio
import base64
import hashlib
import io
import logging
import math
import random
import urllib.parse
from urllib.parse import urlparse
import uuid
import wave
from typing import Any, Dict, Optional

import requests
from fastapi import UploadFile
from PIL import Image, ImageDraw

from vereda_backend.core.config import settings


logger = logging.getLogger(__name__)


def _allowed_image_fetch_host(hostname: str) -> bool:
    if not hostname:
        return False
    h = hostname.lower()
    if h in ("image.pollinations.ai", "pollinations.ai"):
        return True
    if h.endswith(".replicate.delivery") or h.endswith(".pbxt.replicate"):
        return True
    return False


def fetch_whitelisted_image_url_to_base64(url: str) -> Dict[str, Any]:
    """
    Baixa bytes de uma URL de imagem permitida e devolve base64 (para o chat não depender
    de carregar domínio externo no navegador — evita 502/proxy).
    """
    raw = (url or "").strip()
    if not raw:
        raise ValueError("URL vazia.")
    p = urlparse(raw)
    if p.scheme not in ("http", "https") or not _allowed_image_fetch_host(p.hostname or ""):
        raise ValueError("Host da URL não permitido para fetch.")
    resp = requests.get(
        raw,
        timeout=60,
        headers={"User-Agent": "SyntexaMedia/1.0"},
    )
    resp.raise_for_status()
    mime = (resp.headers.get("content-type") or "image/jpeg").split(";")[0].strip() or "image/jpeg"
    if not mime.startswith("image/"):
        mime = "image/jpeg"
    b64 = base64.b64encode(resp.content).decode("ascii")
    return {
        "ok": True,
        "image_base64": b64,
        "mime": mime,
        "source_url": raw,
    }


def _pollinations_download_b64(prompt: str) -> Optional[Dict[str, Any]]:
    """Tenta Pollinations com mais de uma URL; sempre retorna base64 se der certo."""
    encoded = urllib.parse.quote_plus((prompt or "").strip() or "futuristic illustration")
    variants = [
        f"https://image.pollinations.ai/prompt/{encoded}",
        f"https://image.pollinations.ai/prompt/{encoded}?width=768&height=768&nologo=true",
    ]
    last_exc: Optional[Exception] = None
    for url in variants:
        try:
            resp = requests.get(
                url,
                timeout=60,
                headers={"User-Agent": "SyntexaMedia/1.0"},
            )
            resp.raise_for_status()
            mime = (resp.headers.get("content-type") or "image/jpeg").split(";")[0].strip() or "image/jpeg"
            if not mime.startswith("image/"):
                mime = "image/jpeg"
            b64 = base64.b64encode(resp.content).decode("ascii")
            return {
                "ok": True,
                "id": f"img-pollinations-{uuid.uuid4()}",
                "provider": "pollinations",
                "prompt": prompt,
                "image_base64": b64,
                "mime": mime,
                "source_url": url,
            }
        except Exception as exc:
            last_exc = exc
            logger.warning("Pollinations falhou (%s): %s", url[:96], exc)
    if last_exc:
        logger.warning("Todas as tentativas Pollinations falharam.")
    return None


def _local_video_gif_data_uri(prompt: str) -> str:
    seed = int(hashlib.sha256((prompt or "").encode("utf-8")).hexdigest()[:8], 16)
    rnd = random.Random(seed)
    w, h = 480, 270
    frames = []
    base_color = (rnd.randint(20, 120), rnd.randint(20, 120), rnd.randint(20, 120))

    for i in range(18):
        img = Image.new("RGB", (w, h), base_color)
        draw = ImageDraw.Draw(img)
        for _ in range(24):
            x = rnd.randint(0, w - 1)
            y = rnd.randint(0, h - 1)
            r = rnd.randint(8, 40)
            c = (
                (base_color[0] + i * 8 + rnd.randint(0, 140)) % 255,
                (base_color[1] + i * 6 + rnd.randint(0, 140)) % 255,
                (base_color[2] + i * 4 + rnd.randint(0, 140)) % 255,
            )
            draw.ellipse((x, y, min(w - 1, x + r), min(h - 1, y + r)), outline=c, width=2)
        draw.text((16, 16), f"Syntexa Video | frame {i+1}", fill=(240, 240, 255))
        draw.text((16, 40), (prompt or "")[:90], fill=(245, 245, 245))
        frames.append(img)

    buf = io.BytesIO()
    frames[0].save(
        buf,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=90,
        loop=0,
    )
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/gif;base64,{b64}"


def _local_audio_data_uri(prompt: str, duration_s: float = 6.0, sample_rate: int = 22050) -> str:
    seed = int(hashlib.sha256((prompt or "").encode("utf-8")).hexdigest()[:8], 16)
    rnd = random.Random(seed)
    base = 180 + rnd.randint(0, 220)
    freqs = [base, base * 1.25, base * 1.5, base * 2.0]
    total = int(duration_s * sample_rate)
    amp = 14000

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        pcm = bytearray()
        for n in range(total):
            t = n / sample_rate
            env = 0.3 + 0.7 * min(1.0, t / 0.8) * min(1.0, (duration_s - t) / 0.8)
            val = 0.0
            for idx, f in enumerate(freqs):
                val += math.sin(2.0 * math.pi * f * t + idx * 0.45) * (0.42 / (idx + 1))
            sample = int(max(-1.0, min(1.0, val * env)) * amp)
            pcm += int(sample).to_bytes(2, byteorder="little", signed=True)
        wf.writeframes(pcm)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:audio/wav;base64,{b64}"


def generate_image_from_prompt(prompt: str) -> Dict[str, Any]:
    """
    Gera imagem a partir do prompt.

    Ordem de tentativa:
    1) Se LOCAL_IMAGE_GEN_ENDPOINT estiver configurado, delega para serviço open-source externo (ex.: Stable Diffusion API).
       Espera um POST em `${LOCAL_IMAGE_GEN_ENDPOINT.rstrip('/')}/generate` com JSON `{\"prompt\": prompt}` e
       resposta JSON contendo ao menos `image_base64` (PNG base64) ou `url` (link da imagem).
    2) Pollinations (várias URLs) — sempre tenta devolver image_base64 (não url crua pro browser).
    3) Se REPLICATE_API_TOKEN existir, tenta Replicate (também base64).
    Se nenhum provedor responder, levanta erro (sem imagem placeholder).
    """
    endpoint = (settings.local_image_gen_endpoint or "").rstrip("/")
    if endpoint:
        try:
            resp = requests.post(
                f"{endpoint}/generate",
                json={"prompt": prompt},
                timeout=180,
            )
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict) and (
                data.get("image_base64")
                or data.get("url")
                or data.get("image_url")
            ):
                data.setdefault("ok", True)
                data.setdefault("id", f"img-{uuid.uuid4()}")
                data.setdefault("provider", "local-image-gen")
                data.setdefault("prompt", prompt)
                return data
        except Exception as exc:
            logger.warning("Falha na geração de imagem via serviço externo: %s", exc)

    poll = _pollinations_download_b64(prompt)
    if poll:
        return poll

    if (settings.replicate_api_token or "").strip():
        from vereda_backend.services.replicate_media import try_replicate_image

        rr = try_replicate_image(prompt)
        if rr:
            return rr

    # Se chegou aqui, nenhum provedor real conseguiu gerar.
    raise RuntimeError("Falha ao gerar imagem em todos os provedores configurados.")


def analyze_video_basic(file: UploadFile) -> Dict[str, Any]:
    """
    Análise básica de vídeo por metadados de upload.
    Se LOCAL_VIDEO_GEN_ENDPOINT existir com rota /analyze, delega para serviço local.
    """
    endpoint = (settings.local_video_gen_endpoint or "").rstrip("/")
    if endpoint:
        try:
            file.file.seek(0)
            resp = requests.post(
                f"{endpoint}/analyze",
                files={
                    "file": (
                        file.filename or "video.bin",
                        file.file.read(),
                        file.content_type or "application/octet-stream",
                    )
                },
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict):
                data.setdefault("ok", True)
                return data
        except Exception as exc:
            logger.warning("Falha no analyze de video externo: %s", exc)
        finally:
            try:
                file.file.seek(0)
            except Exception:
                pass
    try:
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)
    except Exception:
        size = None
    return {
        "ok": True,
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": size,
        "description": "Análise básica local concluída (metadados).",
    }


def generate_video_from_prompt(prompt: str) -> Dict[str, Any]:
    """
    Gera vídeo a partir do prompt.

    Ordem de tentativa:
    1) Se LOCAL_VIDEO_GEN_ENDPOINT estiver configurado, delega para serviço open-source externo de vídeo
       (ex.: SVD, Open-Sora, etc) em `${LOCAL_VIDEO_GEN_ENDPOINT.rstrip('/')}/generate`,
       enviando JSON `{\"prompt\": prompt}` e esperando resposta com `url` ou `video_url`.
    2) Fallback: gera animação GIF determinística local (data URI) via motor interno.
    """
    endpoint = (settings.local_video_gen_endpoint or "").rstrip("/")
    if endpoint:
        try:
            resp = requests.post(
                f"{endpoint}/generate",
                json={"prompt": prompt},
                timeout=600,
            )
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict) and (
                data.get("url")
                or data.get("video_url")
            ):
                data.setdefault("ok", True)
                data.setdefault("id", f"vid-{uuid.uuid4()}")
                data.setdefault("provider", "local-video-gen")
                data.setdefault("prompt", prompt)
                return data
        except Exception as exc:
            logger.warning("Falha na geração de vídeo via serviço externo: %s", exc)

    if (settings.replicate_api_token or "").strip():
        from vereda_backend.services.replicate_media import try_replicate_video

        rr = try_replicate_video(prompt)
        if rr:
            return rr

    return {
        "ok": True,
        "id": f"vid-{uuid.uuid4()}",
        "provider": "syntexa-media-engine",
        "prompt": prompt,
        "url": _local_video_gif_data_uri(prompt),
        "mime": "image/gif",
    }


def generate_music_from_prompt(prompt: str) -> Dict[str, Any]:
    """
    Geração de áudio a partir do prompt.

    Ordem de tentativa:
    1) Se LOCAL_MUSIC_GEN_ENDPOINT estiver configurado, delega para serviço open-source externo de música
       em `${LOCAL_MUSIC_GEN_ENDPOINT.rstrip('/')}/generate`, com JSON `{\"prompt\": prompt}` e
       resposta contendo `audio_url` ou `url`.
    2) Fallback: gera WAV sintetizado localmente em data URI para nunca quebrar.
    """
    endpoint = (settings.local_music_gen_endpoint or "").rstrip("/")
    if endpoint:
        try:
            resp = requests.post(
                f"{endpoint}/generate",
                json={"prompt": prompt},
                timeout=600,
            )
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict) and (
                data.get("audio_url")
                or data.get("url")
            ):
                data.setdefault("ok", True)
                data.setdefault("id", f"music-{uuid.uuid4()}")
                data.setdefault("provider", "local-music-gen")
                data.setdefault("prompt", prompt)
                data.setdefault("mime", data.get("mime") or "audio/wav")
                return data
        except Exception as exc:
            logger.exception("Falha na geração de áudio via serviço externo: %s", exc)

    if (settings.replicate_api_token or "").strip():
        from vereda_backend.services.replicate_media import try_replicate_music

        rr = try_replicate_music(prompt)
        if rr:
            return rr

    return {
        "ok": True,
        "id": f"music-{uuid.uuid4()}",
        "provider": "syntexa-media-engine",
        "prompt": prompt,
        "audio_url": _local_audio_data_uri(prompt),
        "mime": "audio/wav",
    }


def _edge_tts_mp3_bytes(text: str, voice: str) -> bytes:
    import edge_tts

    async def _go() -> bytes:
        communicate = edge_tts.Communicate(text, voice)
        chunks: list[bytes] = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])
        return b"".join(chunks)

    return asyncio.run(_go())


def generate_tts_from_text(text: str, voice: str | None = None) -> Dict[str, Any]:
    """
    Voz (TTS) em português via Microsoft Edge TTS (sem API key).
    Opcional: LOCAL_TTS_ENDPOINT com POST /generate JSON {\"text\": \"...\", \"voice\": \"...\"}
    retornando {\"audio_url\": \"...\"} ou {\"url\": \"...\"}.
    """
    raw = (text or "").strip()
    if not raw:
        return {"ok": False, "detail": "Texto vazio."}

    endpoint = (settings.local_tts_endpoint or "").rstrip("/")
    if endpoint:
        try:
            resp = requests.post(
                f"{endpoint}/generate",
                json={"text": raw, "voice": voice or settings.edge_tts_voice},
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict) and (data.get("audio_url") or data.get("url")):
                u = data.get("audio_url") or data.get("url")
                data.setdefault("ok", True)
                data.setdefault("provider", "local-tts")
                data["audio_url"] = u
                data.setdefault("mime", data.get("mime") or "audio/mpeg")
                return data
        except Exception as exc:
            logger.warning("TTS via LOCAL_TTS_ENDPOINT falhou: %s", exc)

    v = (voice or settings.edge_tts_voice or "pt-BR-FranciscaNeural").strip()
    try:
        mp3 = _edge_tts_mp3_bytes(raw[:5000], v)
        b64 = base64.b64encode(mp3).decode("ascii")
        return {
            "ok": True,
            "provider": "edge-tts",
            "audio_url": f"data:audio/mpeg;base64,{b64}",
            "mime": "audio/mpeg",
            "voice": v,
        }
    except Exception as exc:
        logger.exception("edge-tts falhou: %s", exc)
        return {"ok": False, "detail": str(exc)}


def describe_image_with_ollama(file: UploadFile, prompt: str = "") -> str:
    """
    Reconhecimento de imagem via modelo multimodal local no Ollama.
    """
    endpoint = (settings.ollama_endpoint or "").rstrip("/")
    if not endpoint:
        return ""
    try:
        file.file.seek(0)
        img = Image.open(file.file).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        user_prompt = prompt.strip() or "Descreva esta imagem em detalhes objetivos."
        payload = {
            "model": settings.ollama_vision_model,
            "prompt": user_prompt,
            "images": [b64],
            "stream": False,
        }
        resp = requests.post(
            f"{endpoint}/api/generate",
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        return str(data.get("response") or "").strip()
    except Exception as exc:
        logger.warning("Falha na descrição de imagem via Ollama: %s", exc)
        return ""
    finally:
        try:
            file.file.seek(0)
        except Exception:
            pass


def transcribe_audio_local(file: UploadFile) -> str:
    """
    Transcrição via endpoint STT local open-source (ex.: whisper.cpp/faster-whisper service).
    Espera LOCAL_STT_ENDPOINT recebendo multipart "file" e retornando JSON com "text".
    """
    endpoint = (settings.local_stt_endpoint or "").rstrip("/")
    if not endpoint:
        return ""
    try:
        file.file.seek(0)
        resp = requests.post(
            endpoint,
            files={
                "file": (
                    file.filename or "audio.bin",
                    file.file.read(),
                    file.content_type or "application/octet-stream",
                )
            },
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict):
            return str(data.get("text") or data.get("transcript") or "").strip()
        return ""
    except Exception as exc:
        logger.warning("Falha na transcrição local de áudio: %s", exc)
        return ""
    finally:
        try:
            file.file.seek(0)
        except Exception:
            pass

