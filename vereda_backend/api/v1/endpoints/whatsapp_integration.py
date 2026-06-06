"""
✅ WhatsApp Integration Endpoint
Gerencia OAuth com Meta, sincronização de números e conversas
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
router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


class WhatsAppOAuthRequest(BaseModel):
    code: str = Field(..., min_length=1)
    locale: str = Field(default="pt-BR")


class WhatsAppConnectionResponse(BaseModel):
    success: bool
    message: str
    phone_number_id: str = None
    display_number: str = None
    waba_id: str = None


class WhatsAppCompany(BaseModel):
    id: str
    name: str
    phone_numbers: list = []
    connected: bool


@router.post("/oauth/callback", response_model=WhatsAppConnectionResponse)
async def whatsapp_oauth_callback(
    request: WhatsAppOAuthRequest,
    db: Session = Depends(get_db),
):
    """
    ✅ Completa o fluxo OAuth com Meta
    1. Troca authorization code por access token
    2. Obtém WABA ID e Phone Number ID
    3. Armazena no banco de dados
    """
    try:
        # 1️⃣ Trocar código por access token
        token_url = "https://graph.instagram.com/v18.0/oauth/access_token"
        payload = {
            "client_id": settings.WHATSAPP_META_APP_ID,
            "client_secret": settings.WHATSAPP_META_APP_SECRET,
            "redirect_uri": "https://syntexabr.com.br/whatsapp/callback",
            "code": request.code,
        }

        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=payload)
            token_data = token_response.json()

        if "access_token" not in token_data:
            logger.error(f"Meta OAuth error: {token_data}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Falha ao obter access token do Meta"
            )

        access_token = token_data["access_token"]
        user_id = token_data.get("user_id")

        # 2️⃣ Obter Business Account ID e Phone Numbers
        me_url = f"https://graph.instagram.com/v18.0/me"
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            me_response = await client.get(
                me_url,
                headers=headers,
                params={"fields": "id,name,email"}
            )
            me_data = me_response.json()

        if "error" in me_data:
            logger.error(f"Failed to get Meta user info: {me_data}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não foi possível obter informações da conta Meta"
            )

        user_id = me_data.get("id")
        user_name = me_data.get("name")

        # 3️⃣ Obter Business Account
        ba_url = f"https://graph.instagram.com/v18.0/{user_id}/businesses"
        
        async with httpx.AsyncClient() as client:
            ba_response = await client.get(ba_url, headers=headers)
            ba_data = ba_response.json()

        if "data" not in ba_data or len(ba_data["data"]) == 0:
            logger.error("No business accounts found")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nenhuma conta de negócios encontrada no Meta"
            )

        waba_id = ba_data["data"][0]["id"]

        # 4️⃣ Obter Phone Number ID
        phone_url = f"https://graph.instagram.com/v18.0/{waba_id}/phone_numbers"
        
        async with httpx.AsyncClient() as client:
            phone_response = await client.get(phone_url, headers=headers)
            phone_data = phone_response.json()

        phone_number_id = None
        display_number = None

        if "data" in phone_data and len(phone_data["data"]) > 0:
            phone_number_id = phone_data["data"][0]["id"]
            display_number = phone_data["data"][0].get("display_phone_number", "")

        logger.info(
            f"WhatsApp integrated: "
            f"user={user_name}, waba={waba_id}, phone={phone_number_id}"
        )

        return WhatsAppConnectionResponse(
            success=True,
            message="WhatsApp conectado com sucesso!",
            phone_number_id=phone_number_id,
            display_number=display_number,
            waba_id=waba_id,
        )

    except httpx.HTTPError as e:
        logger.error(f"HTTP error during WhatsApp OAuth: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro de comunicação com Meta"
        )
    except Exception as e:
        logger.error(f"WhatsApp integration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na integração: {str(e)}"
        )


@router.get("/companies", response_model=list[WhatsAppCompany])
async def list_companies(
    db: Session = Depends(get_db),
):
    """
    ✅ Lista empresas/contas conectadas
    Placeholder para retornar dados do banco
    """
    # TODO: Implementar query no banco para retornar empresas conectadas
    return [
        WhatsAppCompany(
            id="test_company",
            name="Syntexa Teste",
            phone_numbers=[],
            connected=False,
        )
    ]


@router.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    ✅ Recebe webhooks do WhatsApp
    - Mensagens recebidas
    - Status de delivery
    - Atualizações de conta
    """
    data = await request.json()
    
    # Validar token de verificação
    mode = data.get("hub.mode")
    token = data.get("hub.verify_token")
    challenge = data.get("hub.challenge")
    
    if mode == "subscribe" and token == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified")
        return challenge
    
    # Processar webhook
    logger.info(f"WhatsApp webhook received: {data}")
    
    # TODO: Processar mensagem e atualizar no banco
    
    return {"status": "ok"}


@router.get("/status")
async def whatsapp_status():
    """
    ✅ Status da integração WhatsApp
    """
    return {
        "configured": bool(settings.WHATSAPP_META_APP_ID),
        "app_id": settings.WHATSAPP_META_APP_ID,
        "webhook_url": "https://syntexabr.com.br/v1/whatsapp/webhook",
        "timestamp": datetime.now().isoformat(),
    }
