from datetime import datetime, timedelta
from secrets import randbelow
from urllib.parse import quote
import logging
import secrets

logger = logging.getLogger(__name__)

from jose import JWTError, jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

import pyotp
import requests

from vereda_backend.core.security import (
    ALGORITHM,
    create_access_token,
    create_pre_2fa_token,
    get_current_admin,
    get_current_user,
    get_secret_key,
    get_user_from_refresh_token,
    issue_refresh_token,
    revoke_refresh_token_string,
    user_may_enable_2fa,
    user_requires_2fa_flow,
    get_password_hash,
    verify_password,
)
from vereda_backend.core.config import settings
from vereda_backend.core.rate_limit import (
    get_client_ip,
    is_test_request,
    login_limiter,
    register_limiter,
    password_reset_limiter,
    verify_email_limiter,
)
from vereda_backend.core.turnstile import verify_turnstile_token
from vereda_backend.db import models
from vereda_backend.db.session import get_db
from vereda_backend.schemas.auth import (
    LoginNeeds2FA,
    LoginResponse,
    LoginSuccess,
    RefreshRequest,
    TwoFactorEnable,
    TwoFactorVerify,
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


def _github_callback_url() -> str:
    custom = (getattr(settings, "github_oauth_callback_url", None) or "").strip()
    if custom:
        return custom
    return f"https://api.syntexabr.com.br{settings.api_v1_prefix}/auth/github/callback"


class GitHubOAuthEmailMissing(Exception):
    """Conta GitHub sem e-mail visível para a API (perfil privado / sem primary)."""


def _github_oauth_frontend_url(query: str) -> str:
    base = settings.frontend_base_url.rstrip("/")
    path = (getattr(settings, "frontend_oauth_return_path", None) or "/login").strip()
    if not path.startswith("/"):
        path = "/" + path
    path = path.rstrip("/") or "/login"
    q = (query or "").lstrip("?&")
    return f"{base}{path}/?{q}"


@router.post("/login", response_model=LoginResponse)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> LoginResponse:
    login_limiter.check(
        get_client_ip(request),
        detail="Muitas tentativas de login. Aguarde 1 minuto.",
    )
    turnstile_token = request.headers.get("x-turnstile-token") or ""
    if not verify_turnstile_token(turnstile_token, remote_ip=get_client_ip(request)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verificação de segurança falhou. Atualize a página e tente novamente.",
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

    if user_requires_2fa_flow(user):
        pre = create_pre_2fa_token(user.email)
        return LoginNeeds2FA(two_factor_token=pre)

    access_token = create_access_token(subject=user.email, is_admin=user.is_admin, role=user_role)
    refresh_token = issue_refresh_token(db, user)

    # Webhook de login bem-sucedido
    events.notify_login_success(user)
    return LoginSuccess(access_token=access_token, refresh_token=refresh_token)


@router.get("/github/login")
def github_login_start() -> RedirectResponse:
    client_id = (getattr(settings, "github_client_id", None) or "").strip()
    if not client_id:
        raise HTTPException(status_code=503, detail="GitHub SSO não configurado no servidor.")
    state = secrets.token_urlsafe(24)
    callback = _github_callback_url()
    # OAuth exige redirect_uri codificado; GitHub compara com o cadastro exato do app.
    url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={quote(client_id, safe='')}"
        f"&redirect_uri={quote(callback, safe='')}"
        "&scope=user:email"
        f"&state={state}"
    )
    return RedirectResponse(url=url, status_code=302)


@router.get("/github/callback")
def github_login_callback(
    code: str,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    client_id = (getattr(settings, "github_client_id", None) or "").strip()
    client_secret = (getattr(settings, "github_client_secret", None) or "").strip()
    if not client_id or not client_secret:
        raise HTTPException(status_code=503, detail="GitHub SSO não configurado no servidor.")

    callback = _github_callback_url()
    try:
        token_resp = requests.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": callback,
            },
            timeout=30,
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()
        if not isinstance(token_data, dict):
            logger.warning("GitHub OAuth: resposta de token inesperada (não é JSON objeto).")
            raise RuntimeError("GitHub não retornou access token.")
        gh_err = (token_data.get("error") or "").strip()
        if gh_err:
            logger.warning(
                "GitHub OAuth token error: %s — %s",
                gh_err,
                token_data.get("error_description") or "",
            )
            return RedirectResponse(
                url=_github_oauth_frontend_url("gh_error=oauth"),
                status_code=302,
            )
        gh_access = (token_data.get("access_token") or "").strip()
        if not gh_access:
            logger.warning("GitHub OAuth: sem access_token na resposta.")
            raise RuntimeError("GitHub não retornou access token.")

        user_resp = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {gh_access}", "Accept": "application/json"},
            timeout=30,
        )
        user_resp.raise_for_status()
        raw_profile = user_resp.json()
        user_data = raw_profile if isinstance(raw_profile, dict) else {}

        email = (user_data.get("email") or "").strip().lower()
        if not email:
            emails_resp = requests.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {gh_access}", "Accept": "application/json"},
                timeout=30,
            )
            emails_resp.raise_for_status()
            emails_data = emails_resp.json()
            if isinstance(emails_data, list):
                primary = next((e for e in emails_data if isinstance(e, dict) and e.get("primary")), None)
                chosen = primary or next((e for e in emails_data if isinstance(e, dict)), None)
                if isinstance(chosen, dict):
                    email = str(chosen.get("email") or "").strip().lower()

        if not email:
            raise GitHubOAuthEmailMissing()

        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            full_name = (user_data.get("name") or user_data.get("login") or "").strip() or None
            placeholder_pw = secrets.token_urlsafe(32)
            user = models.User(
                email=email,
                full_name=full_name,
                hashed_password=get_password_hash(placeholder_pw),
                is_active=True,
                is_admin=False,
                role="user",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            events.notify_user_registered(user)

        if user_requires_2fa_flow(user):
            pre = create_pre_2fa_token(user.email)
            return RedirectResponse(
                url=_github_oauth_frontend_url(f"two_factor_token={quote(pre, safe='')}"),
                status_code=302,
            )

        user_role = getattr(user, "role", "user") or "user"
        access_token = create_access_token(subject=user.email, is_admin=user.is_admin, role=user_role)
        refresh_token = issue_refresh_token(db, user)
        events.notify_login_success(user)
        return RedirectResponse(
            url=_github_oauth_frontend_url(
                f"gh_token={quote(access_token, safe='')}&gh_refresh={quote(refresh_token, safe='')}"
            ),
            status_code=302,
        )
    except HTTPException:
        raise
    except GitHubOAuthEmailMissing:
        return RedirectResponse(
            url=_github_oauth_frontend_url("gh_error=no_email"),
            status_code=302,
        )
    except Exception as exc:
        logger.exception("GitHub OAuth callback falhou: %s", exc)
        return RedirectResponse(
            url=_github_oauth_frontend_url("gh_error=1"),
            status_code=302,
        )


@router.post("/refresh", response_model=LoginSuccess)
def refresh_token_endpoint(payload: RefreshRequest, db: Session = Depends(get_db)) -> LoginSuccess:
    user = get_user_from_refresh_token(db, payload.refresh_token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido ou expirado.")
    revoke_refresh_token_string(db, payload.refresh_token)
    user_role = getattr(user, "role", "user") or "user"
    access_token = create_access_token(subject=user.email, is_admin=user.is_admin, role=user_role)
    new_refresh = issue_refresh_token(db, user)
    return LoginSuccess(access_token=access_token, refresh_token=new_refresh)


@router.post("/2fa/verify", response_model=LoginSuccess)
def verify_two_factor(payload: TwoFactorVerify, db: Session = Depends(get_db)) -> LoginSuccess:
    try:
        decoded = jwt.decode(payload.two_factor_token, get_secret_key(), algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 2FA inválido ou expirado.")
    if decoded.get("typ") != "pre_2fa":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token não é de segundo fator.")
    email = decoded.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido.")
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inválido.")
    secret = getattr(user, "totp_secret", None) or ""
    if not secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA não configurado para esta conta.")
    totp = pyotp.TOTP(secret)
    if not totp.verify(payload.code.strip().replace(" ", ""), valid_window=1):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Código TOTP inválido.")
    user_role = getattr(user, "role", "user") or "user"
    access_token = create_access_token(subject=user.email, is_admin=user.is_admin, role=user_role)
    refresh_token = issue_refresh_token(db, user)
    events.notify_login_success(user)
    return LoginSuccess(access_token=access_token, refresh_token=refresh_token)


@router.post("/2fa/setup")
def setup_two_factor(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> dict:
    if not user_may_enable_2fa(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="2FA disponível apenas para administradores ou contas governo.",
        )
    secret = pyotp.random_base32()
    current_user.totp_secret = secret
    current_user.totp_enabled = False
    db.add(current_user)
    db.commit()
    uri = pyotp.TOTP(secret).provisioning_uri(
        name=current_user.email, issuer_name="Syntexa"
    )
    return {"secret": secret, "otpauth_uri": uri}


@router.post("/2fa/enable")
def enable_two_factor(
    payload: TwoFactorEnable,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> dict:
    if not user_may_enable_2fa(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão.")
    secret = getattr(current_user, "totp_secret", None) or ""
    if not secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Execute /auth/2fa/setup antes.")
    totp = pyotp.TOTP(secret)
    if not totp.verify(payload.code.strip().replace(" ", ""), valid_window=1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Código inválido.")
    current_user.totp_enabled = True
    db.add(current_user)
    db.commit()
    return {"detail": "2FA ativado. Próximo login exigirá o código do autenticador."}


@router.get("/me")
def auth_me(current_user: models.User = Depends(get_current_user)):
    """Retorna o usuário logado com plano e papel (para o frontend sincronizar limites e navegação)."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "username": getattr(current_user, "username", None),
        "avatar_url": getattr(current_user, "avatar_url", None),
        "document": getattr(current_user, "document", None),
        "cep": getattr(current_user, "cep", None),
        "state": getattr(current_user, "state", None),
        "city": getattr(current_user, "city", None),
        "address_line": getattr(current_user, "address_line", None),
        "address_number": getattr(current_user, "address_number", None),
        "address_complement": getattr(current_user, "address_complement", None),
        "subscription_plan": getattr(current_user, "subscription_plan", "free") or "free",
        "role": getattr(current_user, "role", "user") or "user",
        "is_admin": bool(current_user.is_admin),
    }


@router.put("/me")
def update_auth_me(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> dict:
    full_name = (payload.get("full_name") or "").strip()
    username = (payload.get("username") or "").strip().lower()
    avatar_url = (payload.get("avatar_url") or "").strip()
    document = (payload.get("document") or "").strip()
    cep = (payload.get("cep") or "").strip()
    state = (payload.get("state") or "").strip()
    city = (payload.get("city") or "").strip()
    address_line = (payload.get("address_line") or "").strip()
    address_number = (payload.get("address_number") or "").strip()
    address_complement = (payload.get("address_complement") or "").strip()

    if full_name:
        current_user.full_name = full_name[:255]

    if username:
        if len(username) < 3 or len(username) > 30:
            raise HTTPException(status_code=400, detail="Username deve ter entre 3 e 30 caracteres.")
        if not all(c.isalnum() or c in ("_", ".") for c in username):
            raise HTTPException(status_code=400, detail="Username aceita apenas letras, números, '_' e '.'.")
        exists = (
            db.query(models.User)
            .filter(models.User.username == username)
            .filter(models.User.id != current_user.id)
            .first()
        )
        if exists:
            raise HTTPException(status_code=400, detail="Username já está em uso.")
        current_user.username = username

    if avatar_url:
        if not (avatar_url.startswith("data:image/") or avatar_url.startswith("https://") or avatar_url.startswith("http://")):
            raise HTTPException(status_code=400, detail="Avatar inválido. Use imagem data URL ou link HTTP(S).")
        if len(avatar_url) > 2_000_000:
            raise HTTPException(status_code=400, detail="Avatar muito grande.")
        current_user.avatar_url = avatar_url

    if document:
        exists_doc = (
            db.query(models.User)
            .filter(models.User.document == document)
            .filter(models.User.id != current_user.id)
            .first()
        )
        if exists_doc:
            raise HTTPException(status_code=400, detail="CPF/CNPJ já está em uso em outra conta.")
        current_user.document = document
    if cep:
        current_user.cep = cep[:16]
    if state:
        current_user.state = state[:64]
    if city:
        current_user.city = city[:128]
    if address_line:
        current_user.address_line = address_line[:255]
    if address_number:
        current_user.address_number = address_number[:32]
    if address_complement:
        current_user.address_complement = address_complement[:255]

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "username": getattr(current_user, "username", None),
        "avatar_url": getattr(current_user, "avatar_url", None),
        "document": getattr(current_user, "document", None),
        "cep": getattr(current_user, "cep", None),
        "state": getattr(current_user, "state", None),
        "city": getattr(current_user, "city", None),
        "address_line": getattr(current_user, "address_line", None),
        "address_number": getattr(current_user, "address_number", None),
        "address_complement": getattr(current_user, "address_complement", None),
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
    turnstile_token = payload.get("turnstile_token") or ""
    if not verify_turnstile_token(turnstile_token, remote_ip=get_client_ip(request)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verificação de segurança falhou. Atualize a página e tente novamente.",
        )
    if not is_test_request(request):
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

