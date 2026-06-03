"""
Subscription API
================

Endpoints para:
- Verificar status da subscription
- Gerenciar plano
- Ver uso atual
- Cancelar/reativar
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from vereda_backend.db.session import get_db
from vereda_backend.db import models
from vereda_backend.core.security import get_current_user
from vereda_backend.core.subscription import (
    check_subscription_status,
    get_usage_stats,
    get_plan_features,
    Plan,
    PLAN_PRICES,
    require_subscription,
    cancel_subscription,
    activate_subscription,
)
from vereda_ai.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/subscription")


class SubscriptionInfoResponse(BaseModel):
    plan: str
    status: str
    payment_status: str
    is_active: bool
    is_trial: bool
    is_expired: bool
    trial_days_left: int
    expires_in_days: Optional[int]
    renewal_date: Optional[str]
    features: dict
    usage: dict
    paywall_url: str


class PlanInfo(BaseModel):
    id: str
    name: str
    price_cents: int
    price_display: str
    features: dict


class PlansResponse(BaseModel):
    plans: list[PlanInfo]
    current_plan: str


class UsageResponse(BaseModel):
    messages_used: int
    messages_limit: Optional[int]
    messages_remaining: Optional[int]
    whatsapp_connections_used: int
    whatsapp_connections_limit: Optional[int]
    agents_used: int
    agents_limit: Optional[int]
    automations_used: int
    automations_limit: Optional[int]


class CancelRequest(BaseModel):
    immediate: bool = False


@router.get("/status", response_model=SubscriptionInfoResponse)
async def get_subscription_status(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Retorna o status completo da subscription do usuário.
    """
    status_info = check_subscription_status(current_user)
    usage = get_usage_stats(db, current_user)
    
    return SubscriptionInfoResponse(
        plan=current_user.subscription_plan,
        status=status_info["status"],
        payment_status=current_user.payment_status,
        is_active=status_info["is_active"],
        is_trial=status_info["is_trial"],
        is_expired=status_info["is_expired"],
        trial_days_left=status_info["trial_days_left"],
        expires_in_days=status_info["expires_in_days"],
        renewal_date=current_user.renewal_date.isoformat() if current_user.renewal_date else None,
        features=status_info["features"],
        usage=usage,
        paywall_url=f"/i18n/{current_user.id}/plans?blocked=1",
    )


@router.get("/plans", response_model=PlansResponse)
async def get_available_plans(
    current_user: models.User = Depends(get_current_user),
):
    """
    Retorna os planos disponíveis e seus preços.
    """
    plans = [
        PlanInfo(
            id=Plan.FREE.value,
            name="Gratuito",
            price_cents=0,
            price_display="R$ 0,00",
            features=get_plan_features(Plan.FREE.value),
        ),
        PlanInfo(
            id=Plan.BASIC.value,
            name="Basic",
            price_cents=PLAN_PRICES[Plan.BASIC.value],
            price_display="R$ 39,00/mês",
            features=get_plan_features(Plan.BASIC.value),
        ),
        PlanInfo(
            id=Plan.MEDIUM.value,
            name="Medium",
            price_cents=PLAN_PRICES[Plan.MEDIUM.value],
            price_display="R$ 99,00/mês",
            features=get_plan_features(Plan.MEDIUM.value),
        ),
        PlanInfo(
            id=Plan.MASTER.value,
            name="Master",
            price_cents=PLAN_PRICES[Plan.MASTER.value],
            price_display="R$ 199,00/mês",
            features=get_plan_features(Plan.MASTER.value),
        ),
    ]
    
    return PlansResponse(
        plans=plans,
        current_plan=current_user.subscription_plan,
    )


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Retorna o uso atual do usuário.
    """
    usage = get_usage_stats(db, current_user)
    
    return UsageResponse(
        messages_used=usage["messages"]["used"],
        messages_limit=usage["messages"]["limit"],
        messages_remaining=usage["messages"]["remaining"],
        whatsapp_connections_used=usage["whatsapp_connections"]["used"],
        whatsapp_connections_limit=usage["whatsapp_connections"]["limit"],
        agents_used=usage["agents"]["used"],
        agents_limit=usage["agents"]["limit"],
        automations_used=usage["automations"]["used"],
        automations_limit=usage["automations"]["limit"],
    )


@router.post("/cancel")
async def cancel(
    body: CancelRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Cancela a subscription do usuário.
    
    - immediate=True: Cancela imediatamente
    - immediate=False: Cancela ao final do período pago
    """
    if current_user.subscription_status not in ["active", "trial"]:
        raise HTTPException(
            status_code=400,
            detail="Não há subscription ativa para cancelar"
        )
    
    cancel_subscription(db, current_user, immediate=body.immediate)
    
    return {
        "message": "Subscription cancelada",
        "immediate": body.immediate,
        "status": current_user.subscription_status,
    }


@router.post("/reactivate")
async def reactivate(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Reativa uma subscription cancelada/expirada (requer novo pagamento).
    """
    # Apenas marca como pendente de reativação
    # O usuário precisa fazer novo pagamento via /payments/stripe/checkout
    
    if current_user.subscription_status not in ["cancelled", "expired", "suspended"]:
        raise HTTPException(
            status_code=400,
            detail="Subscription não pode ser reativada neste estado"
        )
    
    # Reseta para trial se expirou há muito tempo
    # ou mantém o plano anterior
    return {
        "message": "Para reativar, faça um novo pagamento",
        "redirect_to": "/payments/stripe/checkout",
        "plan": current_user.subscription_plan,
    }


@router.post("/upgrade")
async def upgrade_plan(
    new_plan: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Inicia upgrade para um plano superior.
    Retorna URL para checkout.
    """
    valid_plans = [Plan.BASIC.value, Plan.MEDIUM.value, Plan.MASTER.value]
    
    if new_plan not in valid_plans:
        raise HTTPException(status_code=400, detail="Plano inválido")
    
    # Gera URL de checkout
    checkout_url = f"/payments/stripe/checkout?plan={new_plan}&upgrade=1"
    
    return {
        "message": f"Redirecionando para upgrade para {new_plan}",
        "checkout_url": checkout_url,
        "plan": new_plan,
        "price_cents": PLAN_PRICES[new_plan],
    }


@router.get("/check-access")
async def check_access(
    feature: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Verifica se o usuário tem acesso a uma feature específica.
    Usado pelo frontend para validar antes de mostrar UI.
    """
    result = require_subscription(db, current_user, feature)
    
    return {
        "allowed": result["allowed"],
        "has_access": result["allowed"],
        "feature": feature,
        "redirect_url": result.get("redirect_url"),
        "required_plan": result.get("required_plan"),
    }


@router.get("/paywall-url")
async def get_paywall(
    feature: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
):
    """
    Retorna a URL do paywall para redirecionamento.
    """
    from vereda_backend.core.subscription import get_paywall_redirect_url
    
    return {
        "url": get_paywall_redirect_url(current_user, feature),
        "feature": feature,
    }
