"""The assistant service's identity: a service token plus the customer's ID, on a short list.

The assistant resolves the signed-in customer from their own session, then calls these routes
with ``Authorization: Bearer <token>`` and ``X-On-Behalf-Of``. It must reach exactly the
customer's own data, only on the allowed routes, and never act as the customer's browser.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce.auth.deps import ASSISTANT_ROUTES, Principal, require_browser_user
from commerce.auth.models import User
from commerce.config import get_settings
from commerce.main import PUBLIC_ROUTES
from tests.integration.conftest import variant_id_for
from tests.integration.test_orders_api import _make_order


def _user(db: Session, email: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    assert user is not None
    return user


def _as_assistant(app, user: User, token: str | None = None) -> TestClient:  # type: ignore[no-untyped-def]
    token = token or get_settings().assistant_service_token
    return TestClient(
        app, headers={"Authorization": f"Bearer {token}", "X-On-Behalf-Of": str(user.id)}
    )


def test_assistant_reads_only_the_customers_own_orders(app, db: Session, alice) -> None:  # type: ignore[no-untyped-def]
    _make_order(db, "alice@example.com")
    _make_order(db, "bob@example.com")
    as_bob = _as_assistant(app, _user(db, "bob@example.com"))
    alice_orders = alice.get("/v1/orders").json()
    bob_orders = as_bob.get("/v1/orders").json()
    assert bob_orders and alice_orders
    assert not {o["id"] for o in bob_orders} & {o["id"] for o in alice_orders}
    # Bob's assistant can't open Alice's order, and gets the same 404 as a missing one.
    assert as_bob.get(f"/v1/orders/{alice_orders[0]['id']}").status_code == 404


def test_assistant_can_add_to_the_customers_cart(app, db: Session) -> None:  # type: ignore[no-untyped-def]
    as_alice = _as_assistant(app, _user(db, "alice@example.com"))
    vid = variant_id_for(db, "sonora-arc-wireless-headphones", "MID")
    resp = as_alice.put("/v1/cart/items", json={"variant_id": vid, "quantity": 1})
    assert resp.status_code == 200, resp.text
    assert [i["variant_id"] for i in resp.json()["items"]] == [vid]


@pytest.mark.parametrize(
    ("method", "path"),
    [("GET", "/v1/auth/me"), ("POST", "/v1/auth/sign-out"), ("DELETE", "/v1/cart/items/x")],
)
def test_assistant_is_refused_outside_its_routes(app, db: Session, method: str, path: str) -> None:  # type: ignore[no-untyped-def]
    as_alice = _as_assistant(app, _user(db, "alice@example.com"))
    resp = as_alice.request(method, path)
    # sign-out is public (it just clears a cookie); everything else is a 401.
    assert resp.status_code in ((204,) if (method, path) in PUBLIC_ROUTES else (401, 422))
    if (method, path) not in PUBLIC_ROUTES:
        assert resp.status_code == 401


def test_wrong_token_or_missing_user_is_refused(app, db: Session) -> None:  # type: ignore[no-untyped-def]
    alice = _user(db, "alice@example.com")
    assert _as_assistant(app, alice, token="not-the-token").get("/v1/orders").status_code == 401
    no_user = TestClient(
        app, headers={"Authorization": f"Bearer {get_settings().assistant_service_token}"}
    )
    assert no_user.get("/v1/orders").status_code == 401
    bad_user = TestClient(
        app,
        headers={
            "Authorization": f"Bearer {get_settings().assistant_service_token}",
            "X-On-Behalf-Of": "00000000-0000-0000-0000-000000000000",
        },
    )
    assert bad_user.get("/v1/orders").status_code == 401


def test_browser_only_actions_refuse_the_assistant(db: Session) -> None:
    user = _user(db, "alice@example.com")
    with pytest.raises(HTTPException) as exc:
        require_browser_user(Principal(user=user, session_token=None, via_assistant=True))
    assert exc.value.status_code == 403
    assert require_browser_user(Principal(user=user, session_token="t")).id == user.id


def test_the_allowlist_has_no_money_or_auth_actions() -> None:
    for method, path in ASSISTANT_ROUTES:
        assert not path.startswith("/v1/auth"), path
        assert "confirm" not in path and "refund" not in path and "checkout" not in path, path
        # Writes: the customer's own cart, a quote (prices, changes nothing), a support case.
        assert method == "GET" or (method, path) in {
            ("PUT", "/v1/cart/items"),
            ("POST", "/v1/returns/quote"),
            ("POST", "/v1/support/cases"),
        }, (method, path)


def test_assistant_reads_the_catalog_vocabulary(app, db: Session) -> None:  # type: ignore[no-untyped-def]
    as_alice = _as_assistant(app, _user(db, "alice@example.com"))
    vocab = as_alice.get("/v1/catalog/vocabulary").json()
    types = {t["value"]: t["count"] for t in vocab["product_types"]}
    tags = {t["value"]: t["label"] for t in vocab["tags"]}
    assert types["milk"] > 5 and types["yogurt"] > 5
    assert tags["fat-free"] == "Fat free" and "sugar-free" in tags
