"""The development accounts' order history: correct money, correct owners."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from commerce.orders.models import Order
from commerce.seed.orders import DEV_ORDERS, DEV_SHIP_TO, RETIRED_ORDER_KEYS, order_id
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
        assert order["subtotal_minor"] == sum(ln["amount_subtotal_minor"] for ln in lines)
        for ln in lines:
            assert ln["amount_subtotal_minor"] == ln["unit_price_minor"] * ln["quantity"]
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


def test_reseeding_removes_retired_scenario_orders(db: Session) -> None:
    seed_dev_orders(db)
    stale = db.get(Order, order_id(DEV_ORDERS[0].key))
    assert stale is not None
    # Pretend an older seed left an order under a retired key.
    db.add(
        Order(
            id=order_id(RETIRED_ORDER_KEYS[0]),
            user_id=stale.user_id,
            status=stale.status,
            currency="USD",
            subtotal_minor=0,
            total_minor=0,
            placed_at=stale.placed_at,
        )
    )
    db.commit()
    seed_dev_orders(db)
    db.commit()
    assert db.get(Order, order_id(RETIRED_ORDER_KEYS[0])) is None


def test_seeded_orders_ship_to_a_labeled_sample_address(db: Session, alice: TestClient) -> None:
    seed_dev_orders(db)
    db.commit()
    order = alice.get(f"/v1/orders/{order_id('alice-headphones')}").json()
    expected = DEV_SHIP_TO["alice@example.com"]
    assert order["shipping_address"] == {
        "name": expected.name,
        "line1": expected.line1,
        "line2": expected.line2,
        "city": expected.city,
        "state": expected.state,
        "postal_code": expected.postal_code,
        "country": "US",
        "is_sample": True,
    }
    # The order list carries item titles (for search), not the address.
    summary = next(o for o in alice.get("/v1/orders").json() if o["id"] == order["id"])
    assert "shipping_address" not in summary
    assert sorted(summary["item_titles"]) == sorted(ln["product_title"] for ln in order["lines"])


def test_bob_cannot_read_alices_shipping_address(
    db: Session, alice: TestClient, bob: TestClient
) -> None:
    seed_dev_orders(db)
    db.commit()
    alices_order = order_id("alice-headphones")
    street = DEV_SHIP_TO["alice@example.com"].line1
    assert street in alice.get(f"/v1/orders/{alices_order}").text

    for path in (f"/v1/orders/{alices_order}", f"/v1/orders/{alices_order}/return-options"):
        resp = bob.get(path)
        assert resp.status_code == 404
        assert street not in resp.text
    assert street not in bob.get("/v1/orders").text
    # Bob's own orders show his address, never Alice's.
    bobs = bob.get(f"/v1/orders/{order_id('bob-tablet')}").json()
    assert bobs["shipping_address"]["line1"] == DEV_SHIP_TO["bob@example.com"].line1


def test_reseeding_keeps_one_address_per_order(db: Session) -> None:
    seed_dev_orders(db)
    db.commit()
    seed_dev_orders(db)
    db.commit()
    order = db.get(Order, order_id("alice-headphones"))
    assert order is not None
    assert order.ship_to_line1 == DEV_SHIP_TO["alice@example.com"].line1
    assert order.ship_to_is_sample is True
