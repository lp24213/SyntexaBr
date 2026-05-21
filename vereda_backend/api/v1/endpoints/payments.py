from typing import Optional

import os

import stripe
from fastapi import APIRouter, HTTPException, Request, status
from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from vereda_backend.core.config import settings
from vereda_backend.core.security import get_current_user_optional
from vereda_backend.db import models
from vereda_backend.db.session import get_db
from vereda_ai.core.logging import get_logger


logger = get_logger(__name__)


router = APIRouter(prefix="/payments/stripe")


# Lê chaves EXCLUSIVAMENTE do ambiente — nenhum fallback hardcoded.
# Em produção, definir STRIPE_SECRET_KEY e STRIPE_WEBHOOK_SECRET no .env ou variáveis de sistema.
STRIPE_SECRET_KEY = (os.getenv("STRIPE_SECRET_KEY") or "").strip()
STRIPE_WEBHOOK_SECRET = (os.getenv("STRIPE_WEBHOOK_SECRET") or "").strip()

if not STRIPE_SECRET_KEY:
    import logging as _logging
    _logging.getLogger(__name__).warning(
        "STRIPE_SECRET_KEY não configurada — endpoints de pagamento retornarão 503."
    )

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


def _stripe_api_key() -> str:
    if not STRIPE_SECRET_KEY:
        from fastapi import HTTPException as _HTTPException
        raise _HTTPException(
            status_code=503,
            detail="Pagamentos temporariamente indisponíveis. Configure STRIPE_SECRET_KEY.",
        )
    return STRIPE_SECRET_KEY


class CheckoutRequest(BaseModel):
    plan: str  # "basic" | "medium" | "master"


class CheckoutResponse(BaseModel):
    url: str


def _get_plan_amount(plan: str) -> tuple[int, str]:
    """
    Retorna (valor_em_centavos, nome_plano) para o plano informado.
    Não depende de STRIPE_PRICE_*; usa amount direto no Checkout.
    """
    plan_key = (plan or "").lower().strip()
    # Valores em centavos (BRL). Ajuste conforme seus planos reais.
    mapping: dict[str, tuple[int, str]] = {
        "basic": (3900, "Syntexa Basic"),
        "medium": (9900, "Syntexa Medium"),
        "master": (19900, "Syntexa Master"),
    }
    if plan_key not in mapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plano inválido: '{plan}'. Use basic, medium ou master.",
        )
    return mapping[plan_key]


def _frontend_base_url() -> str:
    return getattr(settings, "frontend_base_url", None) or "https://syntexabr.com.br"


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    body: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional),
) -> CheckoutResponse:
    """
    Cria uma sessão de checkout do Stripe para um plano (basic/medium/master).
    Se o usuário estiver logado (Bearer), associa o pagamento a ele via client_reference_id.
    """
    key = _stripe_api_key()
    if not key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe SECRET_KEY não configurado.",
        )
    stripe.api_key = key

    amount_cents, plan_name = _get_plan_amount(body.plan)
    plan_key = (body.plan or "").lower().strip()

    # V46 — URLs limpas (encryptedPath foi desabilitado no frontend; /s/cGxhbnM
    # virava 404 e impedia o retorno após o pagamento).
    success_url = f"{_frontend_base_url()}/plans?success=1"
    cancel_url = f"{_frontend_base_url()}/plans?canceled=1"

    create_params = {
        "mode": "payment",
        "payment_method_types": ["card"],
        "line_items": [
            {
                "price_data": {
                    "currency": "brl",
                    "product_data": {"name": plan_name},
                    "unit_amount": amount_cents,
                },
                "quantity": 1,
            }
        ],
        "success_url": success_url + "&session_id={CHECKOUT_SESSION_ID}",
        "cancel_url": cancel_url,
        "metadata": {"plan": plan_key},
    }
    if current_user:
        create_params["client_reference_id"] = str(current_user.id)

    try:
        session = stripe.checkout.Session.create(**create_params)
    except Exception as e:
        logger.exception("Erro ao criar checkout session do Stripe: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Não foi possível iniciar o pagamento. Tente novamente mais tarde.",
        ) from e

    return CheckoutResponse(url=session.url)


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook do Stripe.

    URL configurada na Stripe:
    https://api.syntexabr.com.br/v1/payments/stripe/webhook
    """
    webhook_secret = STRIPE_WEBHOOK_SECRET
    if not webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe WEBHOOK_SECRET não configurado.",
        )

    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=webhook_secret,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload inválido.",
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assinatura inválida.",
        )

    event_type = event.get("type")
    logger.info("Stripe webhook recebido: %s", event_type)

    if event_type == "checkout.session.completed":
        session_data = event.get("data", {}).get("object", {})
        session_id = session_data.get("id")
        if session_id:
            try:
                session = stripe.checkout.Session.retrieve(
                    session_id,
                    expand=["line_items"],
                )
            except Exception as e:
                logger.exception("Erro ao recuperar sessão Stripe %s: %s", session_id, e)
            else:
                user_id_raw = session.get("client_reference_id")
                plan = (session.metadata or {}).get("plan") or ""
                plan = (plan or "").lower().strip()
                if plan not in ("basic", "medium", "master"):
                    # Fallback: inferir pelo nome do produto no line_item
                    items = (session.get("line_items") or {}).get("data") or []
                    if items:
                        name = (items[0].get("description") or items[0].get("price", {}).get("product") or "").lower()
                        if "basic" in name:
                            plan = "basic"
                        elif "medium" in name:
                            plan = "medium"
                        elif "master" in name:
                            plan = "master"
                if plan in ("basic", "medium", "master") and user_id_raw:
                    try:
                        user_id = int(user_id_raw)
                    except (TypeError, ValueError):
                        user_id = None
                    if user_id:
                        user = db.query(models.User).filter(models.User.id == user_id).first()
                        if user:
                            user.subscription_plan = plan
                            db.commit()
                            logger.info("Plano ativado: user_id=%s plan=%s", user_id, plan)

    return {"received": True}

