from __future__ import annotations

import time
import uuid

import jwt
import pytest

from ai_commerce_planner.delegation import (
    AUDIENCE,
    ISSUER,
    DelegationError,
    ReplayGuard,
    mint,
    verify,
)

SECRET = "test-secret-0123456789-0123456789"
ALICE = uuid.UUID("00000000-0000-0000-0000-00000000a11c")


def raw(**overrides: object) -> str:
    now = int(time.time())
    claims = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": str(ALICE),
        "cid": "conv-1",
        "scope": "catalog:read basket:estimate",
        "iat": now,
        "exp": now + 60,
        "jti": uuid.uuid4().hex,
        **overrides,
    }
    return jwt.encode({k: v for k, v in claims.items() if v is not None}, SECRET, algorithm="HS256")


def test_a_fresh_gateway_token_names_the_customer() -> None:
    d = verify(mint(SECRET, ALICE, "conv-1"), SECRET, ReplayGuard())
    assert (d.customer_id, d.conversation_id) == (ALICE, "conv-1")


@pytest.mark.parametrize(
    "token",
    [
        pytest.param(raw(exp=int(time.time()) - 60), id="expired"),
        pytest.param(raw(aud="someone-else"), id="wrong audience"),
        pytest.param(raw(iss="a-browser"), id="wrong issuer"),
        pytest.param(raw(exp=int(time.time()) + 3600), id="lifetime over 5 minutes"),
        pytest.param(raw(scope="catalog:read"), id="missing scope"),
        pytest.param(raw(sub="alice@example.com"), id="subject not a customer id"),
        pytest.param(raw(jti=None), id="no jti"),
        pytest.param(
            jwt.encode(
                {"sub": str(ALICE)}, "wrong-secret-0123456789-0123456789", algorithm="HS256"
            ),
            id="forged",
        ),
        pytest.param("", id="missing"),
    ],
)
def test_bad_tokens_are_refused(token: str) -> None:
    with pytest.raises(DelegationError):
        verify(token, SECRET, ReplayGuard())


def test_a_token_works_once() -> None:
    guard = ReplayGuard()
    token = mint(SECRET, ALICE, "conv-1")
    verify(token, SECRET, guard)
    with pytest.raises(DelegationError, match="already used"):
        verify(token, SECRET, guard)
