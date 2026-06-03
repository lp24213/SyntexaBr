"""
Middleware de Subscription - Proteção Global de Rotas
======================================================

Protege todas as rotas que requerem subscription válida.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

from vereda_backend.db.session import get_db
from vereda_backend.core.security import get_current_user_optional
from vereda_backend.core.subscription import require_subscription, can_use_feature


# Rotas que requerem subscription ativa (mas não são críticas)
PROTECTED_ROUTES = [
    "/api/v1/media/",
    "/api/v1/agents/",
    "/api/v1/autonomy/",
    "/api/v1/tools/",
    "/api/v1/export/",
    "/api/v1/voice/",
    "/api/v1/vision/",
]

# Rotas que requerem features específicas
FEATURE_ROUTES = {
    "/api/v1/integrations/whatsapp": "whatsapp_saas",
    "/api/v1/whatsapp/": "whatsapp_saas",
}

# Rotas públicas (sempre permitidas)
PUBLIC_ROUTES = [
    "/api/v1/auth/",
    "/api/v1/health",
    "/api/v1/public-chat",
    "/api/v1/webhooks/",
    "/api/v1/payments/",
    "/api/v1/subscription/plans",
    "/api/v1/subscription/status",
]


class SubscriptionMiddleware(BaseHTTPMiddleware):
    """
    Middleware que verifica subscription em todas as requisições protegidas.
    """
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method
        
        # Sempre permitir rotas públicas
        for public in PUBLIC_ROUTES:
            if path.startswith(public):
                return await call_next(request)
        
        # Apenas verificar métodos que modificam ou acessam recursos
        if method not in ["POST", "PUT", "DELETE", "PATCH"]:
            # GET pode ser verificado individualmente nas rotas
            return await call_next(request)
        
        # Verificar se rota é protegida
        is_protected = any(path.startswith(protected) for protected in PROTECTED_ROUTES)
        
        if not is_protected:
            return await call_next(request)
        
        # Verificar feature específica
        required_feature = None
        for route_prefix, feature in FEATURE_ROUTES.items():
            if path.startswith(route_prefix):
                required_feature = feature
                break
        
        try:
            # Obter usuário atual
            from vereda_backend.db.session import SessionLocal
            db = SessionLocal()
            try:
                user = await get_current_user_optional(request, db)
                
                if not user:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"error": "Autenticação necessária"},
                    )
                
                # Verificar subscription
                result = require_subscription(db, user, required_feature)
                
                if not result["allowed"]:
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={
                            "error": result["error"],
                            "redirect_url": result.get("redirect_url"),
                            "required_plan": result.get("required_plan"),
                            "code": "SUBSCRIPTION_REQUIRED",
                        },
                    )
                
                # Adicionar info da subscription ao request
                request.state.subscription = result
                request.state.user = user
                
            finally:
                db.close()
        
        except Exception as e:
            # Em caso de erro, permite passar (fail-open) ou bloqueia (fail-closed)
            # Aqui escolhemos fail-open para não quebrar o sistema
            pass
        
        return await call_next(request)
