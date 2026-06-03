"""
Dependencies de Subscription para FastAPI
==========================================

Protege rotas que requerem subscription ativa.
"""

from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from vereda_backend.db.session import get_db
from vereda_backend.db import models
from vereda_backend.core.security import get_current_user
from vereda_backend.core.subscription import (
    require_subscription,
    can_use_feature,
    check_and_update_subscription_status,
    get_paywall_redirect_url,
)


class SubscriptionRequired:
    """
    Dependency para proteger rotas que requerem subscription.
    
    Uso:
        @router.post("/premium-feature")
        async def premium_feature(
            user: models.User = Depends(SubscriptionRequired(feature="premium_ai")),
        ):
            return {"message": "Acesso permitido"}
    """
    
    def __init__(self, feature: Optional[str] = None, redirect: bool = False):
        self.feature = feature
        self.redirect = redirect
    
    def __call__(
        self,
        request: Request,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user),
    ) -> models.User:
        # Atualiza status
        current_user = check_and_update_subscription_status(db, current_user)
        
        # Verifica subscription
        result = require_subscription(db, current_user, self.feature)
        
        if not result["allowed"]:
            if self.redirect:
                raise RedirectResponse(
                    url=result["redirect_url"],
                    status_code=status.HTTP_303_SEE_OTHER,
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": result["error"],
                        "redirect_url": result["redirect_url"],
                        "required_plan": result.get("required_plan"),
                        "current_status": result.get("current_status"),
                    },
                )
        
        return current_user


def require_active_subscription(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """
    Dependency simples que requer subscription ativa.
    """
    current_user = check_and_update_subscription_status(db, current_user)
    result = require_subscription(db, current_user)
    
    if not result["allowed"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": result["error"],
                "redirect_url": result["redirect_url"],
                "current_status": result.get("current_status"),
            },
        )
    
    return current_user


def require_feature(feature: str):
    """
    Factory para criar dependency de feature específica.
    
    Uso:
        @router.post("/whatsapp")
        async def whatsapp(
            user: models.User = Depends(require_feature("whatsapp_saas")),
        ):
            return {"message": "WhatsApp acesso permitido"}
    """
    def checker(
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user),
    ) -> models.User:
        current_user = check_and_update_subscription_status(db, current_user)
        
        if not can_use_feature(current_user, feature):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": f"Feature '{feature}' não disponível no seu plano",
                    "redirect_url": get_paywall_redirect_url(current_user, feature),
                    "required_upgrade": True,
                },
            )
        
        return current_user
    
    return checker


def get_subscription_info(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> dict:
    """
    Retorna informações da subscription do usuário.
    """
    from vereda_backend.core.subscription import check_subscription_status, get_usage_stats
    
    current_user = check_and_update_subscription_status(db, current_user)
    
    return {
        "subscription": check_subscription_status(current_user),
        "usage": get_usage_stats(db, current_user),
    }
