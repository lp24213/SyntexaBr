"""
Gestão de clientes institucionais (escolas, municípios, governos estaduais/federais).
Todos os endpoints exigem autenticação como administrador.

Fluxo:
  1. Admin cria um cliente → sistema gera uma license_key única
  2. Admin baixa o pacote offline com a chave embutida
  3. Instala nas máquinas da escola/prefeitura
  4. O sistema instalado faz heartbeat periódico em /institutional/heartbeat/<key>
  5. Admin monitora status/atividade no painel
"""
import hashlib
import os
import secrets
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from vereda_backend.core.security import get_current_admin
from vereda_backend.db import models
from vereda_backend.db.session import get_db


router = APIRouter(prefix="/institutional")


# ─────────────────────────── Schemas ────────────────────────────

class ClientCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    cnpj: Optional[str] = Field(default=None, max_length=20)
    client_type: str = Field(default="escola", pattern="^(escola|municipio|estado|universidade|federal)$")
    contact_name: Optional[str] = Field(default=None, max_length=255)
    contact_email: Optional[str] = Field(default=None, max_length=255)
    contact_phone: Optional[str] = Field(default=None, max_length=32)
    city: Optional[str] = Field(default=None, max_length=128)
    state: Optional[str] = Field(default=None, max_length=64)
    plan: str = Field(default="basico", pattern="^(basico|avancado|enterprise)$")
    notes: Optional[str] = Field(default=None, max_length=2000)
    expires_days: Optional[int] = Field(default=365, ge=1, le=3650)


class ClientUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=3, max_length=255)
    contact_name: Optional[str] = Field(default=None, max_length=255)
    contact_email: Optional[str] = Field(default=None, max_length=255)
    contact_phone: Optional[str] = Field(default=None, max_length=32)
    plan: Optional[str] = Field(default=None, pattern="^(basico|avancado|enterprise)$")
    active: Optional[bool] = None
    notes: Optional[str] = Field(default=None, max_length=2000)
    expires_days: Optional[int] = Field(default=None, ge=1, le=3650)


class ClientOut(BaseModel):
    id: int
    name: str
    cnpj: Optional[str]
    client_type: str
    contact_name: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    city: Optional[str]
    state: Optional[str]
    plan: str
    license_key: str
    active: bool
    notes: Optional[str]
    created_at: datetime
    expires_at: Optional[datetime]
    last_seen_at: Optional[datetime]

    class Config:
        from_attributes = True


class HeartbeatOut(BaseModel):
    ok: bool
    message: str


# ─────────────────────────── Helpers ────────────────────────────

def _generate_license_key(name: str) -> str:
    """
    Gera uma chave de licença única e não-sequencial.
    Formato: SYNTEXA-<8hex>-<8hex>-<8hex>  (ex: SYNTEXA-A1B2C3D4-E5F60718-9A0B1C2D)
    """
    rand = secrets.token_bytes(24)
    h = hashlib.sha256(name.encode("utf-8") + rand).hexdigest().upper()
    return f"SYNTEXA-{h[:8]}-{h[8:16]}-{h[16:24]}"


# ─────────────────────────── Endpoints ───────────────────────────

@router.post("/clients", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
def create_client(
    body: ClientCreate,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(get_current_admin),
) -> ClientOut:
    """Registra um novo cliente institucional e gera a chave de licença."""
    license_key = _generate_license_key(body.name)
    # Garante unicidade (probabilidade infinitesimal de colisão, mas protegemos)
    while db.query(models.InstitutionalClient).filter_by(license_key=license_key).first():
        license_key = _generate_license_key(body.name)

    expires_at = datetime.utcnow() + timedelta(days=body.expires_days or 365)

    client = models.InstitutionalClient(
        name=body.name,
        cnpj=body.cnpj,
        client_type=body.client_type,
        contact_name=body.contact_name,
        contact_email=body.contact_email,
        contact_phone=body.contact_phone,
        city=body.city,
        state=body.state,
        plan=body.plan,
        license_key=license_key,
        notes=body.notes,
        expires_at=expires_at,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("/clients", response_model=List[ClientOut])
def list_clients(
    active_only: bool = False,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(get_current_admin),
) -> List[ClientOut]:
    """Lista todos os clientes institucionais."""
    q = db.query(models.InstitutionalClient)
    if active_only:
        q = q.filter_by(active=True)
    return q.order_by(models.InstitutionalClient.created_at.desc()).all()


@router.get("/clients/{client_id}", response_model=ClientOut)
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(get_current_admin),
) -> ClientOut:
    """Retorna detalhes de um cliente por ID."""
    client = db.query(models.InstitutionalClient).filter_by(id=client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    return client


@router.patch("/clients/{client_id}", response_model=ClientOut)
def update_client(
    client_id: int,
    body: ClientUpdate,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(get_current_admin),
) -> ClientOut:
    """Atualiza dados de um cliente institucional."""
    client = db.query(models.InstitutionalClient).filter_by(id=client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    for field, value in body.model_dump(exclude_none=True).items():
        if field == "expires_days":
            client.expires_at = datetime.utcnow() + timedelta(days=value)
        else:
            setattr(client, field, value)

    db.commit()
    db.refresh(client)
    return client


@router.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_client(
    client_id: int,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(get_current_admin),
) -> None:
    """Desativa (soft-delete) um cliente institucional."""
    client = db.query(models.InstitutionalClient).filter_by(id=client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    client.active = False
    db.commit()


@router.post("/clients/{client_id}/renew", response_model=ClientOut)
def renew_license(
    client_id: int,
    expires_days: int = 365,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(get_current_admin),
) -> ClientOut:
    """Renova a licença de um cliente por N dias a partir de hoje."""
    client = db.query(models.InstitutionalClient).filter_by(id=client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    client.expires_at = datetime.utcnow() + timedelta(days=expires_days)
    client.active = True
    db.commit()
    db.refresh(client)
    return client


@router.post("/clients/{client_id}/regenerate-key", response_model=ClientOut)
def regenerate_license_key(
    client_id: int,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(get_current_admin),
) -> ClientOut:
    """Gera uma nova chave de licença para o cliente (revoga a anterior)."""
    client = db.query(models.InstitutionalClient).filter_by(id=client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    new_key = _generate_license_key(client.name)
    while db.query(models.InstitutionalClient).filter_by(license_key=new_key).first():
        new_key = _generate_license_key(client.name)

    client.license_key = new_key
    db.commit()
    db.refresh(client)
    return client


# ─────── Heartbeat público (sem auth — chamado pelo sistema instalado) ─────────

@router.post("/heartbeat/{license_key}", response_model=HeartbeatOut)
def system_heartbeat(
    license_key: str,
    db: Session = Depends(get_db),
) -> HeartbeatOut:
    """
    Endpoint chamado periodicamente pelo sistema offline instalado para
    confirmar que a licença está ativa. Não exige autenticação de usuário.
    Atualiza o campo last_seen_at do cliente.
    """
    client = db.query(models.InstitutionalClient).filter_by(license_key=license_key).first()
    if not client:
        raise HTTPException(status_code=404, detail="Licença não encontrada.")

    if not client.active:
        return HeartbeatOut(ok=False, message="Licença desativada. Entre em contato com o administrador.")

    if client.expires_at and client.expires_at < datetime.utcnow():
        return HeartbeatOut(ok=False, message="Licença expirada. Renove para continuar.")

    client.last_seen_at = datetime.utcnow()
    db.commit()
    return HeartbeatOut(ok=True, message="Licença válida.")


# ─────── Validação de licença (sem auth — verificação interna do sistema) ──────

@router.get("/validate/{license_key}")
def validate_license(
    license_key: str,
    db: Session = Depends(get_db),
) -> dict:
    """
    Retorna informações básicas da licença para o sistema offline validar na inicialização.
    Não expõe dados sensíveis de contato.
    """
    client = db.query(models.InstitutionalClient).filter_by(license_key=license_key).first()
    if not client:
        raise HTTPException(status_code=404, detail="Licença não encontrada.")

    if not client.active:
        raise HTTPException(status_code=403, detail="Licença desativada.")

    if client.expires_at and client.expires_at < datetime.utcnow():
        raise HTTPException(status_code=403, detail="Licença expirada.")

    return {
        "valid": True,
        "plan": client.plan,
        "client_type": client.client_type,
        "name": client.name,
        "expires_at": client.expires_at.isoformat() if client.expires_at else None,
    }
