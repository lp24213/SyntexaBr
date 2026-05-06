import asyncio
import base64
import logging
import urllib.parse
from urllib.parse import urlparse
import uuid
from typing import Any, Dict, Optional

import requests
from fastapi import UploadFile

from vereda_backend.core.config import settings
from vereda_backend.core.media_orchestrator import plan_image_request, plan_video_request


logger = logging.getLogger(__name__)


def _sniff_image_mime(data: bytes) -> Optional[str]:
    """Detecta PNG/JPEG/GIF/WebP pelos magic bytes (evita HTML/JSON da API como 'imagem')."""
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
    raw_bytes = resp.content
    mime = _sniff_image_mime(raw_bytes)
    if not mime:
        raise ValueError("A URL não retornou uma imagem válida (PNG/JPEG/GIF/WebP).")
    b64 = base64.b64encode(raw_bytes).decode("ascii")
    return {
        "ok": True,
        "image_base64": b64,
        "mime": mime,
        "source_url": raw,
    }


def _pollinations_download_b64(prompt: str) -> Optional[Dict[str, Any]]:
    """Tenta Pollinations com mais de uma URL; sempre retorna base64 se der certo."""
    encoded = urllib.parse.quote_plus((prompt or "").strip() or "futuristic illustration")
    raw_res = str(getattr(settings, "media_image_target_resolution", "1024x1024") or "1024x1024")
    try:
        w, h = [int(x) for x in raw_res.lower().replace(" ", "").replace("*", "x").split("x", 1)]
    except Exception:
        w, h = 1024, 1024
    w = max(512, min(2048, w))
    h = max(512, min(2048, h))
    variants = [
        f"https://image.pollinations.ai/prompt/{encoded}",
        f"https://image.pollinations.ai/prompt/{encoded}?width={w}&height={h}&nologo=true",
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
            raw_bytes = resp.content
            mime = _sniff_image_mime(raw_bytes)
            if not mime:
                logger.warning(
                    "Pollinations retornou payload não-imagem (%s bytes), tentando próxima URL.",
                    len(raw_bytes or b""),
                )
                continue
            b64 = base64.b64encode(raw_bytes).decode("ascii")
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


def _extract_image_base64_and_mime(data: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    def _clean_base64(value: Any) -> Optional[str]:
        if not isinstance(value, str):
            return None
        raw = value.strip()
        if not raw:
            return None
        if raw.startswith("data:") and ";base64," in raw:
            raw = raw.split(";base64,", 1)[1]
        return raw or None

    direct_keys = ("image_base64", "b64_json", "b64", "base64")
    for key in direct_keys:
        got = _clean_base64(data.get(key))
        if got:
            return got, data.get("mime") or "image/png"

    for list_key in ("data", "images", "output", "results"):
        arr = data.get(list_key)
        if isinstance(arr, list) and arr:
            first = arr[0]
            if isinstance(first, dict):
                for key in direct_keys:
                    got = _clean_base64(first.get(key))
                    if got:
                        return got, first.get("mime") or data.get("mime") or "image/png"
    return None, None


def _extract_image_url(data: Dict[str, Any]) -> Optional[str]:
    direct_keys = ("url", "image_url", "output_url")
    for key in direct_keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip().startswith(("http://", "https://")):
            return value.strip()
    for list_key in ("data", "images", "output", "results"):
        arr = data.get(list_key)
        if isinstance(arr, list) and arr:
            first = arr[0]
            if isinstance(first, dict):
                for key in direct_keys:
                    value = first.get(key)
                    if isinstance(value, str) and value.strip().startswith(("http://", "https://")):
                        return value.strip()
    return None


def _bfl_generate_b64(prompt: str) -> Optional[Dict[str, Any]]:
    api_key = (getattr(settings, "bfl_api_key", None) or "").strip()
    if not api_key:
        return None

    endpoint_tpl = (getattr(settings, "bfl_api_url", None) or "").strip() or "https://api.us1.bfl.ai/v1/{model}"
    model = (getattr(settings, "bfl_model", None) or "").strip() or "flux-pro-1.1"
    timeout_sec = int(getattr(settings, "bfl_timeout_sec", 90) or 90)
    endpoint = endpoint_tpl.replace("{model}", model)

    payload: Dict[str, Any] = {"prompt": prompt}
    if "{model}" not in endpoint_tpl:
        payload["model"] = model

    try:
        resp = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "SyntexaMedia/1.0",
            },
            json=payload,
            timeout=max(20, timeout_sec),
        )
        resp.raise_for_status()
        data = resp.json() if "application/json" in (resp.headers.get("content-type", "")) else {}
        if not isinstance(data, dict):
            data = {}

        b64, mime = _extract_image_base64_and_mime(data)
        if b64:
            return {
                "ok": True,
                "id": f"img-bfl-{uuid.uuid4()}",
                "provider": "black-forest-labs",
                "prompt": prompt,
                "image_base64": b64,
                "mime": mime or "image/png",
                "source_url": endpoint,
            }

        image_url = _extract_image_url(data)
        if image_url:
            img_resp = requests.get(
                image_url,
                timeout=60,
                headers={"User-Agent": "SyntexaMedia/1.0"},
            )
            img_resp.raise_for_status()
            raw_bytes = img_resp.content
            mime2 = _sniff_image_mime(raw_bytes)
            if mime2:
                return {
                    "ok": True,
                    "id": f"img-bfl-{uuid.uuid4()}",
                    "provider": "black-forest-labs",
                    "prompt": prompt,
                    "image_base64": base64.b64encode(raw_bytes).decode("ascii"),
                    "mime": mime2,
                    "source_url": image_url,
                }
    except Exception as exc:
        logger.warning("Black Forest Labs falhou, aplicando fallback: %s", exc)
    return None


def generate_image_from_prompt(prompt: str) -> Dict[str, Any]:
    """
    Gera imagem a partir do prompt (provedores reais apenas).

    Ordem: Black Forest Labs (BFL_API_KEY) → LOCAL_IMAGE_GEN_ENDPOINT (serviço GPU no VPS) → Pollinations
    se MEDIA_USE_POLLINATIONS=true. Imagem no browser: use Puter.js no frontend (sem este endpoint).
    """
    image_plan = plan_image_request(prompt)
    effective_prompt = image_plan.prompt
    bfl = _bfl_generate_b64(effective_prompt)
    if bfl:
        logger.info("Imagem via Black Forest Labs.")
        return bfl

    endpoint = (settings.local_image_gen_endpoint or "").rstrip("/")
    if endpoint:
        try:
            resp = requests.post(
                f"{endpoint}/generate",
                json={
                    "prompt": effective_prompt,
                    "width": image_plan.width,
                    "height": image_plan.height,
                    "quality": image_plan.quality,
                    "negative_prompt": image_plan.negative_prompt,
                    "style": "photorealistic",
                },
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
                data.setdefault("prompt", effective_prompt)
                return data
        except Exception as exc:
            logger.warning("Falha na geração de imagem via serviço externo: %s", exc)

    if bool(getattr(settings, "media_use_pollinations", False)):
        poll = _pollinations_download_b64(effective_prompt)
        if poll:
            poll.setdefault("provider", "pollinations")
            logger.info("Imagem via Pollinations (fallback quando LOCAL_IMAGE_GEN_ENDPOINT indisponível).")
            return poll

    raise RuntimeError(
        "Imagem indisponível: configure LOCAL_IMAGE_GEN_ENDPOINT (GPU/serviço local) ou "
        "MEDIA_USE_POLLINATIONS=true. No site, a geração principal usa Puter.js no navegador."
    )


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

    Requer LOCAL_VIDEO_GEN_ENDPOINT (serviço no VPS/GPU).
    """
    video_plan = plan_video_request(prompt)
    effective_prompt = video_plan.prompt
    endpoint = (settings.local_video_gen_endpoint or "").rstrip("/")
    if endpoint:
        try:
            resp = requests.post(
                f"{endpoint}/generate",
                json={
                    "prompt": effective_prompt,
                    "resolution": video_plan.resolution,
                    "fps": video_plan.fps,
                    "duration_sec": video_plan.duration_sec,
                    "quality": video_plan.quality,
                    "negative_prompt": video_plan.negative_prompt,
                    "camera_motion": "stable-cinematic",
                },
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
                data.setdefault("prompt", effective_prompt)
                return data
        except Exception as exc:
            logger.warning("Falha na geração de vídeo via serviço externo: %s", exc)

    raise RuntimeError(
        "Vídeo indisponível: configure LOCAL_VIDEO_GEN_ENDPOINT (serviço de vídeo no servidor)."
    )


def generate_music_from_prompt(prompt: str) -> Dict[str, Any]:
    """
    Geração de áudio a partir do prompt.

    Requer LOCAL_MUSIC_GEN_ENDPOINT (serviço no VPS).
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

    raise RuntimeError(
        "Áudio indisponível: configure LOCAL_MUSIC_GEN_ENDPOINT (serviço de música no servidor)."
    )


def _azure_tts_mp3_bytes(text: str, voice: str) -> bytes | None:
    """TTS via Azure AI Speech (mesma chave/região do STT). Devolve MP3 ou None."""
    key = (getattr(settings, "azure_speech_key", None) or "").strip()
    region = (getattr(settings, "azure_speech_region", None) or "").strip()
    if not key or not region or not (text or "").strip():
        return None
    try:
        import azure.cognitiveservices.speech as speechsdk  # type: ignore[import-untyped]

        speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
        speech_config.speech_synthesis_voice_name = (voice or "").strip() or getattr(
            settings, "azure_tts_voice", "pt-BR-FranciscaNeural"
        )
        try:
            speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Audio16Khz128KBitRateMonoMp3
            )
        except Exception:
            pass
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, audio_config=None
        )
        result = synthesizer.speak_text_async((text or "")[:5000]).get()
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            audio = result.audio_data
            if audio and len(audio) > 0:
                return bytes(audio)
        if result.reason == speechsdk.ResultReason.Canceled:
            cr = result.cancellation_details
            logger.warning(
                "Azure TTS cancelado: %s %s",
                cr.reason if cr else "?",
                cr.error_details if cr else "",
            )
    except ImportError:
        logger.warning("Pacote azure-cognitiveservices-speech não instalado (TTS Azure).")
    except Exception as exc:
        logger.warning("Azure TTS falhou: %s", exc)
    return None


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

    v_azure = (voice or settings.azure_tts_voice or settings.edge_tts_voice or "pt-BR-FranciscaNeural").strip()
    mp3_az = _azure_tts_mp3_bytes(raw[:5000], v_azure)
    if mp3_az:
        b64a = base64.b64encode(mp3_az).decode("ascii")
        return {
            "ok": True,
            "provider": "azure-speech-tts",
            "audio_url": f"data:audio/mpeg;base64,{b64a}",
            "mime": "audio/mpeg",
            "voice": v_azure,
        }

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


def describe_image_with_vision_llm(file: UploadFile, prompt: str = "") -> str:
    """Visão via endpoint HTTP próprio (delega para `llm_client.describe_image`)."""
    try:
        from vereda_backend.services.llm_client import describe_image

        return describe_image(file.file, prompt)
    except Exception as exc:
        logger.warning("describe_image gerou erro: %s", exc)
        try:
            file.file.seek(0)
        except Exception:
            pass
        return ""


def transcribe_audio_local(file: UploadFile) -> str:
    """
    STT: Azure Speech (AZURE_SPEECH_*) e/ou LOCAL_STT_ENDPOINT — ver `vereda_backend.audio.stt`.
    """
    from vereda_backend.audio.stt import transcribe_bytes

    try:
        file.file.seek(0)
        data = file.file.read()
        out = transcribe_bytes(
            data,
            filename=file.filename or "audio.bin",
            content_type=file.content_type or "application/octet-stream",
        )
        return str(out.get("text") or "").strip()
    except Exception as exc:
        logger.warning("Falha na transcrição de áudio: %s", exc)
        return ""
    finally:
        try:
            file.file.seek(0)
        except Exception:
            pass

