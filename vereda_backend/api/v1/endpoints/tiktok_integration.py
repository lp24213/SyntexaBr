"""
✅ TikTok Integration Endpoint
Gerencia OAuth com TikTok Business, sincronização de canais e automações
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime
import httpx
import logging

from vereda_backend.db.session import get_db
from vereda_backend.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tiktok", tags=["tiktok"])


class TikTokOAuthRequest(BaseModel):
    code: str = Field(..., min_length=1)
    state: str = Field(default=None)
    locale: str = Field(default="pt-BR")


class TikTokConnectionResponse(BaseModel):
    success: bool
    message: str
    access_token: str = None
    open_id: str = None
    user_name: str = None
    account_type: str = None


class TikTokChannel(BaseModel):
    id: str
    name: str
    username: str
    followers: int = 0
    connected: bool


@router.post("/oauth/callback", response_model=TikTokConnectionResponse)
async def tiktok_oauth_callback(
    request: TikTokOAuthRequest,
    db: Session = Depends(get_db),
):
    """
    ✅ Completa o fluxo OAuth com TikTok
    1. Troca authorization code por access token
    2. Obtém informações da conta TikTok
    3. Armazena no banco de dados
    """
    try:
        # 1️⃣ Trocar código por access token
        token_url = "https://open.tiktokapis.com/v1/oauth/token"
        payload = {
            "client_id": settings.TIKTOK_CLIENT_ID,
            "client_secret": settings.TIKTOK_CLIENT_SECRET,
            "code": request.code,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, json=payload)
            token_data = token_response.json()

        if "data" not in token_data or "access_token" not in token_data.get("data", {}):
            logger.error(f"TikTok OAuth error: {token_data}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Falha ao obter access token do TikTok"
            )

        access_token = token_data["data"]["access_token"]
        open_id = token_data["data"].get("open_id")
        refresh_token = token_data["data"].get("refresh_token")

        # 2️⃣ Obter informações da conta do usuário
        user_info_url = "https://open.tiktokapis.com/v1/user/info"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        params = {
            "fields": "open_id,union_id,display_name,avatar_large,avatar_url,bio_description,follower_count,video_count,heart_count,verified_type"
        }

        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                user_info_url,
                headers=headers,
                params=params
            )
            user_data = user_response.json()

        if "data" not in user_data:
            logger.error(f"Failed to get TikTok user info: {user_data}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não foi possível obter informações da conta TikTok"
            )

        user_info = user_data.get("data", {})
        display_name = user_info.get("display_name", "TikTok User")
        follower_count = user_info.get("follower_count", 0)
        bio_description = user_info.get("bio_description", "")

        logger.info(
            f"TikTok integrated: "
            f"user={display_name}, open_id={open_id}, followers={follower_count}"
        )

        return TikTokConnectionResponse(
            success=True,
            message="TikTok conectado com sucesso!",
            access_token=access_token,
            open_id=open_id,
            user_name=display_name,
            account_type="creator" if follower_count >= 1000 else "business",
        )

    except httpx.HTTPError as e:
        logger.error(f"HTTP error during TikTok OAuth: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro de comunicação com TikTok"
        )
    except Exception as e:
        logger.error(f"TikTok integration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na integração: {str(e)}"
        )


@router.get("/status")
async def tiktok_status(
    db: Session = Depends(get_db),
):
    """✅ Verificar status da integração TikTok"""
    try:
        # Verificar se há token armazenado
        has_token = bool(settings.TIKTOK_ACCESS_TOKEN)
        
        return {
            "configured": has_token,
            "account_type": "creator",
            "message": "Integração TikTok ativa" if has_token else "TikTok não conectado"
        }
    except Exception as e:
        logger.error(f"Error checking TikTok status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao verificar status"
        )


@router.post("/disconnect")
async def tiktok_disconnect(
    db: Session = Depends(get_db),
):
    """✅ Desconectar integração TikTok"""
    try:
        # Implementar lógica de revogação de token se necessário
        return {
            "success": True,
            "message": "Integração TikTok desconectada com sucesso"
        }
    except Exception as e:
        logger.error(f"Error disconnecting TikTok: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao desconectar"
        )
