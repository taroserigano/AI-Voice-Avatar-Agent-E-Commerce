"""Order payments, tracking, return history, return options, and activity, end to end."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from commerce.activity.models import CustomerEvent
from commerce.auth.models import User
from commerce.catalog.models import Category, InventoryBalance, Price, Product, Variant
from commerce.db import utcnow
from commerce.orders.models import Order, OrderLine, OrderStatus
from commerce.seed.history import seed_order_history, seed_policy_versions
from commerce.seed.return_history import seed_return_history
from commerce.seed.run import make_sku

pytestmark = pytest.mark.integration


@dataclass(frozen=True)
class L:
    slug: str
    code: str
    qty: int = 1
    discount: int = 0
    tax_bps: int = 825  # 8.25%, like the dev order seed


def make_order(
    db: Session,
    email: str,
    lines: list[L],
    *,
    placed_days_ago: int,
    delivered_days_ago: int | None,
    status: OrderStatus = OrderStatus.DELIVERED,
    shipping: int = 0,
) -> str:
    """Build an order the way the dev seed does: saved unit price, discount, tax, policy."""
    user = db.scalar(select(User).where(User.email == email))
    assert user is not None
    now = utcnow()
    built = []
    for spec in lines:
        variant, product, category = db.execute(
            select(Variant, Product, Category)
            .join(Product, Product.id == Variant.product_id)
            .join(Category, Category.id == Product.category_id)
            .where(Variant.sku == make_sku(spec.slug, spec.code))
        ).one()
        unit = variant.price.amount_minor
        taxable = unit * spec.qty - spec.discount
        tax = (
            0
            if category.policy_class.value == "final_sale"
            else round(taxable * spec.tax_bps / 10000)
        )
        built.append(
            OrderLine(
                variant_id=variant.id,
                product_title=product.title,
                variant_name=variant.name,
                sku=variant.sku,
                image_path=product.image_path,
                policy_class=category.policy_class.value,
                policy_version="sandbox-2026-09",
                quantity=spec.qty,
                unit_price_minor=unit,
                amount_discount_minor=spec.discount,
                amount_tax_minor=tax,
                amount_total_minor=taxable + tax,
            )
        )
    subtotal = sum(line.unit_price_minor * line.quantity for line in built)
    order = Order(
        user_id=user.id,
        status=status,
        subtotal_minor=subtotal,
        discount_minor=sum(line.amount_discount_minor for line in built),
        tax_minor=sum(line.amount_tax_minor for line in built),
        shipping_minor=shipping,
        total_minor=sum(line.amount_total_minor for line in built) + shipping,
        placed_at=now - timedelta(days=placed_days_ago),
        delivered_at=now - timedelta(days=delivered_days_ago)
        if delivered_days_ago is not None
        else None,
        lines=built,
    )
    db.add(order)
    db.commit()
    return str(order.id)


def seed_history(db: Session) -> None:
    seed_policy_versions(db)
    seed_order_history(db)
    seed_return_history(db)
    db.commit()


def options(client: TestClient, order_id: str) -> dict[str, dict]:  # type: ignore[type-arg]
    resp = client.get(f"/v1/orders/{order_id}/return-options")
    assert resp.status_code == 200, resp.text
    return {line["product_title"]: line for line in resp.json()["lines"]}


def test_return_options_follow_the_sandbox_policy(alice: TestClient, db: Session) -> None:
    audio = make_order(
        db,
        "alice@example.com",
        [L("sonora-arc-wireless-headphones", "MID"), L("quillmark-gel-pens-12pk", "STD")],
        placed_days_ago=6,
        delivered_days_ago=3,
    )
    old = make_order(
        db,
        "alice@example.com",
        [L("kettleworth-gooseneck-kettle", "MAT")],
        placed_days_ago=48,
        delivered_days_ago=45,
    )
    gift = make_order(
        db,
        "alice@example.com",
        [L("larkspur-gift-card", "50")],
        placed_days_ago=6,
        delivered_days_ago=6,
    )
    moving = make_order(
        db,
        "alice@example.com",
        [L("tempo-yoga-mat", "PLU")],
        placed_days_ago=1,
        delivered_days_ago=None,
        status=OrderStatus.FULFILLING,
    )
    seed_history(db)

    lines = options(alice, audio)
    arc, pens = lines["Arc Wireless Over-Ear Headphones"], lines["Quick-Dry Gel Pens, 12-Pack"]
    assert (arc["eligible"], arc["reason"], arc["refund_timing"]) == (
        True,
        "within_window",
        "after_inspection",
    )
    assert arc["inspection_required"] is True
    assert (pens["refund_timing"], pens["max_refund_minor"]) == (
        "instant",
        1199 + round(1199 * 0.0825),
    )

    assert options(alice, old)["Gooseneck Electric Kettle"]["reason"] == "outside_window"
    assert options(alice, gift)["Larkspur Gift Card"]["reason"] == "final_sale"
    assert options(alice, moving)["Grip Yoga Mat, 6 mm"]["reason"] == "not_delivered"

    body = alice.get(f"/v1/orders/{audio}/return-options").json()
    assert body["policy_version"] == "sandbox-2026-09"
    assert body["refund_destination"] == {
        "provider": "simulated",
        "card_brand": "visa",
        "card_last4": "4242",
        "is_simulated": True,
    }


def test_earlier_returns_reduce_what_can_be_returned(alice: TestClient, db: Session) -> None:
    backpack = make_order(
        db,
        "alice@example.com",
        [L("quillmark-laptop-backpack", "CHA", qty=2)],
        placed_days_ago=18,
        delivered_days_ago=15,
    )
    blanket = make_order(
        db,
        "alice@example.com",
        [L("harbor-home-throw-blanket", "CRE")],
        placed_days_ago=12,
        delivered_days_ago=9,
    )
    seed_history(db)

    line = options(alice, backpack)["Commuter Laptop Backpack"]
    # $69.99 x 2 with $11.55 tax split [577, 578]: the first unit came back as 7576, so the
    # last one refunds 7577 and the line's refunds add up to exactly what was paid.
    assert (line["returned_quantity"], line["returnable_quantity"]) == (1, 1)
    assert (line["reason"], line["refund_timing"], line["max_refund_minor"]) == (
        "within_window",
        "after_receipt",
        7577,
    )

    detail = alice.get(f"/v1/orders/{backpack}").json()
    (earlier,) = detail["returns"]
    assert earlier["status"] == "closed" and earlier["is_sample"] is True
    assert earlier["items"][0]["refund_minor"] == 7576
    assert earlier["refund"]["status"] == "succeeded"
    assert detail["payment"]["status"] == "partially_refunded"
    assert detail["payment"]["refunded_minor"] == 7576

    in_progress = options(alice, blanket)["Chunky Knit Throw Blanket"]
    assert (in_progress["eligible"], in_progress["reason"]) == (False, "fully_returned")
    (active,) = alice.get(f"/v1/orders/{blanket}").json()["returns"]
    assert active["status"] == "in_transit" and active["refund"] is None


def test_shipping_comes_back_only_with_the_whole_order(alice: TestClient, db: Session) -> None:
    small = make_order(
        db,
        "alice@example.com",
        [L("pebble-pine-plush-otter", "STD"), L("quillmark-dotted-notebook", "FOR")],
        placed_days_ago=12,
        delivered_days_ago=10,
        shipping=599,
    )
    seed_history(db)
    assert (
        alice.get(f"/v1/orders/{small}/return-options").json()["whole_order_shipping_refund_minor"]
        == 599
    )


def test_order_detail_has_payment_and_tracking(alice: TestClient, db: Session) -> None:
    delivered = make_order(
        db,
        "alice@example.com",
        [L("summit-forge-camp-chair", "STD")],
        placed_days_ago=6,
        delivered_days_ago=2,
    )
    moving = make_order(
        db,
        "alice@example.com",
        [L("tempo-yoga-mat", "PLU")],
        placed_days_ago=1,
        delivered_days_ago=None,
        status=OrderStatus.FULFILLING,
    )
    seed_history(db)

    detail = alice.get(f"/v1/orders/{delivered}").json()
    assert detail["payment"]["card_last4"] == "4242" and detail["payment"]["is_simulated"] is True
    assert detail["payment"]["amount_minor"] == detail["total_minor"]
    (shipment,) = detail["shipments"]
    assert shipment["status"] == "delivered" and shipment["is_simulated"] is True
    events = shipment["events"]
    assert events[0]["status"] == "delivered" and events[-1]["status"] == "label_created"
    assert [e["occurred_at"] for e in events] == sorted(
        (e["occurred_at"] for e in events), reverse=True
    )

    (in_transit,) = alice.get(f"/v1/orders/{moving}").json()["shipments"]
    assert in_transit["status"] in {"label_created", "in_transit"}
    assert in_transit["delivered_at"] is None

    listing = alice.get("/v1/orders").json()
    assert {o["id"] for o in listing} == {delivered, moving}
    assert all(o["preview_images"] for o in listing)


def test_canceled_orders_show_a_full_refund(bob: TestClient, db: Session) -> None:
    canceled = make_order(
        db,
        "bob@example.com",
        [L("kettleworth-french-press", "STD")],
        placed_days_ago=5,
        delivered_days_ago=None,
        status=OrderStatus.CANCELED,
    )
    seed_history(db)
    detail = bob.get(f"/v1/orders/{canceled}").json()
    assert detail["payment"]["status"] == "refunded"
    assert detail["payment"]["refunded_minor"] == detail["total_minor"]
    assert detail["shipments"] == []
    assert options(bob, canceled)["Double-Wall French Press, 34 oz"]["reason"] == "canceled"


def test_other_shoppers_orders_stay_private(
    alice: TestClient, bob: TestClient, db: Session
) -> None:
    bobs = make_order(
        db,
        "bob@example.com",
        [L("sonora-arc-wireless-headphones", "MID")],
        placed_days_ago=7,
        delivered_days_ago=4,
    )
    seed_history(db)
    assert alice.get(f"/v1/orders/{bobs}/return-options").status_code == 404
    assert alice.get(f"/v1/orders/{bobs}").status_code == 404
    assert all(
        e["order_id"] != bobs for e in alice.get("/v1/activity", params={"limit": 100}).json()
    )


def test_history_seed_is_repeatable(db: Session) -> None:
    make_order(
        db,
        "alice@example.com",
        [L("quillmark-laptop-backpack", "CHA", qty=2)],
        placed_days_ago=18,
        delivered_days_ago=15,
    )
    seed_history(db)
    counts = {t: db.scalar(select(func.count()).select_from(t)) for t in (CustomerEvent.__table__,)}
    seed_history(db)
    assert counts == {t: db.scalar(select(func.count()).select_from(t)) for t in counts}
    assert seed_return_history(db) == 1  # updated in place, not duplicated


def test_activity_records_views_and_searches(
    alice: TestClient, bob: TestClient, db: Session
) -> None:
    product_id = str(db.scalar(select(Product.id).where(Product.slug == "summit-forge-headlamp")))
    detail = alice.get(f"/v1/products/{product_id}").json()
    alice.get(f"/v1/products/{product_id}")  # a second look within 30 minutes is the same visit
    alice.get("/v1/products", params={"q": "rain boots"})

    events = alice.get("/v1/activity").json()
    assert [e["type"] for e in events[:2]] == ["searched", "viewed_product"]
    assert events[0]["data"]["query"] == "rain boots"
    assert events[1]["product"]["title"] == "Trailbeam Rechargeable Headlamp"
    # the live price and stock, the same numbers the product page shows
    assert events[1]["product"]["price_minor"] == detail["default_price_minor"]
    assert events[1]["product"]["in_stock"] == detail["in_stock"]
    assert sum(e["type"] == "viewed_product" for e in events) == 1
    assert bob.get("/v1/activity").json() == []


def test_recently_viewed_price_skips_sold_out_options(alice: TestClient, db: Session) -> None:
    """The price follows the product cards: the cheapest option in stock, not a sold-out one."""
    product = db.scalar(select(Product).where(Product.slug == "sonora-arc-wireless-headphones"))
    assert product is not None
    options = sorted(
        (v for v in product.variants if v.is_active and v.price), key=lambda v: v.price.amount_minor
    )
    cheapest, *others = options
    assert others, "needs a product with more than one option"
    # make one option the cheapest by far, then sell it out
    db.execute(update(Price).where(Price.variant_id == cheapest.id).values(amount_minor=100))
    db.execute(
        update(InventoryBalance)
        .where(InventoryBalance.variant_id == cheapest.id)
        .values(on_hand=0, reserved=0)
    )
    db.commit()
    alice.get(f"/v1/products/{product.id}")
    viewed = next(e for e in alice.get("/v1/activity").json() if e["type"] == "viewed_product")
    in_stock = [v for v in others if sum(max(b.available, 0) for b in v.balances) > 0]
    assert in_stock
    assert viewed["product"]["price_minor"] == min(v.price.amount_minor for v in in_stock) > 100


def test_order_list_shows_return_and_delivery_hints(alice: TestClient, db: Session) -> None:
    open_window = make_order(
        db,
        "alice@example.com",
        [L("summit-forge-camp-chair", "STD")],
        placed_days_ago=6,
        delivered_days_ago=2,
    )
    closed = make_order(
        db,
        "alice@example.com",
        [L("kettleworth-gooseneck-kettle", "MAT")],
        placed_days_ago=48,
        delivered_days_ago=45,
    )
    moving = make_order(
        db,
        "alice@example.com",
        [L("tempo-yoga-mat", "PLU")],
        placed_days_ago=1,
        delivered_days_ago=None,
        status=OrderStatus.FULFILLING,
    )
    returning = make_order(
        db,
        "alice@example.com",
        [L("harbor-home-throw-blanket", "CRE")],
        placed_days_ago=12,
        delivered_days_ago=9,
    )
    seed_history(db)

    by_id = {o["id"]: o for o in alice.get("/v1/orders").json()}
    assert by_id[open_window]["return_window_ends_at"] is not None
    assert by_id[closed]["return_window_ends_at"] is None
    assert by_id[moving]["estimated_delivery_at"] is not None
    assert by_id[moving]["return_window_ends_at"] is None
    assert by_id[returning]["has_open_return"] is True
    assert by_id[open_window]["has_open_return"] is False


def test_tracking_scans_are_in_time_order_and_gift_cards_are_emailed(
    alice: TestClient, db: Session
) -> None:
    gift = make_order(
        db,
        "alice@example.com",
        [L("larkspur-gift-card", "50")],
        placed_days_ago=6,
        delivered_days_ago=6,
    )
    parcel = make_order(
        db,
        "alice@example.com",
        [L("summit-forge-camp-chair", "STD")],
        placed_days_ago=3,
        delivered_days_ago=1,
    )
    seed_history(db)

    (email,) = alice.get(f"/v1/orders/{gift}").json()["shipments"]
    assert email["service"] == "Email" and email["status"] == "delivered"
    assert [e["description"] for e in email["events"]] == [
        "Delivered to your inbox",
        "Gift card email sent",
    ]

    for order_id in (gift, parcel):
        (shipment,) = alice.get(f"/v1/orders/{order_id}").json()["shipments"]
        times = [e["occurred_at"] for e in reversed(shipment["events"])]
        assert times == sorted(times), order_id
        assert shipment["shipped_at"] is None or shipment["shipped_at"] <= shipment["delivered_at"]
