from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from vereda_backend.core.admin_allowed_ips import load_allowed_ips, save_allowed_ips
from vereda_backend.core.security import get_current_admin
from vereda_backend.db import models
from vereda_backend.db.session import get_db
from vereda_backend.schemas.knowledge import (
    KnowledgeBaseItemCreate,
    KnowledgeBaseItemPublic,
)


router = APIRouter(prefix="/admin")


@router.get("/system/status")
def admin_system_status(_: models.User = Depends(get_current_admin)) -> dict:
    """
    Monitor interno: CPU, RAM, stress, requisições ativas, fila ARQ aproximada, slots de concorrência.
    """
    from vereda_backend.core.concurrency_control import stats as conc_stats
    from vereda_backend.core.load_monitor import snapshot

    return {"load": snapshot(), "concurrency": conc_stats()}


@router.get("/me")
def admin_me(current_admin: models.User = Depends(get_current_admin)):
    return {
        "id": current_admin.id,
        "email": current_admin.email,
        "full_name": current_admin.full_name,
        "is_admin": current_admin.is_admin,
    }


@router.post("/knowledge", response_model=KnowledgeBaseItemPublic)
def create_knowledge_item(
    payload: KnowledgeBaseItemCreate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin),
) -> KnowledgeBaseItemPublic:
    item = models.KnowledgeItem(
        title=payload.title,
        question=payload.question,
        answer=payload.answer,
        tags=payload.tags or "",
        owner_id=current_admin.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/knowledge", response_model=List[KnowledgeBaseItemPublic])
def list_knowledge_items(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin),
) -> List[KnowledgeBaseItemPublic]:
    items = db.query(models.KnowledgeItem).order_by(models.KnowledgeItem.id.desc()).all()
    return items


class AllowedIpsPayload(BaseModel):
    ips: List[str] = Field(default_factory=list)


@router.get("/network/allowed-ips")
def get_network_allowed_ips(_: models.User = Depends(get_current_admin)) -> dict:
    """IPs cadastrados para referência (ex.: firewall/nginx na instituição)."""
    return {"ips": load_allowed_ips()}


@router.put("/network/allowed-ips")
def put_network_allowed_ips(
    body: AllowedIpsPayload,
    _: models.User = Depends(get_current_admin),
) -> dict:
    """Substitui a lista de IPs (um por linha no cliente; aqui lista normalizada)."""
    saved = save_allowed_ips(body.ips)
    return {"ok": True, "ips": saved}

