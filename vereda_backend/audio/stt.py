"""Speech-to-text: Whisper HTTP local (LOCAL_STT_ENDPOINT). Chat web usa Xenova no navegador."""
from __future__ import annotations

import io
import logging
import os
import subprocess
import tempfile
from typing import Any, Dict

import requests

from vereda_backend.core.config import settings

_log = logging.getLogger(__name__)


def _read_binary(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def _ffmpeg_to_wav_16k_mono(data: bytes, suffix: str) -> bytes | None:
    """Converte áudio arbitrário para WAV PCM 16 kHz mono (Whisper HTTP)."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as src:
            src.write(data)
            src.flush()
            src_path = src.name
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as out:
            dst_path = out.name
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    src_path,
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    "-f",
                    "wav",
                    dst_path,
                ],
                check=True,
                capture_output=True,
                timeout=120,
            )
            return _read_binary(dst_path)
        finally:
            try:
                os.unlink(src_path)
            except OSError:
                pass
            try:
                os.unlink(dst_path)
            except OSError:
                pass
    except FileNotFoundError:
        _log.warning("ffmpeg não encontrado no PATH — instale ffmpeg para WebM/Opus → WAV.")
    except subprocess.CalledProcessError as exc:
        _log.warning("ffmpeg falhou: %s", exc.stderr[:500] if exc.stderr else exc)
    except Exception as exc:
        _log.warning("conversão de áudio falhou: %s", exc)
    return None


def _suffix_from_name(filename: str) -> str:
    fn = (filename or "").lower()
    if fn.endswith(".webm"):
        return ".webm"
    if fn.endswith(".wav"):
        return ".wav"
    if fn.endswith(".mp3"):
        return ".mp3"
    if fn.endswith(".ogg"):
        return ".ogg"
    if fn.endswith(".m4a"):
        return ".m4a"
    return ".bin"


def _local_http_transcribe(data: bytes, filename: str, content_type: str) -> Dict[str, Any]:
    endpoint = (settings.local_stt_endpoint or "").rstrip("/")
    if not endpoint:
        return {}
    try:
        resp = requests.post(
            endpoint,
            files={"file": (filename, io.BytesIO(data), content_type)},
            timeout=180,
        )
        resp.raise_for_status()
        body = resp.json()
        if isinstance(body, dict):
            text = str(body.get("text") or body.get("transcript") or "").strip()
            return {"ok": bool(text), "text": text, "raw": body, "provider": "local_whisper_http"}
    except Exception as exc:
        _log.warning("STT local HTTP falhou: %s", exc)
    return {}


def transcribe_bytes(
    data: bytes,
    filename: str = "audio.bin",
    content_type: str = "application/octet-stream",
) -> Dict[str, Any]:
    """
    STT no servidor — só Whisper HTTP (LOCAL_STT_ENDPOINT).
    O microfone do chat em produção usa Xenova/Whisper no browser (frontend/lib/xenova-stt.js).
    """
    if not data:
        return {"ok": False, "text": "", "detail": "Áudio vazio."}

    ct = (content_type or "").lower()
    fn = filename or "audio.bin"
    suffix = _suffix_from_name(fn)

    local = _local_http_transcribe(data, fn, content_type or "application/octet-stream")
    if local.get("ok") and local.get("text"):
        return local

    wav_bytes: bytes | None = None
    if "wav" in ct and suffix == ".wav":
        wav_bytes = data
    else:
        wav_bytes = _ffmpeg_to_wav_16k_mono(data, suffix)

    if wav_bytes and wav_bytes is not data:
        local2 = _local_http_transcribe(wav_bytes, "converted.wav", "audio/wav")
        if local2.get("ok") and local2.get("text"):
            return local2

    detail = (
        "Transcrição no servidor indisponível: defina LOCAL_STT_ENDPOINT (Whisper HTTP, ex. production-node/stt-service) "
        "e ffmpeg no PATH. No chat web, use o microfone — STT local Xenova no navegador."
    )
    return {"ok": False, "text": "", "detail": detail}
