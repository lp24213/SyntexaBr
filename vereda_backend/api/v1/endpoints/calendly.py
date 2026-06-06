# 📅 Calendly API Endpoints
# Integração de agendamentos com Calendly

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from vereda_backend.core.calendly_integration import calendly_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/calendly", tags=["calendly"])


class CalendlyEventResponse(BaseModel):
    """Resposta de evento Calendly"""
    uri: str
    name: str
    start_time: str
    end_time: str
    status: str


@router.get("/events", response_model=list[CalendlyEventResponse])
async def list_events():
    """Listar eventos agendados no Calendly"""
    try:
        events = await calendly_client.list_scheduled_events()
        
        if not events:
            return []
        
        # Filtrar e formatar eventos
        formatted_events = []
        for event in events:
            try:
                formatted_events.append({
                    "uri": event.get("uri", ""),
                    "name": event.get("name", ""),
                    "start_time": event.get("start_time", ""),
                    "end_time": event.get("end_time", ""),
                    "status": event.get("status", ""),
                })
            except Exception as e:
                logger.warning(f"⚠️ Erro ao formatar evento: {e}")
                continue
        
        logger.info(f"✅ {len(formatted_events)} eventos retornados")
        return formatted_events
    
    except Exception as e:
        logger.error(f"❌ Erro ao listar eventos: {e}")
        raise HTTPException(status_code=500, detail="Erro ao listar eventos Calendly")


@router.get("/availability")
async def check_availability():
    """Verificar disponibilidade do Calendly"""
    try:
        user = await calendly_client.get_current_user()
        
        if not user:
            return {
                "available": False,
                "message": "Calendly API não configurada"
            }
        
        return {
            "available": True,
            "user": user.get("name"),
            "url": f"https://calendly.com/{user.get('slug')}"
        }
    
    except Exception as e:
        logger.error(f"❌ Erro ao verificar disponibilidade: {e}")
        raise HTTPException(status_code=500, detail="Erro ao verificar Calendly")


@router.post("/webhook/events")
async def handle_calendly_webhook(payload: dict):
    """Webhook para eventos do Calendly (opcional)"""
    try:
        event_type = payload.get("event", "")
        resource = payload.get("resource", {})
        
        if event_type == "invitee.created":
            logger.info(f"✅ Novo agendamento: {resource.get('name')}")
        elif event_type == "invitee.canceled":
            logger.info(f"❌ Cancelado: {resource.get('name')}")
        
        return {"ok": True}
    
    except Exception as e:
        logger.error(f"❌ Erro ao processar webhook: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar webhook")
