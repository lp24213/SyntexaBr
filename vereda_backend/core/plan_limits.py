"""
Limites de uso por plano (mensagens/mês e mídia/mês).
Reconhecimento de pagamento: planos basic/medium/master são ativados via webhook Stripe.
"""
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from vereda_backend.db import models


# Limite de mensagens do usuário (role=user) no mês atual. None = ilimitado.
PLAN_MESSAGE_LIMIT: dict[str, Optional[int]] = {
    "anon": 120,
    "free": 200,
    "basic": 500,
    "medium": None,
    "master": None,
}

# Limites por tipo de mídia no mês (por usuário autenticado; anônimo por IP).
PLAN_MEDIA_LIMIT: dict[str, dict[str, Optional[int]]] = {
    "anon": {"image": 25, "video": 8, "music": 15, "tts": 40},
    "free": {"image": 35, "video": 15, "music": 25, "tts": 80},
    "basic": {"image": 80, "video": 40, "music": 80, "tts": 300},
    "medium": {"image": None, "video": None, "music": None, "tts": None},
    "master": {"image": None, "video": None, "music": None, "tts": None},
}


def get_message_limit(plan: Optional[str]) -> Optional[int]:
    """Retorna o limite de mensagens do plano (None = ilimitado)."""
    if not plan:
        return PLAN_MESSAGE_LIMIT.get("free", 200)
    key = (plan or "").lower().strip()
    return PLAN_MESSAGE_LIMIT.get(key, PLAN_MESSAGE_LIMIT["free"])


def get_effective_plan(plan: Optional[str]) -> str:
    if not plan:
        return "anon"
    key = (plan or "").lower().strip()
    if key in PLAN_MEDIA_LIMIT:
        return key
    return "free"


def count_user_messages_this_month(db: Session, user_id: int) -> int:
    """Conta quantas mensagens (role=user) o usuário enviou no mês atual."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    q = (
        db.query(func.count(models.ConversationLog.id))
        .filter(
            models.ConversationLog.user_id == user_id,
            models.ConversationLog.role == "user",
            models.ConversationLog.created_at >= start,
        )
    )
    return (q.scalar() or 0)


def get_media_limit(plan: Optional[str], media_kind: str) -> Optional[int]:
    key = get_effective_plan(plan)
    kind = (media_kind or "").lower().strip()
    return PLAN_MEDIA_LIMIT.get(key, PLAN_MEDIA_LIMIT["free"]).get(kind, 0)


def count_media_usage_this_month(
    db: Session,
    media_kind: str,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
) -> int:
    from datetime import datetime

    start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    action = f"media_generate_{(media_kind or '').lower().strip()}"
    q = db.query(func.count(models.AuditLog.id)).filter(
        models.AuditLog.action == action,
        models.AuditLog.created_at >= start,
    )
    if user_id is not None:
        q = q.filter(models.AuditLog.user_id == user_id)
    else:
        q = q.filter(models.AuditLog.ip_address == (ip_address or "unknown"))
    return q.scalar() or 0


def user_over_message_limit(db: Session, user: models.User) -> bool:
    """True se o usuário já atingiu o limite de mensagens do plano no mês."""
    limit = get_message_limit(user.subscription_plan)
    if limit is None:
        return False
    return count_user_messages_this_month(db, user.id) >= limit
