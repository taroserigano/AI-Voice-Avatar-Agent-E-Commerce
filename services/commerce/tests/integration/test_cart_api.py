from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import Session

from commerce.catalog.models import Price

from .conftest import variant_id_for

pytestmark = pytest.mark.integration

HEADPHONES = ("sonora-arc-wireless-headphones", "MID")  # $129.99, 14 in stock
BOWLS = ("kettleworth-mixing-bowls", "STD")  # out of stock
CHAIR = ("summit-forge-camp-chair", "STD")  # 1 in stock


def test_add_update_and_remove_lines(alice: TestClient, db: Session) -> None:
    vid = variant_id_for(db, *HEADPHONES)

    cart = alice.put("/v1/cart/items", json={"variant_id": vid, "quantity": 2}).json()
    assert cart["item_count"] == 2
    assert cart["subtotal_minor"] == 2 * 12999
    version = cart["version"]

    cart = alice.put("/v1/cart/items", json={"variant_id": vid, "quantity": 3}).json()
    assert cart["items"][0]["quantity"] == 3
    assert cart["version"] > version

    cart = alice.put("/v1/cart/items", json={"variant_id": vid, "quantity": 0}).json()
    assert cart["items"] == [] and cart["subtotal_minor"] == 0


def test_cart_survives_a_new_session(app, db: Session) -> None:  # type: ignore[no-untyped-def]
    from .conftest import sign_in

    first = sign_in(TestClient(app), "alice@example.com")
    first.put("/v1/cart/items", json={"variant_id": variant_id_for(db, *HEADPHONES), "quantity": 1})
    first.post("/v1/auth/sign-out")

    second = sign_in(TestClient(app), "alice@example.com")
    assert second.get("/v1/cart").json()["item_count"] == 1


def test_cannot_add_more_than_in_stock_or_out_of_stock_items(
    alice: TestClient, db: Session
) -> None:
    oos = alice.put(
        "/v1/cart/items", json={"variant_id": variant_id_for(db, *BOWLS), "quantity": 1}
    )
    assert oos.status_code == 409

    too_many = alice.put(
        "/v1/cart/items", json={"variant_id": variant_id_for(db, *CHAIR), "quantity": 2}
    )
    assert too_many.status_code == 409
    assert "Only 1 left" in too_many.json()["detail"]


def test_client_cannot_set_the_price(alice: TestClient, db: Session) -> None:
    vid = variant_id_for(db, *HEADPHONES)
    resp = alice.put(
        "/v1/cart/items",
        json={"variant_id": vid, "quantity": 1, "unit_price_minor": 1, "subtotal_minor": 1},
    )
    assert resp.status_code == 200
    assert resp.json()["items"][0]["unit_price_minor"] == 12999


def test_cart_shows_the_current_price_after_a_price_change(alice: TestClient, db: Session) -> None:
    vid = variant_id_for(db, *HEADPHONES)
    alice.put("/v1/cart/items", json={"variant_id": vid, "quantity": 1})
    db.execute(update(Price).where(Price.variant_id == vid).values(amount_minor=9999))
    db.commit()
    assert alice.get("/v1/cart").json()["subtotal_minor"] == 9999


def test_shipping_is_charged_below_the_threshold_and_free_at_it(
    alice: TestClient, db: Session
) -> None:
    empty = alice.get("/v1/cart").json()
    assert empty["shipping_minor"] == 0 and empty["estimated_total_minor"] == 0

    vid = variant_id_for(db, *HEADPHONES)
    db.execute(update(Price).where(Price.variant_id == vid).values(amount_minor=3000))
    db.commit()
    cart = alice.put("/v1/cart/items", json={"variant_id": vid, "quantity": 1}).json()
    assert cart["shipping_minor"] == 599
    assert cart["free_shipping_remaining_minor"] == 500
    assert cart["estimated_total_minor"] == 3599

    db.execute(update(Price).where(Price.variant_id == vid).values(amount_minor=3500))
    db.commit()
    cart = alice.get("/v1/cart").json()
    assert cart["shipping_minor"] == 0 and cart["free_shipping_remaining_minor"] == 0
    assert cart["estimated_total_minor"] == 3500


def test_bob_cannot_see_or_touch_alices_cart(
    alice: TestClient, bob: TestClient, db: Session
) -> None:
    cart = alice.put(
        "/v1/cart/items", json={"variant_id": variant_id_for(db, *HEADPHONES), "quantity": 1}
    ).json()
    alice_item_id = cart["items"][0]["id"]

    assert bob.get("/v1/cart").json()["items"] == []
    assert bob.get("/v1/cart").json()["id"] != cart["id"]
    assert bob.delete(f"/v1/cart/items/{alice_item_id}").status_code == 404
    # Still there for Alice.
    assert alice.get("/v1/cart").json()["item_count"] == 1


def test_unknown_variant_is_404(alice: TestClient) -> None:
    resp = alice.put(
        "/v1/cart/items",
        json={"variant_id": "00000000-0000-0000-0000-000000000000", "quantity": 1},
    )
    assert resp.status_code == 404
