"""
Webhooks de Billing - Todos os gateways
==========================================

Recebe webhooks de:
- Stripe
- Pagar.me
- PagBank
- Coinbase Commerce

Ativa subscriptions automaticamente.
"""

import hashlib
import hmac
import os
import json
from typing import Any, Dict
from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException, Request, status, Depends
from sqlalchemy.orm import Session

from vereda_backend.db.session import get_db
from vereda_backend.db import models
from vereda_backend.core.subscription import (
    activate_subscription,
    handle_payment_failure,
    SubscriptionStatus,
    PaymentStatus,
    Plan,
    TRIAL_DAYS,
)
from vereda_ai.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/webhooks")


# =============================================================================
# STRIPE WEBHOOKS (complementar aos existentes em payments.py)
# =============================================================================

@router.post("/stripe")
async def stripe_webhook_billing(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
    db: Session = Depends(get_db),
):
    """
    Webhook unificado do Stripe para billing.
    
    Eventos suportados:
    - checkout.session.completed
    - invoice.paid
    - invoice.payment_failed
    - customer.subscription.created
    - customer.subscription.updated
    - customer.subscription.deleted
    - payment_intent.succeeded
    - payment_intent.payment_failed
    """
    import stripe
    
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
    if not webhook_secret:
        raise HTTPException(status_code=503, detail="Webhook secret não configurado")
    
    payload = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature or "",
            secret=webhook_secret,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Payload inválido")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Assinatura inválida")
    
    event_type = event.get("type")
    data = event.get("data", {}).get("object", {})
    
    logger.info(f"Stripe webhook: {event_type}")
    
    # checkout.session.completed - Pagamento inicial
    if event_type == "checkout.session.completed":
        await _handle_stripe_checkout_completed(data, db)
    
    # invoice.paid - Renovação paga
    elif event_type == "invoice.paid":
        await _handle_stripe_invoice_paid(data, db)
    
    # invoice.payment_failed - Falha na renovação
    elif event_type == "invoice.payment_failed":
        await _handle_stripe_invoice_failed(data, db)
    
    # customer.subscription.deleted - Cancelamento
    elif event_type == "customer.subscription.deleted":
        await _handle_stripe_subscription_deleted(data, db)
    
    return {"received": True, "type": event_type}


async def _handle_stripe_checkout_completed(data: Dict, db: Session):
    """Processa checkout completo - ativa subscription."""
    user_id_raw = data.get("client_reference_id")
    metadata = data.get("metadata", {})
    plan = metadata.get("plan", "").lower()
    customer_id = data.get("customer")
    subscription_id = data.get("subscription")
    
    if not user_id_raw:
        logger.warning("Stripe checkout sem client_reference_id")
        return
    
    try:
        user_id = int(user_id_raw)
    except ValueError:
        logger.error(f"User ID inválido: {user_id_raw}")
        return
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        logger.error(f"Usuário não encontrado: {user_id}")
        return
    
    # Mapeia plano
    if plan not in ["basic", "medium", "master"]:
        # Tenta inferir pelo produto
        items = data.get("line_items", {}).get("data", [])
        if items:
            name = items[0].get("description", "").lower()
            if "basic" in name:
                plan = "basic"
            elif "medium" in name:
                plan = "medium"
            elif "master" in name:
                plan = "master"
    
    if plan not in ["basic", "medium", "master"]:
        logger.error(f"Plano inválido: {plan}")
        return
    
    # Ativa subscription
    activate_subscription(
        db=db,
        user=user,
        plan=plan,
        payment_gateway="stripe",
        gateway_customer_id=customer_id,
        gateway_subscription_id=subscription_id,
        payment_amount=data.get("amount_total", 0) / 100,  # centavos -> reais
        period_days=30,
    )
    
    logger.info(f"Subscription ativada via Stripe: user_id={user_id}, plan={plan}")


async def _handle_stripe_invoice_paid(data: Dict, db: Session):
    """Processa pagamento de invoice - renovação."""
    subscription_id = data.get("subscription")
    customer_id = data.get("customer")
    
    if not subscription_id:
        return
    
    # Busca usuário pelo subscription_id
    user = db.query(models.User).filter(
        models.User.payment_gateway_subscription_id == subscription_id
    ).first()
    
    if not user:
        logger.warning(f"Usuário não encontrado para subscription: {subscription_id}")
        return
    
    # Renova subscription
    activate_subscription(
        db=db,
        user=user,
        plan=user.subscription_plan,
        payment_gateway="stripe",
        gateway_customer_id=customer_id,
        gateway_subscription_id=subscription_id,
        payment_amount=data.get("amount_paid", 0) / 100,
        period_days=30,
    )
    
    logger.info(f"Subscription renovada via Stripe: user_id={user.id}")


async def _handle_stripe_invoice_failed(data: Dict, db: Session):
    """Processa falha de pagamento de invoice."""
    subscription_id = data.get("subscription")
    
    if not subscription_id:
        return
    
    user = db.query(models.User).filter(
        models.User.payment_gateway_subscription_id == subscription_id
    ).first()
    
    if not user:
        return
    
    handle_payment_failure(db, user)
    logger.warning(f"Falha de pagamento Stripe: user_id={user.id}")


async def _handle_stripe_subscription_deleted(data: Dict, db: Session):
    """Processa cancelamento de subscription."""
    subscription_id = data.get("id")
    
    if not subscription_id:
        return
    
    user = db.query(models.User).filter(
        models.User.payment_gateway_subscription_id == subscription_id
    ).first()
    
    if not user:
        return
    
    user.subscription_status = SubscriptionStatus.CANCELLED.value
    user.subscription_end = datetime.now(timezone.utc)
    db.commit()
    
    logger.info(f"Subscription cancelada via Stripe: user_id={user.id}")


# =============================================================================
# PAGAR.ME WEBHOOKS
# =============================================================================

@router.post("/pagarme")
async def pagarme_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Webhook do Pagar.me
    
    Documentação: https://docs.pagar.me/docs/webhooks
    """
    body = await request.body()
    payload = json.loads(body)
    
    event = payload.get("event", payload.get("type", ""))
    data = payload.get("data", {})
    
    logger.info(f"Pagar.me webhook: {event}")
    
    if event in ["transaction.paid", "order.paid"]:
        await _handle_pagarme_payment_paid(data, db)
    elif event in ["transaction.refused", "transaction.refunded", "order.payment_failed"]:
        await _handle_pagarme_payment_failed(data, db)
    
    return {"received": True}


async def _handle_pagarme_payment_paid(data: Dict, db: Session):
    """Processa pagamento aprovado do Pagar.me."""
    # Extrai metadados
    order = data.get("order", data)
    metadata = order.get("metadata", {})
    user_id = metadata.get("user_id")
    plan = metadata.get("plan", "basic")
    
    if not user_id:
        # Tenta extrair do customer
        customer = order.get("customer", {})
        customer_id = customer.get("id")
        # Busca usuário pelo customer_id
        user = db.query(models.User).filter(
            models.User.payment_gateway_customer_id == str(customer_id),
            models.User.payment_gateway == "pagarme"
        ).first()
    else:
        user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    
    if not user:
        logger.warning(f"Usuário não encontrado para pagamento Pagar.me")
        return
    
    amount = order.get("amount", 0) / 100  # centavos
    
    activate_subscription(
        db=db,
        user=user,
        plan=plan,
        payment_gateway="pagarme",
        payment_amount=amount,
        period_days=30,
    )
    
    logger.info(f"Subscription ativada via Pagar.me: user_id={user.id}")


async def _handle_pagarme_payment_failed(data: Dict, db: Session):
    """Processa pagamento recusado do Pagar.me."""
    order = data.get("order", data)
    metadata = order.get("metadata", {})
    user_id = metadata.get("user_id")
    
    if user_id:
        user = db.query(models.User).filter(models.User.id == int(user_id)).first()
        if user:
            handle_payment_failure(db, user)


# =============================================================================
# PAGBANK WEBHOOKS
# =============================================================================

@router.post("/pagbank")
async def pagbank_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Webhook do PagBank
    
    Documentação: https://dev.pagbank.uol.com.br/reference/webhooks
    """
    body = await request.body()
    payload = json.loads(body)
    
    event = payload.get("event", "")
    data = payload.get("data", {})
    
    logger.info(f"PagBank webhook: {event}")
    
    if event == "PAYMENT_CONFIRMED":
        await _handle_pagbank_payment_confirmed(data, db)
    elif event in ["PAYMENT_DECLINED", "PAYMENT_CANCELED"]:
        await _handle_pagbank_payment_failed(data, db)
    
    return {"received": True}


async def _handle_pagbank_payment_confirmed(data: Dict, db: Session):
    """Processa pagamento confirmado do PagBank."""
    reference_id = data.get("reference_id", "")
    # reference_id deve conter user_id e plan
    # formato: syntexa_{user_id}_{plan}
    
    if reference_id.startswith("syntexa_"):
        parts = reference_id.split("_")
        if len(parts) >= 3:
            try:
                user_id = int(parts[1])
                plan = parts[2]
            except ValueError:
                logger.error(f"Reference ID inválido: {reference_id}")
                return
        else:
            return
    else:
        return
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return
    
    amount = data.get("amount", {}).get("value", 0) / 100
    
    activate_subscription(
        db=db,
        user=user,
        plan=plan,
        payment_gateway="pagbank",
        payment_amount=amount,
        period_days=30,
    )
    
    logger.info(f"Subscription ativada via PagBank: user_id={user.id}")


async def _handle_pagbank_payment_failed(data: Dict, db: Session):
    """Processa pagamento recusado do PagBank."""
    reference_id = data.get("reference_id", "")
    
    if reference_id.startswith("syntexa_"):
        parts = reference_id.split("_")
        if len(parts) >= 2:
            try:
                user_id = int(parts[1])
                user = db.query(models.User).filter(models.User.id == user_id).first()
                if user:
                    handle_payment_failure(db, user)
            except ValueError:
                pass


# =============================================================================
# COINBASE COMMERCE WEBHOOKS
# =============================================================================

@router.post("/coinbase")
async def coinbase_webhook(
    request: Request,
    x_cc_webhook_signature: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """
    Webhook do Coinbase Commerce
    
    Documentação: https://docs.cloud.coinbase.com/commerce/docs/webhooks
    """
    webhook_secret = os.getenv("COINBASE_WEBHOOK_SECRET", "").strip()
    
    body = await request.body()
    
    # Valida assinatura
    if webhook_secret and x_cc_webhook_signature:
        expected = hmac.new(
            webhook_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        
        if not hmac.compare_digest(expected, x_cc_webhook_signature):
            raise HTTPException(status_code=401, detail="Assinatura inválida")
    
    payload = json.loads(body)
    
    event = payload.get("event", {})
    event_type = event.get("type", "")
    data = event.get("data", {})
    
    logger.info(f"Coinbase webhook: {event_type}")
    
    if event_type == "charge:confirmed":
        await _handle_coinbase_charge_confirmed(data, db)
    elif event_type in ["charge:failed", "charge:delayed"]:
        await _handle_coinbase_charge_failed(data, db)
    
    return {"received": True}


async def _handle_coinbase_charge_confirmed(data: Dict, db: Session):
    """Processa pagamento confirmado do Coinbase."""
    metadata = data.get("metadata", {})
    user_id = metadata.get("user_id")
    plan = metadata.get("plan", "basic")
    
    if not user_id:
        logger.warning("Coinbase charge sem user_id nos metadados")
        return
    
    try:
        user_id = int(user_id)
    except ValueError:
        return
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return
    
    # Coinbase retorna valores em crypto, converte aproximadamente
    # ou usa os metadados
    amount = data.get("pricing", {}).get("local", {}).get("amount", 0)
    
    activate_subscription(
        db=db,
        user=user,
        plan=plan,
        payment_gateway="coinbase",
        payment_amount=float(amount) if amount else None,
        period_days=30,
    )
    
    logger.info(f"Subscription ativada via Coinbase: user_id={user.id}")


async def _handle_coinbase_charge_failed(data: Dict, db: Session):
    """Processa pagamento falho do Coinbase."""
    metadata = data.get("metadata", {})
    user_id = metadata.get("user_id")
    
    if user_id:
        try:
            user = db.query(models.User).filter(models.User.id == int(user_id)).first()
            if user:
                handle_payment_failure(db, user)
        except ValueError:
            pass
