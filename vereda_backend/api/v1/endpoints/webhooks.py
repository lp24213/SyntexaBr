"""
Webhooks externos — Resend (e-mail) e outros serviços.

Segurança:
  - Resend: valida assinatura HMAC-SHA256 via header `resend-signature` quando
    RESEND_WEBHOOK_SECRET está configurado. Se não configurado, apenas loga e aceita
    (modo permissivo para ambiente dev). Em produção configure RESEND_WEBHOOK_SECRET.
"""
import hashlib
import hmac
import logging
import os
from typing import Any, Dict

from fastapi import APIRouter, Header, HTTPException, Request, status


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks")

# Segredo do webhook Resend (opcional mas recomendado em produção)
_RESEND_WEBHOOK_SECRET = (os.getenv("RESEND_WEBHOOK_SECRET") or "").strip()


def _verify_resend_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """
    Valida a assinatura HMAC-SHA256 do webhook da Resend.
    Formato do header: 'v1=<hex_digest>'
    Retorna True se válido ou se o segredo não está configurado (modo dev).
    """
    if not _RESEND_WEBHOOK_SECRET:
        # Sem segredo configurado — aceita em dev, loga aviso
        logger.warning(
            "RESEND_WEBHOOK_SECRET não configurado — aceitando webhook sem validação. "
            "Configure em produção para segurança."
        )
        return True

    if not signature_header:
        return False

    # Extrai o digest do header 'v1=<hex>'
    try:
        parts = {k.strip(): v.strip() for k, v in (p.split("=", 1) for p in signature_header.split(",") if "=" in p)}
        expected_sig = parts.get("v1", "")
    except Exception:
        return False

    if not expected_sig:
        return False

    computed = hmac.new(
        _RESEND_WEBHOOK_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(computed, expected_sig)


@router.post("/resend")
async def resend_webhook_handler(
    request: Request,
    resend_signature: str | None = Header(default=None, alias="resend-signature"),
) -> Dict[str, Any]:
    """
    Recebe eventos de webhook da Resend (entrega, bounce, spam, etc.).
    Valida a assinatura HMAC-SHA256 quando RESEND_WEBHOOK_SECRET está configurado.
    """
    raw_body = await request.body()

    if not _verify_resend_signature(raw_body, resend_signature):
        logger.warning("Webhook Resend rejeitado: assinatura inválida ou ausente.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Assinatura de webhook inválida.",
        )

    try:
        import json
        payload: Dict[str, Any] = json.loads(raw_body)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payload inválido.")

    event_type = payload.get("type", "unknown")
    logger.info("Webhook Resend recebido: type=%s", event_type)

    return {"received": True, "type": event_type}
