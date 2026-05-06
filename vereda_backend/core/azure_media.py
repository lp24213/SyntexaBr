"""
Publica metadados de geração de imagem na fila Azure Storage e, se configurado,
faz upload do binário para um container Blob (URL com SAS ou caminho para workers).
"""
from __future__ import annotations

import base64
import json
import logging
import uuid
from typing import Any, Dict

from vereda_backend.core.config import settings

logger = logging.getLogger(__name__)


def _mime_to_ext(mime: str) -> str:
    m = (mime or "").lower().split(";")[0].strip()
    if m == "image/png":
        return "png"
    if m in ("image/jpeg", "image/jpg"):
        return "jpg"
    if m == "image/webp":
        return "webp"
    if m == "image/gif":
        return "gif"
    return "bin"


def publish_image_job_result(result: Dict[str, Any], prompt: str) -> None:
    """
    Enfileira mensagem JSON (<=64KB). Opcionalmente grava image_base64 no Blob
    quando AZURE_STORAGE_IMAGE_CONTAINER estiver definido.
    """
    conn = (getattr(settings, "azure_storage_connection_string", None) or "").strip()
    if not conn:
        return
    queue_name = (getattr(settings, "azure_storage_image_queue", None) or "image-jobs").strip()
    container = (getattr(settings, "azure_storage_image_container", None) or "").strip()

    blob_name: str | None = None
    blob_url: str | None = None

    if container and result.get("image_base64"):
        try:
            raw = base64.b64decode(result["image_base64"])
            mime = str(result.get("mime") or "image/png")
            ext = _mime_to_ext(mime)
            blob_name = f"generated/{uuid.uuid4().hex}.{ext}"
            from azure.storage.blob import BlobServiceClient, ContentSettings

            bsc = BlobServiceClient.from_connection_string(conn)
            blob = bsc.get_blob_client(container=container, blob=blob_name)
            blob.upload_blob(
                raw,
                overwrite=True,
                content_settings=ContentSettings(content_type=mime),
            )
            blob_url = blob.url
        except Exception as exc:
            logger.warning("Azure Blob upload falhou (fila ainda será tentada): %s", exc)

    payload = {
        "event": "image_generated",
        "prompt_preview": (prompt or "")[:4000],
        "provider": result.get("provider"),
        "image_id": result.get("id"),
        "mime": result.get("mime"),
        "blob_name": blob_name,
        "blob_url": blob_url,
        "has_inline_base64": bool(result.get("image_base64")),
    }
    try:
        from azure.storage.queue import QueueClient

        text_body = json.dumps(payload, ensure_ascii=False)
        if len(text_body.encode("utf-8")) > 63000:
            payload.pop("prompt_preview", None)
            text_body = json.dumps(payload, ensure_ascii=False)
        qc = QueueClient.from_connection_string(conn, queue_name)
        qc.send_message(text_body)
    except Exception as exc:
        logger.warning("Azure Queue send falhou: %s", exc)
