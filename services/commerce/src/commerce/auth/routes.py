from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from commerce.auth import oidc
from commerce.auth.deps import CurrentUser
from commerce.auth.models import AuthSession, PasswordResetToken, Role, User
from commerce.auth.ratelimit import RateLimiter, get_rate_limiter
from commerce.auth.returnto import safe_return_to
from commerce.auth.schemas import (
    AuthConfigOut,
    ForgotPasswordRequest,
    MessageOut,
    ResetPasswordRequest,
    SignInRequest,
    SignUpRequest,
    UserOut,
)
from commerce.auth.sessions import (
    create_session,
    hash_password,
    hash_token,
    normalize_email,
    revoke_session,
    verify_password,
)
from commerce.config import Settings, get_settings
from commerce.db import get_db, utcnow
from commerce.metrics import signin_attempts

log = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/auth", tags=["auth"])

GENERIC_SIGNIN_ERROR = "Wrong email or password."
RESET_TOKEN_TTL = timedelta(minutes=30)

SettingsDep = Annotated[Settings, Depends(get_settings)]
DbDep = Annotated[Session, Depends(get_db)]
LimiterDep = Annotated[RateLimiter, Depends(get_rate_limiter)]


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


def _client_ip(request: Request) -> str:
    # The web app forwards the browser's address. In the cloud the ALB sets this header.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _email_key(email: str) -> str:
    return hashlib.sha256(email.encode()).hexdigest()[:32]


def _require_dev_provider(settings: Settings) -> None:
    if settings.auth_provider != "dev":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Password sign-in is not enabled")


@router.get("/config", response_model=AuthConfigOut)
def auth_config(settings: SettingsDep) -> AuthConfigOut:
    return AuthConfigOut(
        provider=settings.auth_provider,
        development_sign_in=settings.auth_provider == "dev",
    )


@router.post(
    "/sign-in",
    response_model=UserOut,
    responses={401: {"model": MessageOut}, 429: {"model": MessageOut}},
)
def sign_in(
    body: SignInRequest,
    request: Request,
    response: Response,
    db: DbDep,
    settings: SettingsDep,
    limiter: LimiterDep,
) -> UserOut:
    _require_dev_provider(settings)
    email = normalize_email(body.email)
    acct_key = f"rl:signin:acct:{_email_key(email)}"
    ip_key = f"rl:signin:ip:{_client_ip(request)}"
    window = settings.signin_window_seconds

    ip_count = limiter.hit(ip_key, window)
    if (
        ip_count > settings.signin_max_attempts_per_ip
        or limiter.peek(acct_key) >= settings.signin_max_failures_per_account
    ):
        signin_attempts.add(1, {"outcome": "rate_limited"})
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many sign-in attempts. Wait a few minutes and try again.",
            headers={"Retry-After": str(window)},
        )

    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(body.password, user.password_hash):
        limiter.hit(acct_key, window)
        signin_attempts.add(1, {"outcome": "failure"})
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, GENERIC_SIGNIN_ERROR)

    limiter.reset(acct_key)
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
    _require_dev_provider(settings)
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


@router.post("/forgot-password", response_model=MessageOut, status_code=status.HTTP_202_ACCEPTED)
def forgot_password(body: ForgotPasswordRequest, db: DbDep, settings: SettingsDep) -> MessageOut:
    _require_dev_provider(settings)
    message = MessageOut(
        message="If an account exists for that email, we've sent a link to reset the password."
    )
    user = db.scalar(select(User).where(User.email == normalize_email(body.email)))
    if user is None or user.password_hash is None:
        return message
    token = secrets.token_urlsafe(32)
    db.add(
        PasswordResetToken(
            user_id=user.id, token_hash=hash_token(token), expires_at=utcnow() + RESET_TOKEN_TTL
        )
    )
    db.commit()
    if settings.is_dev:
        # No email provider in development: the link goes to the server log, labeled.
        log.info(
            "DEVELOPMENT ONLY - password reset link (no email sent)",
            extra={"fields": {"reset_url": f"{settings.web_origin}/reset-password?token={token}"}},
        )
    else:  # pragma: no cover - an email adapter arrives with the cloud work
        log.error("password reset requested but no email adapter is configured")
    return message


@router.post(
    "/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={400: {"model": MessageOut}},
)
def reset_password(body: ResetPasswordRequest, db: DbDep, settings: SettingsDep) -> Response:
    _require_dev_provider(settings)
    row = db.scalar(
        select(PasswordResetToken)
        .where(PasswordResetToken.token_hash == hash_token(body.token))
        .with_for_update()
    )
    if row is None or row.used_at is not None or row.expires_at <= utcnow():
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "This reset link is invalid or has expired."
        )
    user = db.get(User, row.user_id)
    assert user is not None
    user.password_hash = hash_password(body.password)
    row.used_at = utcnow()
    # A password reset ends every existing session for the account.
    for session_row in db.scalars(
        select(AuthSession).where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))
    ):
        session_row.revoked_at = utcnow()
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/oidc/start", include_in_schema=False)
def oidc_start(
    settings: SettingsDep, return_to: Annotated[str | None, Query(alias="returnTo")] = None
) -> RedirectResponse:
    if settings.auth_provider != "oidc":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "OIDC sign-in is not enabled")
    try:
        url, cookie = oidc.build_authorization_redirect(settings, safe_return_to(return_to))
    except oidc.OidcError as exc:
        log.error("oidc start failed: %s", exc)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Sign-in is unavailable") from exc
    resp = RedirectResponse(url, status_code=status.HTTP_302_FOUND)
    resp.set_cookie(
        oidc.STATE_COOKIE,
        cookie,
        max_age=oidc.STATE_TTL_SECONDS,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    return resp


@router.get("/oidc/callback", include_in_schema=False)
def oidc_callback(
    request: Request, code: str, state: str, db: DbDep, settings: SettingsDep
) -> RedirectResponse:
    if settings.auth_provider != "oidc":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "OIDC sign-in is not enabled")
    cookie = request.cookies.get(oidc.STATE_COOKIE)
    if not cookie:
        return RedirectResponse("/sign-in?error=expired", status_code=status.HTTP_302_FOUND)
    try:
        claims, return_to = oidc.complete_authorization(
            settings, code=code, state=state, state_cookie=cookie
        )
    except (oidc.OidcError, Exception) as exc:  # noqa: BLE001 - any failure means "sign in again"
        log.warning("oidc callback rejected: %s", type(exc).__name__)
        return RedirectResponse("/sign-in?error=oidc", status_code=status.HTTP_302_FOUND)

    user = db.scalar(select(User).where(User.oidc_subject == claims.subject))
    if user is None:
        user = db.scalar(select(User).where(User.email == normalize_email(claims.email)))
        if user is None:
            user = User(
                email=normalize_email(claims.email),
                display_name=claims.name,
                role=Role.CUSTOMER,
            )
            db.add(user)
        user.oidc_subject = claims.subject
        db.flush()
    token, _ = create_session(db, user, settings.session_ttl_hours)
    db.commit()
    resp = RedirectResponse(safe_return_to(return_to), status_code=status.HTTP_302_FOUND)
    resp.delete_cookie(oidc.STATE_COOKIE, path="/")
    _set_session_cookie(resp, token, settings)
    return resp
