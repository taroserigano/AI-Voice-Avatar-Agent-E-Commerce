"""The development accounts' order history: correct money, correct owners."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from commerce.seed.orders import DEV_ORDERS, order_id
from commerce.seed.run import seed_dev_orders


def test_scenario_orders_add_up_and_belong_to_the_right_customer(
    db: Session, alice: TestClient, bob: TestClient
) -> None:
    seed_dev_orders(db)
    db.commit()
    alice_orders = alice.get("/v1/orders").json()
    bob_orders = bob.get("/v1/orders").json()
    assert len(alice_orders) == sum(o.email == "alice@example.com" for o in DEV_ORDERS)
    assert len(bob_orders) == sum(o.email == "bob@example.com" for o in DEV_ORDERS)

    for summary in alice_orders:
        order = alice.get(f"/v1/orders/{summary['id']}").json()
        lines = order["lines"]
        assert order["subtotal_minor"] == sum(
            ln["unit_price_minor"] * ln["quantity"] for ln in lines
        )
        assert (
            order["total_minor"]
            == sum(ln["amount_total_minor"] for ln in lines) + order["shipping_minor"]
        )
        for ln in lines:
            assert ln["amount_total_minor"] == (
                ln["unit_price_minor"] * ln["quantity"]
                - ln["amount_discount_minor"]
                + ln["amount_tax_minor"]
            )

    # Alice can't open Bob's order, and doesn't learn that it exists.
    assert alice.get(f"/v1/orders/{order_id('bob-tablet')}").status_code == 404


def test_reseeding_keeps_ids_and_refreshes_dates(db: Session, alice: TestClient) -> None:
    seed_dev_orders(db)
    db.commit()
    first = alice.get(f"/v1/orders/{order_id('alice-headphones')}").json()
    seed_dev_orders(db)
    db.commit()
    second = alice.get(f"/v1/orders/{order_id('alice-headphones')}").json()
    assert first["id"] == second["id"]
    assert second["delivered_at"] >= first["delivered_at"]
    assert [ln["id"] for ln in first["lines"]] == [ln["id"] for ln in second["lines"]]


def test_apparel_line_keeps_its_discount_and_tax(db: Session, alice: TestClient) -> None:
    seed_dev_orders(db)
    db.commit()
    order = alice.get(f"/v1/orders/{order_id('alice-apparel')}").json()
    tees = next(ln for ln in order["lines"] if ln["quantity"] == 3)
    assert tees["unit_price_minor"] == 2200 and tees["amount_discount_minor"] == 1000
    # 8.25% of (3 x 22.00 - 10.00) = 4.62
    assert tees["amount_tax_minor"] == 462
