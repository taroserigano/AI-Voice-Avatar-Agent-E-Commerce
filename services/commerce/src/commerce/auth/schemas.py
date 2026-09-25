from __future__ import annotations

import uuid
from typing import Literal

from pydantic import EmailStr, Field

from commerce.api_model import ApiModel
from commerce.auth.models import Role
from commerce.auth.sessions import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH


class SignInRequest(ApiModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=MAX_PASSWORD_LENGTH)


class SignUpRequest(ApiModel):
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)
    display_name: str = Field(min_length=1, max_length=120)


class ForgotPasswordRequest(ApiModel):
    email: EmailStr


class ResetPasswordRequest(ApiModel):
    token: str = Field(min_length=10, max_length=200)
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)


class UserOut(ApiModel):
    id: uuid.UUID
    email: str
    display_name: str
    role: Role


class AuthConfigOut(ApiModel):
    provider: Literal["dev", "oidc"]
    development_sign_in: bool = Field(
        description="True when the development sign-in adapter is active; the UI must say so."
    )
    min_password_length: int = MIN_PASSWORD_LENGTH


class MessageOut(ApiModel):
    message: str
