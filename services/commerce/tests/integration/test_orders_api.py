from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce.auth.models import User
from commerce.db import utcnow
from commerce.orders.models import Order, OrderLine, OrderStatus

from .conftest import variant_id_for

pytestmark = pytest.mark.integration


def _make_order(db: Session, email: str) -> str:
    """Orders come from verified payments in Milestone 2; insert one directly for now."""
    user = db.scalar(select(User).where(User.email == email))
    assert user is not None
    order = Order(
        user_id=user.id,
        status=OrderStatus.PAID,
        subtotal_minor=12999,
        total_minor=12999,
        placed_at=utcnow(),
        lines=[
            OrderLine(
                variant_id=variant_id_for(db, "sonora-arc-wireless-headphones", "MID"),
                product_title="Arc Wireless Over-Ear Headphones",
                variant_name="Midnight",
                sku="SON-ARC-WIR-HEA-MID",
                image_path="/images/products/sonora-arc-wireless-headphones.svg",
                policy_class="inspection",
                quantity=1,
                unit_price_minor=12999,
                amount_total_minor=12999,
            )
        ],
    )
    db.add(order)
    db.commit()
    return str(order.id)


def test_customer_sees_only_their_own_orders(
    alice: TestClient, bob: TestClient, db: Session
) -> None:
    alice_order = _make_order(db, "alice@example.com")

    assert [o["id"] for o in alice.get("/v1/orders").json()] == [alice_order]
    assert bob.get("/v1/orders").json() == []


def test_bob_gets_404_not_403_for_alices_order(
    alice: TestClient, bob: TestClient, db: Session
) -> None:
    alice_order = _make_order(db, "alice@example.com")

    assert alice.get(f"/v1/orders/{alice_order}").status_code == 200
    resp = bob.get(f"/v1/orders/{alice_order}")
    assert resp.status_code == 404
    assert "Arc" not in resp.text
