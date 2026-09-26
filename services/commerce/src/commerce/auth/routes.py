"""Sign-in: check the email and password, then set a session cookie. Nothing else."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from commerce.auth.deps import CurrentUser
from commerce.auth.models import Role, User
from commerce.auth.schemas import MessageOut, SignInRequest, SignUpRequest, UserOut
from commerce.auth.sessions import (
    create_session,
    hash_password,
    normalize_email,
    revoke_session,
    verify_password,
)
from commerce.config import Settings, get_settings
from commerce.db import get_db
from commerce.metrics import signin_attempts

router = APIRouter(prefix="/v1/auth", tags=["auth"])

WRONG_CREDENTIALS = "Wrong email or password."

SettingsDep = Annotated[Settings, Depends(get_settings)]
DbDep = Annotated[Session, Depends(get_db)]


def _user_out(user: User) -> UserOut:
    return UserOut(id=user.id, email=user.email, display_name=user.display_name, role=user.role)


def _set_session_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=settings.session_ttl_hours * 3600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


@router.post("/sign-in", response_model=UserOut, responses={401: {"model": MessageOut}})
def sign_in(body: SignInRequest, response: Response, db: DbDep, settings: SettingsDep) -> UserOut:
    user = db.scalar(select(User).where(User.email == normalize_email(body.email)))
    if user is None or not verify_password(body.password, user.password_hash):
        signin_attempts.add(1, {"outcome": "failure"})
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, WRONG_CREDENTIALS)
    token, _ = create_session(db, user, settings.session_ttl_hours)
    db.commit()
    _set_session_cookie(response, token, settings)
    signin_attempts.add(1, {"outcome": "success"})
    return _user_out(user)


@router.post(
    "/sign-up",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": MessageOut}},
)
def sign_up(body: SignUpRequest, response: Response, db: DbDep, settings: SettingsDep) -> UserOut:
    user = User(
        email=normalize_email(body.email),
        display_name=body.display_name.strip(),
        role=Role.CUSTOMER,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, "An account with this email already exists. Try signing in."
        ) from None
    token, _ = create_session(db, user, settings.session_ttl_hours)
    db.commit()
    _set_session_cookie(response, token, settings)
    return _user_out(user)


@router.post("/sign-out", status_code=status.HTTP_204_NO_CONTENT)
def sign_out(request: Request, db: DbDep, settings: SettingsDep) -> Response:
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        revoke_session(db, token)
        db.commit()
    resp = Response(status_code=status.HTTP_204_NO_CONTENT)
    resp.delete_cookie(settings.session_cookie_name, path="/", samesite="lax")
    return resp


@router.get("/me", response_model=UserOut)
def me(principal: CurrentUser) -> UserOut:
    return _user_out(principal.user)
