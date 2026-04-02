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


def create_access_token(
    subject: str,
    is_admin: bool = False,
    role: str = "user",
    expires_delta: Optional[timedelta] = None,
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(hours=12)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": subject, "is_admin": is_admin, "role": role}
    encoded_jwt = jwt.encode(to_encode, get_secret_key(), algorithm=ALGORITHM)
    return encoded_jwt


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
        token_data = TokenPayload(**payload)
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
        token_data = TokenPayload(**payload)
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

