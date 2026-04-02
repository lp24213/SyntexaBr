from __future__ import annotations

import logging
from typing import Any

import requests

from vereda_backend.core.config import settings
from vereda_backend.db import models


logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def _get_resend_api_key() -> str | None:
  return getattr(settings, "resend_api_key", None)  # type: ignore[attr-defined]


def _get_brevo_api_key() -> str | None:
  return getattr(settings, "brevo_api_key", None)  # type: ignore[attr-defined]


def _get_from_email() -> str:
  from_email = getattr(settings, "resend_from_email", None)
  if from_email:
    return from_email
  return "onboarding@resend.dev"


def _get_default_to_email() -> str:
  resend_to = getattr(settings, "resend_to_email", None)
  if resend_to:
    return str(resend_to)
  return settings.admin_email


def _send_resend_email(subject: str, html: str, to: str | None = None) -> None:
  api_key = _get_resend_api_key()
  if not api_key:
    msg = "[Resend] RESEND_API_KEY não configurada — e-mail não enviado: %s" % subject
    logger.error(msg)
    raise RuntimeError(msg)

  to_email = to or _get_default_to_email()
  payload: dict[str, Any] = {
    "from": _get_from_email(),
    "to": [to_email],
    "subject": subject,
    "html": html,
  }

  try:
    resp = requests.post(
      RESEND_API_URL,
      json=payload,
      headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
      },
      timeout=10,
    )
    resp.raise_for_status()
    logger.info("[Resend] E-mail enviado com sucesso para %s | assunto: %s", to_email, subject)
  except requests.HTTPError as exc:
    msg = (
      "[Resend] Erro HTTP ao enviar e-mail para %s | status: %s | resposta: %s"
      % (
        to_email,
        exc.response.status_code if exc.response is not None else "?",
        exc.response.text if exc.response is not None else str(exc),
      )
    )
    logger.error(msg)
    raise RuntimeError(msg) from exc
  except Exception as exc:
    msg = "[Resend] Falha ao enviar e-mail para %s: %s" % (to_email, exc)
    logger.error(msg)
    raise RuntimeError(msg) from exc


def _send_brevo_email(subject: str, html: str, to: str | None = None) -> None:
  api_key = _get_brevo_api_key()
  if not api_key:
    msg = "[Brevo] BREVO_API_KEY não configurada — e-mail não enviado: %s" % subject
    logger.error(msg)
    raise RuntimeError(msg)

  to_email = to or _get_default_to_email()
  from_email = _get_from_email()
  sender_name = "Syntexa"
  payload: dict[str, Any] = {
    "sender": {"name": sender_name, "email": from_email},
    "to": [{"email": to_email}],
    "subject": subject,
    "htmlContent": html,
  }

  try:
    resp = requests.post(
      BREVO_API_URL,
      json=payload,
      headers={
        "api-key": api_key,
        "accept": "application/json",
        "content-type": "application/json",
      },
      timeout=10,
    )
    resp.raise_for_status()
    logger.info("[Brevo] E-mail enviado com sucesso para %s | assunto: %s", to_email, subject)
  except requests.HTTPError as exc:
    msg = (
      "[Brevo] Erro HTTP ao enviar e-mail para %s | status: %s | resposta: %s"
      % (
        to_email,
        exc.response.status_code if exc.response is not None else "?",
        exc.response.text if exc.response is not None else str(exc),
      )
    )
    logger.error(msg)
    raise RuntimeError(msg) from exc
  except Exception as exc:
    msg = "[Brevo] Falha ao enviar e-mail para %s: %s" % (to_email, exc)
    logger.error(msg)
    raise RuntimeError(msg) from exc


def _send_email(subject: str, html: str, to: str | None = None) -> None:
  # Prefer Brevo if configured; fallback to Resend.
  if _get_brevo_api_key():
    _send_brevo_email(subject, html, to=to)
    return
  _send_resend_email(subject, html, to=to)


def notify_user_registered(user: models.User) -> None:
  subject = "Novo usuário registrado na Syntexa"
  html = f"""
  <h1>Novo usuário criado</h1>
  <p><strong>Email:</strong> {user.email}</p>
  <p><strong>Nome:</strong> {user.full_name or "-"} </p>
  <p><strong>Admin:</strong> {"sim" if user.is_admin else "não"}</p>
  """
  _send_email(subject, html)


def notify_login_success(user: models.User) -> None:
  subject = "Login efetuado na Syntexa"
  html = f"""
  <h1>Login bem-sucedido</h1>
  <p><strong>Email:</strong> {user.email}</p>
  <p>Um usuário acabou de entrar na plataforma de IA Syntexa.</p>
  """
  try:
    _send_email(subject, html)
  except Exception as exc:
    logger.warning("Falha ao notificar login bem-sucedido: %s", exc)


def notify_login_failed(email: str) -> None:
  subject = "Tentativa de login com falha na Syntexa"
  html = f"""
  <h1>Login com falha</h1>
  <p><strong>Email informado:</strong> {email}</p>
  <p>Uma tentativa de login não autorizada foi detectada.</p>
  """
  try:
    _send_email(subject, html)
  except Exception as exc:
    logger.warning("Falha ao notificar login com falha: %s", exc)


def notify_chat_completion(
  user: models.User | None, prompt_preview: str, reply_preview: str
) -> None:
  subject = "Novo chat processado pela Syntexa"
  html = f"""
  <h1>Novo chat</h1>
  <p><strong>Usuário:</strong> {user.email if user else "anônimo"}</p>
  <p><strong>Entrada (tamanho):</strong> {len(prompt_preview or "")} caracteres</p>
  <p><strong>Resposta (tamanho):</strong> {len(reply_preview or "")} caracteres</p>
  <p>Prévia de conteúdo desativada por segurança.</p>
  """
  try:
    _send_email(subject, html)
  except Exception as exc:
    # Nunca quebrar fluxo do chat por falha de notificação.
    logger.warning("Falha ao notificar chat completion: %s", exc)


def notify_feedback_created(
  feedback: models.Feedback, log_row: models.ConversationLog, user: models.User
) -> None:
  subject = "Novo feedback de conversa na Syntexa"
  html = f"""
  <h1>Feedback recebido</h1>
  <p><strong>Usuário:</strong> {user.email}</p>
  <p><strong>Rating:</strong> {feedback.rating}</p>
  <p><strong>Comentário:</strong> {feedback.comment or "-"} </p>
  <p><strong>Trecho da conversa:</strong></p>
  <pre>{(log_row.content or "")[:400]}</pre>
  """
  _send_email(subject, html)


def send_verification_code_email(email: str, code: str, purpose: str) -> None:
  subject = "Código de verificação Syntexa"
  if purpose == "signup":
    title = "Confirmação de cadastro"
    intro = "Use o código abaixo para confirmar seu cadastro na plataforma Syntexa."
  else:
    title = "Recuperação de senha"
    intro = "Use o código abaixo para redefinir sua senha na plataforma Syntexa."

  html = f"""
  <h1>{title}</h1>
  <p>{intro}</p>
  <p><strong>Código:</strong> {code}</p>
  <p>Ele expira em 30 minutos.</p>
  """
  _send_email(subject, html, to=email)

