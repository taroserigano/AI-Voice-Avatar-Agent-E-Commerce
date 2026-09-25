"""The session check every private route depends on.

The Next.js sign-in redirect is a convenience only. This dependency is the actual gate:
no valid session cookie means 401, whatever the caller did to reach the API.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ai_commerce_telemetry import SpanLabels, customer_hash, set_span_labels
from commerce.auth.models import Role, User
from commerce.auth.sessions import find_active_session
from commerce.config import Settings, get_settings
from commerce.db import get_db


@dataclass(frozen=True)
class Principal:
    user: User
    session_token: str

    @property
    def id(self) -> uuid.UUID:
        return self.user.id

    @property
    def role(self) -> Role:
        return self.user.role


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sign in required",
    )


def require_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Principal:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise _unauthorized()
    row = find_active_session(db, token)
    if row is None:
        raise _unauthorized()
    set_span_labels(
        SpanLabels(customer_hash=customer_hash(str(row.user_id), settings.session_secret))
    )
    return Principal(user=row.user, session_token=token)


CurrentUser = Annotated[Principal, Depends(require_user)]


def require_staff(principal: CurrentUser) -> Principal:
    if principal.role not in (Role.STAFF, Role.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff only")
    return principal
