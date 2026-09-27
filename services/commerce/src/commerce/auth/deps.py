"""The session check every private route depends on.

The Next.js sign-in redirect is a convenience only. This dependency is the actual gate:
no valid session cookie means 401, whatever the caller did to reach the API.

The assistant service is the one other caller. It sends ``Authorization: Bearer <service
token>`` plus ``X-On-Behalf-Of: <user id>`` after resolving the signed-in user from their own
session, so the model's side of the system never holds the customer's cookie. That identity is
accepted only on the routes in :data:`ASSISTANT_ROUTES`; everywhere else it gets 401, and
:func:`require_browser_user` refuses it outright (return confirmation, for example).
"""

from __future__ import annotations

import hmac
import uuid
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from ai_commerce_telemetry import SpanLabels, customer_hash, set_span_labels
from commerce.auth.models import Role, User
from commerce.auth.sessions import find_active_session
from commerce.config import Settings, get_settings
from commerce.db import get_db

# (method, path template) pairs the assistant may call on a customer's behalf: reading the
# catalog, stores, policies, their own cart, orders, and returns; adding to their cart;
# pricing a return (a quote changes nothing); and opening a support case. Nothing that
# confirms, pays, refunds, or signs in.
ASSISTANT_ROUTES: frozenset[tuple[str, str]] = frozenset(
    {
        ("GET", "/v1/categories"),
        ("GET", "/v1/catalog/vocabulary"),
        ("GET", "/v1/products"),
        ("GET", "/v1/products/{product_id}"),
        ("GET", "/v1/stores"),
        ("GET", "/v1/policies/search"),
        ("GET", "/v1/policies/{doc_id}"),
        ("GET", "/v1/cart"),
        ("PUT", "/v1/cart/items"),
        ("GET", "/v1/orders"),
        ("GET", "/v1/orders/{order_id}"),
        ("GET", "/v1/orders/{order_id}/return-options"),
        ("GET", "/v1/returns"),
        ("POST", "/v1/returns/quote"),
        ("GET", "/v1/returns/quotes/{quote_id}"),
        ("POST", "/v1/support/cases"),
    }
)

ON_BEHALF_OF_HEADER = "x-on-behalf-of"


@dataclass(frozen=True)
class Principal:
    user: User
    session_token: str | None
    # True when the assistant service is calling on the user's behalf (no browser session).
    via_assistant: bool = False

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


def _route_key(request: Request) -> tuple[str, str] | None:
    route = request.scope.get("route")
    if isinstance(route, APIRoute):
        return request.method, route.path
    return None


def _assistant_principal(request: Request, db: Session, settings: Settings) -> Principal | None:
    """The assistant's identity, if this request carries a valid one for an allowed route."""
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    expected = settings.assistant_service_token
    if not expected or not hmac.compare_digest(auth[7:].strip(), expected):
        raise _unauthorized()
    if _route_key(request) not in ASSISTANT_ROUTES:
        raise _unauthorized()
    try:
        user_id = uuid.UUID(request.headers.get(ON_BEHALF_OF_HEADER, ""))
    except ValueError:
        raise _unauthorized() from None
    user = db.get(User, user_id)
    if user is None:
        raise _unauthorized()
    return Principal(user=user, session_token=None, via_assistant=True)


def require_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Principal:
    principal = _assistant_principal(request, db, settings)
    if principal is None:
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            raise _unauthorized()
        row = find_active_session(db, token)
        if row is None:
            raise _unauthorized()
        principal = Principal(user=row.user, session_token=token)
    set_span_labels(
        SpanLabels(customer_hash=customer_hash(str(principal.id), settings.session_secret))
    )
    return principal


CurrentUser = Annotated[Principal, Depends(require_user)]


def require_browser_user(principal: CurrentUser) -> Principal:
    """The signed-in customer themselves, in their browser: never the assistant service."""
    if principal.via_assistant or principal.session_token is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This action needs the customer")
    return principal


BrowserUser = Annotated[Principal, Depends(require_browser_user)]


def require_staff(principal: CurrentUser) -> Principal:
    if principal.role not in (Role.STAFF, Role.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff only")
    return principal
