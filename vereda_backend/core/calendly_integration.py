# 📅 Calendly Integration
# Gerenciamento de agendamentos via Calendly API

import os
import logging
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger(__name__)

class CalendlyClient:
    """Cliente para integração com Calendly API"""
    
    BASE_URL = "https://api.calendly.com"
    
    def __init__(self, access_token: str | None = None):
        self.access_token = access_token or os.getenv("CALENDLY_API_KEY")
        self.user_uri = None
        
        if not self.access_token:
            logger.warning("⚠️ Calendly API key não configurada")
    
    async def get_current_user(self) -> Dict[str, Any] | None:
        """Obter informações do usuário atual"""
        if not self.access_token:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/users/me",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                self.user_uri = data.get("resource", {}).get("uri")
                return data.get("resource")
        except Exception as e:
            logger.error(f"❌ Erro ao obter usuário Calendly: {e}")
            return None
    
    async def list_scheduled_events(self, user_uri: str | None = None) -> list[Dict[str, Any]] | None:
        """Listar eventos agendados"""
        if not self.access_token:
            return None
        
        uri = user_uri or self.user_uri
        if not uri:
            await self.get_current_user()
            uri = self.user_uri
        
        if not uri:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/scheduled_events",
                    params={"user": uri},
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    timeout=10
                )
                response.raise_for_status()
                events = response.json().get("collection", [])
                logger.info(f"✅ {len(events)} eventos encontrados no Calendly")
                return events
        except Exception as e:
            logger.error(f"❌ Erro ao listar eventos Calendly: {e}")
            return None
    
    async def get_event_details(self, event_uri: str) -> Dict[str, Any] | None:
        """Obter detalhes de um evento específico"""
        if not self.access_token:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    event_uri,
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    timeout=10
                )
                response.raise_for_status()
                return response.json().get("resource")
        except Exception as e:
            logger.error(f"❌ Erro ao obter evento Calendly: {e}")
            return None
    
    async def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Verificar assinatura do webhook do Calendly (se necessário)"""
        # Calendly envia X-Calendly-Webhook-Signature header
        # Implementar verificação se necessário
        return True  # Por enquanto, aceitar todos


# ✅ Inicializar cliente Calendly global
calendly_client = CalendlyClient()
