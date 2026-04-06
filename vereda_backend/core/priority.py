"""Prioridade de tráfego: governo > autenticado > público (Fase 3)."""
from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from vereda_backend.db import models


class TrafficPriority(IntEnum):
    PUBLIC = 0
    AUTH = 1
    GOV = 2


def priority_for_user(user: Optional["models.User"]) -> TrafficPriority:
    if user is None:
        return TrafficPriority.PUBLIC
    if getattr(user, "is_admin", False):
        return TrafficPriority.GOV
    plan = (getattr(user, "subscription_plan", "") or "").strip().lower()
    if plan in ("gov", "government"):
        return TrafficPriority.GOV
    return TrafficPriority.AUTH
