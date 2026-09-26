from __future__ import annotations

import uuid

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


class UserOut(ApiModel):
    id: uuid.UUID
    email: str
    display_name: str
    role: Role


class MessageOut(ApiModel):
    message: str
