"""
Cloudflare Turnstile — verificação de token no backend.
Graceful degradation: se TURNSTILE_SECRET_KEY não estiver configurada,
todos os tokens são aceitos (não bloqueia ambiente dev/test).
"""
from __future__ import annotations

import logging
import os
from typing import Optional

import httpx

from vereda_backend.core.config import settings

logger = logging.getLogger(__name__)

_TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def _get_secret() -> Optional[str]:
    return (getattr(settings, "turnstile_secret_key", None) or "").strip() or None


def verify_turnstile_token(token: str | None, remote_ip: str | None = None) -> bool:
    """
    Verifica um token Turnstile com a API da Cloudflare.
    Retorna True se válido ou se a verificação estiver desativada.
    Retorna False apenas se o token foi explicitamente rejeitado.
    """
    secret = _get_secret()
    if not secret:
        # Desativado em dev/test
        return True
    if not token:
        return False
    payload = {
        "secret": secret,
        "response": token,
    }
    if remote_ip:
        payload["remoteip"] = remote_ip
    try:
        with httpx.Client(timeout=httpx.Timeout(connect=5.0, read=10.0)) as client:
            resp = client.post(_TURNSTILE_VERIFY_URL, data=payload)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.warning("Turnstile verify request failed: %s", exc)
        # Em caso de falha de rede, não bloquear o usuário
        return True
    success = bool(data.get("success"))
    if not success:
        logger.info(
            "Turnstile rejeitado: error-codes=%s",
            data.get("error-codes"),
        )
    return success
