from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from vereda_backend.core.config import settings
from vereda_backend.core.rate_limit import get_client_ip
from vereda_backend.core.security import get_current_admin
from vereda_backend.db import models
from vereda_backend.db.session import get_db
from vereda_backend.schemas.chat import ChatRequest, ChatResponse
from vereda_backend.services.chat_engine import create_chat_completion


router = APIRouter(prefix="/integrations")
_token_windows: Dict[str, List[float]] = {}


class ApiTokenCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    scopes: str = Field(default="chat:read,chat:write", max_length=255)
    expires_days: Optional[int] = Field(default=365, ge=1, le=3650)


class ApiTokenOut(BaseModel):
    id: int
    name: str
    token_prefix: str
    scopes: str
    active: bool
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]

    class Config:
        from_attributes = True


class ApiTokenCreateOut(ApiTokenOut):
    token: str


class ApiTokenRotateOut(ApiTokenOut):
    token: str


class IntegrationMeOut(BaseModel):
    token_prefix: str
    scopes: str
    active: bool
    expires_at: Optional[datetime]
    owner_email: str
    owner_user_id: int


class IntegrationConfigOut(BaseModel):
    token_rpm: int


class IntegrationConfigUpdate(BaseModel):
    token_rpm: int = Field(..., ge=1, le=10_000)


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _token_has_scope(scope_csv: str, wanted: str) -> bool:
    items = [s.strip().lower() for s in (scope_csv or "").split(",") if s.strip()]
    return wanted.lower() in items


def _resolve_integration_token(
    db: Session,
    raw_token: str,
) -> models.ApiIntegrationToken:
    if not raw_token:
        raise HTTPException(status_code=401, detail="Token de integração ausente.")
    token_hash = _hash_token(raw_token)
    row = (
        db.query(models.ApiIntegrationToken)
        .filter(models.ApiIntegrationToken.token_hash == token_hash)
        .first()
    )
    if not row:
        raise HTTPException(status_code=401, detail="Token de integração inválido.")
    if not row.active:
        raise HTTPException(status_code=403, detail="Token de integração revogado.")
    if row.expires_at and row.expires_at < datetime.utcnow():
        raise HTTPException(status_code=403, detail="Token de integração expirado.")
    return row


def _enforce_token_rate_limit(token_hash: str) -> None:
    rpm_limit = max(1, int(getattr(settings, "integration_token_rpm", 60) or 60))
    now_ts = datetime.utcnow().timestamp()
    arr = _token_windows.get(token_hash) or []
    arr = [ts for ts in arr if now_ts - ts < 60]
    if len(arr) >= rpm_limit:
        _token_windows[token_hash] = arr
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit do token atingido ({rpm_limit}/min).",
        )
    arr.append(now_ts)
    _token_windows[token_hash] = arr


@router.get("/tokens", response_model=List[ApiTokenOut])
def list_tokens(
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
) -> List[ApiTokenOut]:
    q = (
        db.query(models.ApiIntegrationToken)
        .filter(models.ApiIntegrationToken.owner_user_id == admin.id)
        .order_by(models.ApiIntegrationToken.created_at.desc())
    )
    return q.all()


@router.get("/config", response_model=IntegrationConfigOut)
def integration_config(
    admin: models.User = Depends(get_current_admin),
) -> IntegrationConfigOut:
    _ = admin
    rpm_limit = max(1, int(getattr(settings, "integration_token_rpm", 60) or 60))
    return IntegrationConfigOut(token_rpm=rpm_limit)


@router.put("/config", response_model=IntegrationConfigOut)
def integration_config_update(
    body: IntegrationConfigUpdate,
    admin: models.User = Depends(get_current_admin),
) -> IntegrationConfigOut:
    _ = admin
    settings.integration_token_rpm = int(body.token_rpm)
    return IntegrationConfigOut(token_rpm=int(settings.integration_token_rpm))


@router.post("/tokens", response_model=ApiTokenCreateOut, status_code=status.HTTP_201_CREATED)
def create_token(
    body: ApiTokenCreate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
) -> ApiTokenCreateOut:
    raw = "stx_" + secrets.token_urlsafe(36)
    token_hash = _hash_token(raw)
    prefix = raw[:16]
    expires_at = datetime.utcnow() + timedelta(days=int(body.expires_days or 365))

    row = models.ApiIntegrationToken(
        owner_user_id=admin.id,
        name=body.name.strip(),
        token_hash=token_hash,
        token_prefix=prefix,
        scopes=body.scopes.strip() or "chat:read,chat:write",
        active=True,
        expires_at=expires_at,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ApiTokenCreateOut(
        id=row.id,
        name=row.name,
        token_prefix=row.token_prefix,
        scopes=row.scopes,
        active=row.active,
        created_at=row.created_at,
        expires_at=row.expires_at,
        last_used_at=row.last_used_at,
        token=raw,
    )


@router.post("/tokens/{token_id}/rotate", response_model=ApiTokenRotateOut)
def rotate_token(
    token_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
) -> ApiTokenRotateOut:
    row = (
        db.query(models.ApiIntegrationToken)
        .filter(
            models.ApiIntegrationToken.id == token_id,
            models.ApiIntegrationToken.owner_user_id == admin.id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Token não encontrado.")
    raw = "stx_" + secrets.token_urlsafe(36)
    row.token_hash = _hash_token(raw)
    row.token_prefix = raw[:16]
    row.active = True
    row.last_used_at = None
    db.add(row)
    db.commit()
    db.refresh(row)
    return ApiTokenRotateOut(
        id=row.id,
        name=row.name,
        token_prefix=row.token_prefix,
        scopes=row.scopes,
        active=row.active,
        created_at=row.created_at,
        expires_at=row.expires_at,
        last_used_at=row.last_used_at,
        token=raw,
    )


@router.delete(
    "/tokens/{token_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def revoke_token(
    token_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
) -> Response:
    row = (
        db.query(models.ApiIntegrationToken)
        .filter(
            models.ApiIntegrationToken.id == token_id,
            models.ApiIntegrationToken.owner_user_id == admin.id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Token não encontrado.")
    row.active = False
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=IntegrationMeOut)
def integration_me(
    x_api_token: str | None = Header(default=None, alias="X-API-Token"),
    db: Session = Depends(get_db),
) -> IntegrationMeOut:
    row = _resolve_integration_token(db, (x_api_token or "").strip())
    if not _token_has_scope(row.scopes, "chat:read"):
        raise HTTPException(status_code=403, detail="Token sem escopo chat:read.")
    owner = db.query(models.User).filter(models.User.id == row.owner_user_id).first()
    if not owner:
        raise HTTPException(status_code=401, detail="Dono do token não encontrado.")
    return IntegrationMeOut(
        token_prefix=row.token_prefix,
        scopes=row.scopes,
        active=row.active,
        expires_at=row.expires_at,
        owner_email=owner.email,
        owner_user_id=owner.id,
    )


@router.post("/chat/completions", response_model=ChatResponse)
def integration_chat_completions(
    payload: ChatRequest,
    request: Request,
    x_api_token: str | None = Header(default=None, alias="X-API-Token"),
    db: Session = Depends(get_db),
) -> ChatResponse:
    row = _resolve_integration_token(db, (x_api_token or "").strip())
    if not _token_has_scope(row.scopes, "chat:write"):
        raise HTTPException(status_code=403, detail="Token sem escopo chat:write.")
    _enforce_token_rate_limit(row.token_hash)

    owner = db.query(models.User).filter(models.User.id == row.owner_user_id).first()
    if not owner:
        raise HTTPException(status_code=401, detail="Dono do token não encontrado.")

    resp = create_chat_completion(
        db,
        payload,
        owner,
        get_client_ip(request),
    )

    row.last_used_at = datetime.utcnow()
    db.add(row)
    db.commit()
    return resp

