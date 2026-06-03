"""
Sistema de Subscription Automatizado - Syntexa
==============================================

Gerencia:
- Trial automático
- Controle de acesso por plano
- Status de subscription
- Reativação automática
- Bloqueio automático
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from enum import Enum

from sqlalchemy.orm import Session

from vereda_backend.db import models
from vereda_ai.core.logging import get_logger

logger = get_logger(__name__)


class Plan(Enum):
    FREE = "free"
    BASIC = "basic"
    MEDIUM = "medium"
    MASTER = "master"
    GOV = "gov"


class SubscriptionStatus(Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    OVERDUE = "overdue"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PaymentStatus(Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    OVERDUE = "overdue"
    REFUNDED = "refunded"


# Configurações de trial
TRIAL_DAYS = 30  # 1 mês grátis
GRACE_PERIOD_DAYS = 3

# Limites por plano
PLAN_LIMITS = {
    Plan.FREE.value: {
        "messages_per_month": 200,
        "whatsapp_connections": 0,
        "agents": 0,
        "automations": 0,
        "api_requests_per_day": 100,
        "file_storage_mb": 100,
        "premium_ai": False,
        "voice_input": False,
        "export_formats": ["txt"],
    },
    Plan.BASIC.value: {
        "messages_per_month": 500,
        "whatsapp_connections": 1,
        "agents": 2,
        "automations": 5,
        "api_requests_per_day": 1000,
        "file_storage_mb": 500,
        "premium_ai": True,
        "voice_input": True,
        "export_formats": ["txt", "pdf", "docx"],
    },
    Plan.MEDIUM.value: {
        "messages_per_month": None,  # Ilimitado
        "whatsapp_connections": 3,
        "agents": 10,
        "automations": 50,
        "api_requests_per_day": 10000,
        "file_storage_mb": 2048,
        "premium_ai": True,
        "voice_input": True,
        "export_formats": ["txt", "pdf", "docx", "xlsx", "pptx"],
    },
    Plan.MASTER.value: {
        "messages_per_month": None,  # Ilimitado
        "whatsapp_connections": None,  # Ilimitado
        "agents": None,  # Ilimitado
        "automations": None,  # Ilimitado
        "api_requests_per_day": None,  # Ilimitado
        "file_storage_mb": 10240,
        "premium_ai": True,
        "voice_input": True,
        "export_formats": ["txt", "pdf", "docx", "xlsx", "pptx", "csv", "json"],
    },
    Plan.GOV.value: {
        "messages_per_month": None,
        "whatsapp_connections": None,
        "agents": None,
        "automations": None,
        "api_requests_per_day": None,
        "file_storage_mb": None,
        "premium_ai": True,
        "voice_input": True,
        "export_formats": ["txt", "pdf", "docx", "xlsx", "pptx", "csv", "json"],
    },
}

# Preços dos planos (em centavos, BRL)
PLAN_PRICES = {
    Plan.BASIC.value: 3900,    # R$ 39,00
    Plan.MEDIUM.value: 9900,   # R$ 99,00
    Plan.MASTER.value: 19900,  # R$ 199,00
}


def init_trial_for_user(user: models.User) -> None:
    """
    Inicializa o período de trial para um novo usuário.
    Chamado automaticamente após o cadastro.
    """
    now = datetime.now(timezone.utc)
    user.subscription_status = SubscriptionStatus.TRIAL.value
    user.trial_start = now
    user.trial_end = now + timedelta(days=TRIAL_DAYS)
    user.payment_status = PaymentStatus.PENDING.value
    user.subscription_plan = Plan.FREE.value
    
    # Define limites iniciais
    user.usage_limits = PLAN_LIMITS[Plan.FREE.value].copy()
    user.feature_flags = {
        "premium_ai": False,
        "whatsapp_saas": False,
        "voice_input": False,
        "api_access": False,
        "automations": False,
    }
    
    logger.info(f"Trial iniciado para user_id={user.id}, expira em {user.trial_end}")


def check_subscription_status(user: models.User) -> Dict[str, Any]:
    """
    Verifica o status atual da subscription e retorna informações detalhadas.
    """
    now = datetime.now(timezone.utc)
    
    result = {
        "user_id": user.id,
        "plan": user.subscription_plan,
        "status": user.subscription_status,
        "payment_status": user.payment_status,
        "is_active": False,
        "is_trial": False,
        "is_expired": False,
        "is_grace_period": False,
        "can_use_premium": False,
        "trial_days_left": 0,
        "expires_in_days": None,
        "features": {},
    }
    
    # Verifica trial
    if user.subscription_status == SubscriptionStatus.TRIAL.value:
        result["is_trial"] = True
        if user.trial_end:
            days_left = (user.trial_end - now).days
            result["trial_days_left"] = max(0, days_left)
            if days_left > 0:
                result["is_active"] = True
                result["can_use_premium"] = True
            else:
                result["is_expired"] = True
                result["is_active"] = False
    
    # Verifica subscription ativa
    elif user.subscription_status == SubscriptionStatus.ACTIVE.value:
        result["is_active"] = True
        result["can_use_premium"] = True
        if user.subscription_end:
            days_left = (user.subscription_end - now).days
            result["expires_in_days"] = max(0, days_left)
    
    # Verifica período de carência
    elif user.subscription_status == SubscriptionStatus.OVERDUE.value:
        if user.grace_period_until and user.grace_period_until > now:
            result["is_grace_period"] = True
            result["is_active"] = True  # Ainda pode usar durante carência
            result["can_use_premium"] = True
            days_left = (user.grace_period_until - now).days
            result["expires_in_days"] = max(0, days_left)
        else:
            result["is_expired"] = True
    
    # Status suspenso/cancelado/expirado
    elif user.subscription_status in [
        SubscriptionStatus.SUSPENDED.value,
        SubscriptionStatus.CANCELLED.value,
        SubscriptionStatus.EXPIRED.value,
    ]:
        result["is_expired"] = True
    
    # Se é admin, sempre tem acesso premium
    if user.is_admin:
        result["can_use_premium"] = True
        result["is_active"] = True
    
    # Adiciona features baseadas no plano
    result["features"] = get_plan_features(user.subscription_plan)
    
    return result


def get_plan_features(plan: str) -> Dict[str, Any]:
    """Retorna as features disponíveis para um plano."""
    plan_key = (plan or "free").lower()
    return PLAN_LIMITS.get(plan_key, PLAN_LIMITS[Plan.FREE.value]).copy()


def can_use_feature(user: models.User, feature: str) -> bool:
    """
    Verifica se o usuário pode usar uma feature específica.
    Features: premium_ai, whatsapp_saas, voice_input, api_access, automations
    """
    if user.is_admin:
        return True
    
    status = check_subscription_status(user)
    
    if not status["can_use_premium"]:
        return False
    
    features = status.get("features", {})
    
    if feature == "premium_ai":
        return features.get("premium_ai", False)
    elif feature == "whatsapp_saas":
        return user.subscription_plan in [Plan.MEDIUM.value, Plan.MASTER.value, Plan.GOV.value]
    elif feature == "voice_input":
        return features.get("voice_input", False)
    elif feature == "api_access":
        return user.subscription_plan in [Plan.BASIC.value, Plan.MEDIUM.value, Plan.MASTER.value, Plan.GOV.value]
    elif feature == "automations":
        return features.get("automations", 0) > 0 or user.subscription_plan in [Plan.MEDIUM.value, Plan.MASTER.value, Plan.GOV.value]
    
    return False


def check_and_update_subscription_status(db: Session, user: models.User) -> models.User:
    """
    Verifica e atualiza o status da subscription do usuário.
    Deve ser chamada periodicamente ou antes de operações importantes.
    """
    now = datetime.now(timezone.utc)
    
    # Se está em trial, verifica expiração
    if user.subscription_status == SubscriptionStatus.TRIAL.value:
        if user.trial_end and user.trial_end < now:
            # Trial expirou
            user.subscription_status = SubscriptionStatus.EXPIRED.value
            user.payment_status = PaymentStatus.OVERDUE.value
            logger.info(f"Trial expirado para user_id={user.id}")
    
    # Se está ativo, verifica expiração
    elif user.subscription_status == SubscriptionStatus.ACTIVE.value:
        if user.subscription_end and user.subscription_end < now:
            # Entra em período de carência
            user.subscription_status = SubscriptionStatus.OVERDUE.value
            user.grace_period_until = now + timedelta(days=GRACE_PERIOD_DAYS)
            user.payment_status = PaymentStatus.OVERDUE.value
            logger.info(f"Subscription vencida, grace period iniciado para user_id={user.id}")
    
    # Se está em período de carência, verifica expiração
    elif user.subscription_status == SubscriptionStatus.OVERDUE.value:
        if user.grace_period_until and user.grace_period_until < now:
            # Carência expirou, suspende
            user.subscription_status = SubscriptionStatus.SUSPENDED.value
            logger.info(f"Grace period expirado, user_id={user.id} suspenso")
    
    db.commit()
    return user


def activate_subscription(
    db: Session,
    user: models.User,
    plan: str,
    payment_gateway: str,
    gateway_customer_id: Optional[str] = None,
    gateway_subscription_id: Optional[str] = None,
    payment_amount: Optional[float] = None,
    period_days: int = 30,
) -> models.User:
    """
    Ativa ou renova uma subscription após pagamento.
    """
    now = datetime.now(timezone.utc)
    
    user.subscription_plan = plan
    user.subscription_status = SubscriptionStatus.ACTIVE.value
    user.payment_status = PaymentStatus.PAID.value
    user.payment_gateway = payment_gateway
    if gateway_customer_id:
        user.payment_gateway_customer_id = gateway_customer_id
    if gateway_subscription_id:
        user.payment_gateway_subscription_id = gateway_subscription_id
    
    # Define datas
    if not user.subscription_start:
        user.subscription_start = now
    user.subscription_end = now + timedelta(days=period_days)
    user.renewal_date = user.subscription_end
    
    # Atualiza pagamento
    user.last_payment_date = now
    user.last_payment_amount = payment_amount
    user.payment_failure_count = 0
    user.grace_period_until = None
    
    # Atualiza limites e features
    user.usage_limits = get_plan_features(plan)
    user.feature_flags = {
        "premium_ai": can_use_feature(user, "premium_ai"),
        "whatsapp_saas": can_use_feature(user, "whatsapp_saas"),
        "voice_input": can_use_feature(user, "voice_input"),
        "api_access": can_use_feature(user, "api_access"),
        "automations": can_use_feature(user, "automations"),
    }
    
    db.commit()
    logger.info(f"Subscription ativada: user_id={user.id}, plan={plan}, gateway={payment_gateway}")
    return user


def handle_payment_failure(db: Session, user: models.User) -> models.User:
    """
    Processa falha de pagamento.
    """
    user.payment_failure_count += 1
    user.payment_status = PaymentStatus.FAILED.value
    
    # Após 3 tentativas, marca como overdue
    if user.payment_failure_count >= 3:
        user.subscription_status = SubscriptionStatus.OVERDUE.value
        user.payment_status = PaymentStatus.OVERDUE.value
        if not user.grace_period_until:
            user.grace_period_until = datetime.now(timezone.utc) + timedelta(days=GRACE_PERIOD_DAYS)
        logger.warning(f"Payment failed 3x, user_id={user.id} marcado como overdue")
    
    db.commit()
    return user


def cancel_subscription(db: Session, user: models.User, immediate: bool = False) -> models.User:
    """
    Cancela a subscription do usuário.
    """
    if immediate:
        user.subscription_status = SubscriptionStatus.CANCELLED.value
        user.subscription_end = datetime.now(timezone.utc)
    else:
        # Cancela ao final do período pago
        user.subscription_status = SubscriptionStatus.CANCELLED.value
        # Mantém acesso até subscription_end
    
    db.commit()
    logger.info(f"Subscription cancelada: user_id={user.id}, immediate={immediate}")
    return user


def get_paywall_redirect_url(user: models.User, feature: Optional[str] = None) -> str:
    """
    Retorna a URL de redirecionamento para o paywall/planos.
    """
    base_url = "https://syntexabr.com.br/i18n/pt-BR/plans"
    
    if feature:
        return f"{base_url}?feature={feature}&blocked=1"
    
    return f"{base_url}?blocked=1"


def require_subscription(db: Session, user: models.User, feature: Optional[str] = None) -> Dict[str, Any]:
    """
    Verifica se o usuário tem subscription válida.
    Retorna dict com sucesso ou informações de erro.
    """
    # Atualiza status antes de verificar
    user = check_and_update_subscription_status(db, user)
    
    status = check_subscription_status(user)
    
    if status["can_use_premium"]:
        if feature and not can_use_feature(user, feature):
            return {
                "allowed": False,
                "error": f"Feature '{feature}' não disponível no seu plano",
                "redirect_url": get_paywall_redirect_url(user, feature),
                "required_plan": Plan.BASIC.value if feature == "api_access" else Plan.MEDIUM.value,
            }
        return {"allowed": True, "status": status}
    
    return {
        "allowed": False,
        "error": "Subscription necessária",
        "redirect_url": get_paywall_redirect_url(user, feature),
        "required_plan": Plan.BASIC.value,
        "current_status": status,
    }


# Funções de uso/controle

def increment_usage(db: Session, user: models.User, usage_type: str, amount: int = 1) -> bool:
    """
    Incrementa o uso de um recurso.
    Retorna True se ainda está dentro do limite.
    """
    if user.is_admin:
        return True
    
    # Verifica se tem subscription válida
    status = check_subscription_status(user)
    if not status["can_use_premium"]:
        return False
    
    limits = user.usage_limits or {}
    current = limits.get(f"{usage_type}_used", 0)
    limit = limits.get(usage_type)
    
    # Se não tem limite definido, permite
    if limit is None:
        return True
    
    # Verifica se ainda pode usar
    if current + amount <= limit:
        limits[f"{usage_type}_used"] = current + amount
        user.usage_limits = limits
        db.commit()
        return True
    
    return False


def get_usage_stats(db: Session, user: models.User) -> Dict[str, Any]:
    """
    Retorna estatísticas de uso do usuário.
    """
    limits = user.usage_limits or {}
    
    return {
        "plan": user.subscription_plan,
        "status": user.subscription_status,
        "messages": {
            "used": limits.get("messages_per_month_used", 0),
            "limit": limits.get("messages_per_month"),
            "remaining": None if limits.get("messages_per_month") is None else max(0, limits.get("messages_per_month", 0) - limits.get("messages_per_month_used", 0)),
        },
        "whatsapp_connections": {
            "used": limits.get("whatsapp_connections_used", 0),
            "limit": limits.get("whatsapp_connections"),
        },
        "agents": {
            "used": limits.get("agents_used", 0),
            "limit": limits.get("agents"),
        },
        "automations": {
            "used": limits.get("automations_used", 0),
            "limit": limits.get("automations"),
        },
        "api_requests": {
            "used": limits.get("api_requests_per_day_used", 0),
            "limit": limits.get("api_requests_per_day"),
        },
    }


def reset_monthly_usage(db: Session) -> None:
    """
    Reseta o contador de uso mensal para todos os usuários.
    Deve ser chamado no primeiro dia de cada mês.
    """
    # Esta função seria chamada por um cron job
    logger.info("Resetando contadores de uso mensal")
    # Implementação depende da infraestrutura de cron
    pass
