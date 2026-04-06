from datetime import datetime
from typing import Literal, Optional, Union

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str
    is_admin: bool = False


class UserCreatePublic(UserBase):
    password: str
    document: str
    cep: str
    state: str
    city: str
    address_line: str
    address_number: str
    address_complement: Optional[str] = None


class UserPublic(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None


class LoginSuccess(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class LoginNeeds2FA(BaseModel):
    requires_2fa: Literal[True] = True
    two_factor_token: str
    token_type: str = "bearer"


LoginResponse = Union[LoginSuccess, LoginNeeds2FA]


class TokenPayload(BaseModel):
    sub: str
    is_admin: bool = False
    role: str = "user"


class RefreshRequest(BaseModel):
    refresh_token: str


class TwoFactorVerify(BaseModel):
    two_factor_token: str
    code: str


class TwoFactorEnable(BaseModel):
    code: str


class VerificationRequest(BaseModel):
    email: EmailStr


class VerificationConfirm(BaseModel):
    email: EmailStr
    code: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    email: EmailStr
    code: str
    new_password: str

