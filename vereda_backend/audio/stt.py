"""Speech-to-text: Azure Cognitive Services (prioritário) ou LOCAL_STT_ENDPOINT (Whisper HTTP)."""
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
    """Converte áudio arbitrário para WAV PCM 16 kHz mono (Azure / Whisper aceitam bem)."""
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
            out_bytes = _read_binary(dst_path)
            return out_bytes
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


def _azure_transcribe_wav(wav_bytes: bytes) -> str:
    key = (getattr(settings, "azure_speech_key", None) or "").strip()
    region = (getattr(settings, "azure_speech_region", None) or "").strip()
    if not key or not region:
        return ""
    try:
        import azure.cognitiveservices.speech as speechsdk  # type: ignore[import-untyped]

        speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
        speech_config.speech_recognition_language = "pt-BR"
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(wav_bytes)
            tmp.flush()
            path = tmp.name
        try:
            audio_config = speechsdk.audio.AudioConfig(filename=path)
            recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config, audio_config=audio_config
            )
            result = recognizer.recognize_once()
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return (result.text or "").strip()
            if result.reason == speechsdk.ResultReason.NoMatch:
                _log.info("Azure STT: sem correspondência de fala.")
            else:
                _log.warning("Azure STT: %s", result.reason)
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
    except ImportError:
        _log.warning("Pacote azure-cognitiveservices-speech não instalado.")
    except Exception as exc:
        _log.warning("Azure STT falhou: %s", exc)
    return ""


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
            return {"ok": bool(text), "text": text, "raw": body, "provider": "local_http"}
    except Exception as exc:
        _log.warning("STT local HTTP falhou: %s", exc)
    return {}


def transcribe_bytes(
    data: bytes,
    filename: str = "audio.bin",
    content_type: str = "application/octet-stream",
) -> Dict[str, Any]:
    if not data:
        return {"ok": False, "text": "", "detail": "Áudio vazio."}

    ct = (content_type or "").lower()
    fn = filename or "audio.bin"
    suffix = _suffix_from_name(fn)

    # 1) WAV já adequado → tentar Azure direto
    wav_bytes: bytes | None = None
    if "wav" in ct and suffix == ".wav":
        wav_bytes = data
    else:
        wav_bytes = _ffmpeg_to_wav_16k_mono(data, suffix)

    if wav_bytes:
        azure_text = _azure_transcribe_wav(wav_bytes)
        if azure_text:
            return {"ok": True, "text": azure_text, "provider": "azure_speech"}

    # 2) Endpoint local (Docker faster-whisper, etc.) — bytes originais
    local = _local_http_transcribe(data, fn, content_type or "application/octet-stream")
    if local.get("ok") and local.get("text"):
        return local

    # 3) Se havia WAV convertido mas Azure falhou, tentar local com WAV
    if wav_bytes and wav_bytes is not data:
        local2 = _local_http_transcribe(
            wav_bytes,
            "converted.wav",
            "audio/wav",
        )
        if local2.get("ok") and local2.get("text"):
            return local2

    detail = (
        "Transcrição indisponível: configure AZURE_SPEECH_KEY + AZURE_SPEECH_REGION "
        "e instale ffmpeg no servidor para WebM/Opus, ou defina LOCAL_STT_ENDPOINT."
    )
    return {"ok": False, "text": "", "detail": detail}
