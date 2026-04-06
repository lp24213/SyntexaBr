import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from vereda_backend.core.config import settings
from vereda_backend.db import models
from vereda_backend.db.session import get_db
from vereda_backend.schemas.auth import TokenPayload


pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/v1/auth/login", auto_error=False)


ALGORITHM = "HS256"


def get_secret_key() -> str:
    secret = (getattr(settings, "secret_key", "") or "").strip()
    if not secret:
        raise RuntimeError("VEREDA_SECRET_KEY não configurada.")
    return secret


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def _access_token_ttl() -> timedelta:
    mins = int(getattr(settings, "access_token_expire_minutes", 720) or 720)
    return timedelta(minutes=max(5, mins))


def create_access_token(
    subject: str,
    is_admin: bool = False,
    role: str = "user",
    expires_delta: Optional[timedelta] = None,
) -> str:
    if expires_delta is None:
        expires_delta = _access_token_ttl()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {
        "exp": expire,
        "sub": subject,
        "is_admin": is_admin,
        "role": role,
        "typ": "access",
    }
    encoded_jwt = jwt.encode(to_encode, get_secret_key(), algorithm=ALGORITHM)
    return encoded_jwt


def create_pre_2fa_token(subject: str) -> str:
    """JWT curto só para concluir o 2FA (não autoriza APIs)."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=10)
    to_encode = {"exp": expire, "sub": subject, "typ": "pre_2fa"}
    return jwt.encode(to_encode, get_secret_key(), algorithm=ALGORITHM)


def _hash_refresh(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def issue_refresh_token(db: Session, user: models.User) -> str:
    """Gera refresh opaco, persiste hash e devolve o token uma única vez."""
    raw = secrets.token_urlsafe(48)
    th = _hash_refresh(raw)
    days = int(getattr(settings, "refresh_token_expire_days", 30) or 30)
    exp = datetime.utcnow() + timedelta(days=max(1, days))
    row = models.RefreshToken(user_id=user.id, token_hash=th, expires_at=exp, revoked=False)
    db.add(row)
    db.commit()
    return raw


def revoke_refresh_token_string(db: Session, raw: str) -> None:
    th = _hash_refresh(raw)
    row = (
        db.query(models.RefreshToken)
        .filter(models.RefreshToken.token_hash == th, models.RefreshToken.revoked == False)
        .first()
    )
    if row:
        row.revoked = True
        db.add(row)
        db.commit()


def get_user_from_refresh_token(db: Session, raw: str) -> Optional[models.User]:
    th = _hash_refresh(raw)
    now = datetime.utcnow()
    row = (
        db.query(models.RefreshToken)
        .filter(
            models.RefreshToken.token_hash == th,
            models.RefreshToken.revoked == False,
            models.RefreshToken.expires_at > now,
        )
        .first()
    )
    if not row:
        return None
    user = db.query(models.User).filter(models.User.id == row.user_id).first()
    if not user or not user.is_active:
        return None
    return user


def user_requires_2fa_flow(user: models.User) -> bool:
    """Admin ou plano governo — 2FA só quando já ativado (TOTP)."""
    if getattr(user, "is_admin", False):
        return bool(getattr(user, "totp_enabled", False))
    plan = (getattr(user, "subscription_plan", "") or "").strip().lower()
    if plan in {"gov", "government"}:
        return bool(getattr(user, "totp_enabled", False))
    return False


def user_may_enable_2fa(user: models.User) -> bool:
    if getattr(user, "is_admin", False):
        return True
    plan = (getattr(user, "subscription_plan", "") or "").strip().lower()
    return plan in {"gov", "government"}


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, get_secret_key(), algorithms=[ALGORITHM])
        if payload.get("typ") == "pre_2fa":
            raise credentials_exception
        sub = payload.get("sub")
        if not sub or not isinstance(sub, str):
            raise credentials_exception
        token_data = TokenPayload(
            sub=sub,
            is_admin=payload.get("is_admin", False),
            role=payload.get("role", "user"),
        )
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.email == token_data.sub).first()
    if not user or not user.is_active:
        raise credentials_exception
    return user


def get_current_user_optional(
    db: Session = Depends(get_db), token: Optional[str] = Depends(oauth2_scheme_optional)
) -> Optional[models.User]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, get_secret_key(), algorithms=[ALGORITHM])
        if payload.get("typ") == "pre_2fa":
            return None
        sub = payload.get("sub")
        if not sub or not isinstance(sub, str):
            return None
        token_data = TokenPayload(
            sub=sub,
            is_admin=payload.get("is_admin", False),
            role=payload.get("role", "user"),
        )
        user = db.query(models.User).filter(models.User.email == token_data.sub).first()
        if user and user.is_active:
            return user
    except JWTError:
        pass
    return None


def get_current_admin(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem acessar este recurso",
        )
    return current_user

