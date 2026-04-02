from datetime import datetime, timedelta
from secrets import randbelow

from fastapi import APIRouter, Depends, HTTPException, Request, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from vereda_backend.core.security import (
    create_access_token,
    get_current_admin,
    get_current_user,
    get_password_hash,
    verify_password,
)
from vereda_backend.core.rate_limit import (
    get_client_ip,
    login_limiter,
    register_limiter,
    password_reset_limiter,
    verify_email_limiter,
)
from vereda_backend.db import models
from vereda_backend.db.session import get_db
from vereda_backend.schemas.auth import (
    Token,
    UserCreate,
    UserCreatePublic,
    UserPublic,
    VerificationConfirm,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from vereda_backend.services import events


router = APIRouter(prefix="/auth")


def _generate_code() -> str:
    return f"{randbelow(1000000):06d}"


def _create_verification_code(
    db: Session, user: models.User, purpose: str, minutes_valid: int = 30
) -> str:
    code = _generate_code()
    expires_at = datetime.utcnow() + timedelta(minutes=minutes_valid)
    row = models.VerificationCode(
        user_id=user.id,
        code=code,
        purpose=purpose,
        expires_at=expires_at,
    )
    db.add(row)
    db.commit()
    return code


def _send_code_or_500(email: str, code: str, purpose: str) -> None:
    try:
        events.send_verification_code_email(email, code, purpose=purpose)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha ao enviar e-mail de verificação: {exc}",
        ) from exc


@router.post("/login", response_model=Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    login_limiter.check(
        get_client_ip(request),
        detail="Muitas tentativas de login. Aguarde 1 minuto.",
    )
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        # Webhook de login com falha (via Resend)
        events.notify_login_failed(form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos",
        )
    user_role = getattr(user, "role", "user") or "user"
    access_token = create_access_token(subject=user.email, is_admin=user.is_admin, role=user_role)

    # Webhook de login bem-sucedido
    events.notify_login_success(user)
    return Token(access_token=access_token)


@router.get("/me")
def auth_me(current_user: models.User = Depends(get_current_user)):
    """Retorna o usuário logado com plano e papel (para o frontend sincronizar limites e navegação)."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "subscription_plan": getattr(current_user, "subscription_plan", "free") or "free",
        "role": getattr(current_user, "role", "user") or "user",
        "is_admin": bool(current_user.is_admin),
    }


@router.post("/users", response_model=UserPublic)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin),
) -> UserPublic:
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-mail já cadastrado",
        )
    user = models.User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        is_admin=payload.is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Webhook de novo usuário registrado
    events.notify_user_registered(user)

    return user


@router.post("/public-register")
def public_register(
    request: Request,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
) -> dict:
    """
    Cadastro público com validação mais solta: aceita o JSON vindo do frontend
    e garante apenas os campos mínimos para criar o usuário e enviar o código.
    """
    register_limiter.check(
        get_client_ip(request),
        detail="Muitos cadastros deste IP. Aguarde 1 hora.",
    )
    email = (payload.get("email") or "").strip()
    password = payload.get("password") or ""
    full_name = payload.get("full_name") or None
    document = (payload.get("document") or "").strip() or None
    cep = (payload.get("cep") or "").strip() or ""
    state = (payload.get("state") or "").strip() or ""
    city = (payload.get("city") or "").strip() or ""
    address_line = (payload.get("address_line") or "").strip() or ""
    address_number = (payload.get("address_number") or "").strip() or ""
    address_complement = payload.get("address_complement") or None
    _valid_roles = {"user", "teacher", "researcher", "enterprise"}
    role = (payload.get("role") or "user").strip().lower()
    if role not in _valid_roles:
        role = "user"

    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-mail e senha são obrigatórios.",
        )

    # Validação de força de senha
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A senha deve ter no mínimo 8 caracteres.",
        )
    if len(password) > 128:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A senha não pode exceder 128 caracteres.",
        )
    # Verifica se a senha tem pelo menos um número ou caractere especial
    has_digit = any(c.isdigit() for c in password)
    has_upper = any(c.isupper() for c in password)
    if not has_digit and not has_upper:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A senha deve conter pelo menos um número ou letra maiúscula.",
        )

    # Validação básica de e-mail
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de e-mail inválido.",
        )

    existing_email = db.query(models.User).filter(models.User.email == email).first()
    existing_doc = None
    if document:
        existing_doc = (
            db.query(models.User).filter(models.User.document == document).first()
        )

    # Se já existe usuário com esse e-mail/documento, apenas reenviar código de verificação
    if existing_email:
        user = existing_email
        code = _create_verification_code(db, user, purpose="signup")
        _send_code_or_500(user.email, code, purpose="signup")
        return {
            "detail": "E-mail já cadastrado. Reenviamos um código de verificação para seu e-mail."
        }
    if existing_doc:
        # Evita enviar código para outro e-mail quando o documento já pertence
        # a uma conta diferente da informada no cadastro público.
        if existing_doc.email != email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Documento já cadastrado em outro e-mail.",
            )
        user = existing_doc
        code = _create_verification_code(db, user, purpose="signup")
        _send_code_or_500(user.email, code, purpose="signup")
        return {
            "detail": "Documento já cadastrado. Reenviamos um código de verificação para seu e-mail."
        }

    user = models.User(
        email=email,
        full_name=full_name,
        hashed_password=get_password_hash(password),
        is_active=False,
        is_admin=False,
        role=role,
        document=document,
        cep=cep,
        state=state,
        city=city,
        address_line=address_line,
        address_number=address_number,
        address_complement=address_complement,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    code = _create_verification_code(db, user, purpose="signup")
    _send_code_or_500(user.email, code, purpose="signup")

    return {"detail": "Usuário criado. Enviamos um código de verificação para seu e-mail."}


@router.post("/verify-email")
def verify_email(
    request: Request,
    payload: VerificationConfirm,
    db: Session = Depends(get_db),
) -> dict:
    verify_email_limiter.check(
        get_client_ip(request),
        detail="Muitas tentativas de verificação. Aguarde 5 minutos.",
    )
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuário não encontrado.")

    now = datetime.utcnow()
    code_row = (
        db.query(models.VerificationCode)
        .filter(
            models.VerificationCode.user_id == user.id,
            models.VerificationCode.code == payload.code,
            models.VerificationCode.purpose == "signup",
            models.VerificationCode.used_at.is_(None),
            models.VerificationCode.expires_at >= now,
        )
        .order_by(models.VerificationCode.created_at.desc())
        .first()
    )
    if not code_row:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Código inválido ou expirado.")

    user.is_active = True
    code_row.used_at = now
    db.add(user)
    db.add(code_row)
    db.commit()
    return {"detail": "E-mail verificado com sucesso. Você já pode fazer login."}


@router.post("/request-password-reset")
def request_password_reset(
    request: Request,
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
) -> dict:
    password_reset_limiter.check(
        get_client_ip(request),
        detail="Muitos pedidos de reset. Aguarde 1 hora.",
    )
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if user:
        code = _create_verification_code(db, user, purpose="reset")
        _send_code_or_500(user.email, code, purpose="reset")
    # Resposta genérica para não vazar existência de usuário
    return {"detail": "Se o e-mail existir, um código de redefinição será enviado."}


@router.post("/reset-password")
def reset_password(
    payload: PasswordResetConfirm,
    db: Session = Depends(get_db),
) -> dict:
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuário não encontrado.")

    now = datetime.utcnow()
    code_row = (
        db.query(models.VerificationCode)
        .filter(
            models.VerificationCode.user_id == user.id,
            models.VerificationCode.code == payload.code,
            models.VerificationCode.purpose == "reset",
            models.VerificationCode.used_at.is_(None),
            models.VerificationCode.expires_at >= now,
        )
        .order_by(models.VerificationCode.created_at.desc())
        .first()
    )
    if not code_row:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Código inválido ou expirado.")

    user.hashed_password = get_password_hash(payload.new_password)
    code_row.used_at = now
    db.add(user)
    db.add(code_row)
    db.commit()
    return {"detail": "Senha redefinida com sucesso."}

