"""Delegation tokens: how the assistant gateway tells the planner who it's acting for.

The gateway signs a short-lived JWT per planner call (HS256, shared secret). It travels in
the HTTP ``Authorization`` header only, never in A2A message parts, so no model ever sees
it. The planner accepts one only if it is for this audience, from the gateway, unexpired,
at most 5 minutes long, scoped for catalog reads, and not seen before (``jti``).
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass

import jwt

ISSUER = "assistant-gateway"
AUDIENCE = "shopping-planner"
SCOPE = "catalog:read basket:estimate"
MAX_LIFETIME_S = 300
_LEEWAY_S = 5


class DelegationError(Exception):
    pass


@dataclass(frozen=True)
class Delegation:
    customer_id: uuid.UUID
    conversation_id: str
    jti: str
    expires_at: int


def mint(secret: str, customer_id: uuid.UUID, conversation_id: str, lifetime_s: int = 120) -> str:
    now = int(time.time())
    return jwt.encode(
        {
            "iss": ISSUER,
            "aud": AUDIENCE,
            "sub": str(customer_id),
            "cid": conversation_id,
            "scope": SCOPE,
            "iat": now,
            "exp": now + min(lifetime_s, MAX_LIFETIME_S),
            "jti": uuid.uuid4().hex,
        },
        secret,
        algorithm="HS256",
    )


class ReplayGuard:
    """Remembers ``jti`` values until their token expires. One process; tokens are
    single-use and short, so a restart only reopens a window of at most 5 minutes."""

    def __init__(self) -> None:
        self._seen: dict[str, int] = {}
        self._lock = threading.Lock()

    def first_use(self, jti: str, expires_at: int) -> bool:
        now = int(time.time())
        with self._lock:
            self._seen = {k: exp for k, exp in self._seen.items() if exp + _LEEWAY_S >= now}
            if jti in self._seen:
                return False
            self._seen[jti] = expires_at
            return True


def verify(token: str, secret: str, replay: ReplayGuard) -> Delegation:
    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience=AUDIENCE,
            issuer=ISSUER,
            leeway=_LEEWAY_S,
            options={"require": ["exp", "iat", "sub", "jti", "aud", "iss"]},
        )
    except jwt.PyJWTError as exc:
        raise DelegationError(type(exc).__name__) from exc
    if int(claims["exp"]) - int(claims["iat"]) > MAX_LIFETIME_S:
        raise DelegationError("token lifetime too long")
    if not set(SCOPE.split()) <= set(str(claims.get("scope", "")).split()):
        raise DelegationError("missing scope")
    try:
        customer = uuid.UUID(str(claims["sub"]))
    except ValueError as exc:
        raise DelegationError("bad subject") from exc
    if not replay.first_use(str(claims["jti"]), int(claims["exp"])):
        raise DelegationError("token already used")
    return Delegation(
        customer_id=customer,
        conversation_id=str(claims.get("cid", "")),
        jti=str(claims["jti"]),
        expires_at=int(claims["exp"]),
    )
