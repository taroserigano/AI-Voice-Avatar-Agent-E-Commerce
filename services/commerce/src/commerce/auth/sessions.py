"""Server-side sessions and password hashing."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from commerce.auth.models import AuthSession, User
from commerce.db import utcnow

_hasher = PasswordHasher()
# Verified against when the account doesn't exist, so a missing account takes the same time
# as a wrong password and the response can't reveal which one happened.
_DUMMY_HASH = _hasher.hash("not-a-real-password-used-for-timing-only")

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 256


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerificationError, InvalidHashError):
        return False


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def normalize_email(email: str) -> str:
    return email.strip().lower()


def create_session(db: Session, user: User, ttl_hours: int) -> tuple[str, AuthSession]:
    """Create a session and return (raw cookie token, row). Only the hash is stored."""
    token = secrets.token_urlsafe(32)
    row = AuthSession(
        user_id=user.id,
        token_hash=hash_token(token),
        expires_at=utcnow() + timedelta(hours=ttl_hours),
    )
    db.add(row)
    return token, row


def find_active_session(db: Session, token: str, now: datetime | None = None) -> AuthSession | None:
    now = now or utcnow()
    row = db.scalar(
        select(AuthSession)
        .options(joinedload(AuthSession.user))
        .where(AuthSession.token_hash == hash_token(token))
    )
    if row is None or row.revoked_at is not None or row.expires_at <= now:
        return None
    return row


def revoke_session(db: Session, token: str) -> None:
    row = db.scalar(select(AuthSession).where(AuthSession.token_hash == hash_token(token)))
    if row is not None and row.revoked_at is None:
        row.revoked_at = utcnow()
