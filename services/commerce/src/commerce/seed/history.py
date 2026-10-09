"""Everything around the development orders that makes returns feel real: how each order was
paid, how it shipped (with tracking scans), what the shopper browsed and searched before
buying, and past support conversations.

Derived from whatever orders exist, so it works with any order seed. Development only, and
every row is labeled: payments use the ``simulated`` provider, carriers are fictional, and
activity and support rows carry ``is_sample``. IDs are stable (uuid5 of the order), and each
run updates rows in place, so dates follow the orders when their seed moves them.
"""

from __future__ import annotations

import hashlib
import random
import uuid
from datetime import datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from commerce.activity.models import CustomerEvent, EventType
from commerce.auth.models import Role, User
from commerce.catalog.models import Product, Variant
from commerce.config import REPO_ROOT
from commerce.db import utcnow
from commerce.orders.models import Order, OrderStatus
from commerce.payments.models import PaymentAttempt, PaymentProvider, PaymentStatus
from commerce.returns.models import PolicyVersion
from commerce.returns.policy import SANDBOX_POLICY
from commerce.shipping.models import Shipment, ShipmentEvent, ShipmentStatus
from commerce.support.models import CaseChannel, CaseStatus, SupportCase

_NS = uuid.UUID("8c4f2a6e-1d3b-4e57-9a0c-7b5e2f19d6a3")

# Simulated cards on file (brand and last four only; the numbers are Stripe's public test cards).
_CARDS = {
    "alice@example.com": ("visa", "4242"),
    "bob@example.com": ("mastercard", "4444"),
    "dana@example.com": ("amex", "0005"),
}
_OTHER_CARDS = (("visa", "1881"), ("amex", "0005"), ("discover", "1117"))

# Where each shopper's packages go (city only; no street addresses are stored).
_CITIES = {
    "alice@example.com": "Austin, TX",
    "bob@example.com": "Seattle, WA",
    "dana@example.com": "Dallas, TX",
}
_WAREHOUSE = "Serigan Mart Fulfillment Center, Fort Worth, TX"
_HUBS = {
    "Austin, TX": ("Dallas, TX", "Round Rock, TX"),
    "Seattle, WA": ("Denver, CO", "Kent, WA"),
    "Dallas, TX": ("Fort Worth, TX", "Irving, TX"),
}
_CARRIERS = (("Serigan Mart Ground", "Ground", "LG"), ("Swiftline Parcel", "2-Day", "SW"))

POLICY_SUMMARY = (
    "Return most items within 30 days of delivery for a refund to the original payment "
    "method. Gift cards are final sale. Electronics are refunded after inspection. Items "
    "under $25 that don't need inspection are refunded at the carrier scan. Fresh and frozen "
    "food isn't sent back: report a problem within 7 days. Shipping is refunded only when the "
    "whole order is returned. No restocking fee."
)


def _id(*parts: object) -> uuid.UUID:
    return uuid.uuid5(_NS, ":".join(str(p) for p in parts))


def _rng(*parts: object) -> random.Random:
    digest = hashlib.sha256(":".join(str(p) for p in parts).encode()).hexdigest()
    return random.Random(int(digest[:12], 16))  # noqa: S311 - picks demo data, not a secret


def _card(email: str) -> tuple[str, str]:
    return (
        _CARDS.get(email) or _OTHER_CARDS[int(hashlib.sha256(email.encode()).hexdigest(), 16) % 3]
    )


def _policy_text() -> str:
    """The published policy page if it's in the repo (content/policies), else the summary."""
    page = REPO_ROOT / "content" / "policies" / "returns-and-refunds.md"
    if page.is_file():
        text = page.read_text(encoding="utf-8")
        if f"version: {SANDBOX_POLICY.version}" in text:
            return text.split("---", 2)[-1].strip()
    return POLICY_SUMMARY


def seed_policy_versions(db: Session) -> None:
    """The return policy versions order lines refer to. Seeded in every environment."""
    row = db.scalar(select(PolicyVersion).where(PolicyVersion.version == SANDBOX_POLICY.version))
    if row is None:
        row = PolicyVersion(
            version=SANDBOX_POLICY.version,
            effective_at=datetime.fromisoformat("2026-09-26T00:00:00+00:00"),
        )
        db.add(row)
    row.rules = SANDBOX_POLICY.to_json()
    row.summary = _policy_text()
    db.flush()


def _upsert_payment(db: Session, order: Order, email: str) -> None:
    brand, last4 = _card(email)
    pid = _id("payment", order.id)
    payment = db.get(PaymentAttempt, pid)
    if payment is None:
        payment = PaymentAttempt(
            id=pid,
            order_id=order.id,
            provider=PaymentProvider.SIMULATED,
            provider_payment_id=f"sim_pi_{pid.hex[:24]}",
            refunded_minor=0,
        )
        db.add(payment)
    elif payment.provider != PaymentProvider.SIMULATED:
        return  # a real payment is never rewritten by the seed
    payment.amount_minor = order.total_minor
    payment.currency = order.currency
    payment.card_brand, payment.card_last4 = brand, last4
    payment.captured_at = order.placed_at + timedelta(seconds=40)
    if order.status == OrderStatus.CANCELED:
        # Canceled before it shipped: the charge was refunded in full.
        payment.status, payment.refunded_minor = PaymentStatus.REFUNDED, order.total_minor
    elif payment.refunded_minor == 0:
        payment.status = PaymentStatus.SUCCEEDED


Scan = tuple[datetime, ShipmentStatus, str, str | None]


def _is_digital(order: Order) -> bool:
    """Gift cards are emailed, so an all-gift-card order has no parcel."""
    return bool(order.lines) and all(line.policy_class == "final_sale" for line in order.lines)


def _tracking_events(
    order: Order, city: str, carrier: str, now: datetime
) -> tuple[ShipmentStatus, list[Scan]]:
    """A believable scan history, always in time order: label, pickup, hubs, out for
    delivery, delivered. Delivered orders spread the scans across the actual trip."""
    hub1, hub2 = _HUBS.get(city, ("Dallas, TX", city))
    start, end = order.placed_at, order.delivered_at
    if _is_digital(order):
        # Emailed a minute after checkout and in the inbox a minute later, even when the
        # order row says it was delivered the moment it was placed.
        sent = start + timedelta(minutes=1)
        events: list[Scan] = [(sent, ShipmentStatus.IN_TRANSIT, "Gift card email sent", None)]
        if end is not None:
            inbox = max(end, sent + timedelta(minutes=1))
            events.append((inbox, ShipmentStatus.DELIVERED, "Delivered to your inbox", None))
        return events[-1][1], events
    if end is None:
        # Still on its way: show what has happened so far and stop.
        steps: list[Scan] = [
            (
                start + timedelta(hours=2),
                ShipmentStatus.LABEL_CREATED,
                "Shipping label created",
                _WAREHOUSE,
            ),
            (
                start + timedelta(hours=9),
                ShipmentStatus.IN_TRANSIT,
                f"Picked up by {carrier}",
                _WAREHOUSE,
            ),
            (
                start + timedelta(hours=19),
                ShipmentStatus.IN_TRANSIT,
                "Arrived at sort facility",
                hub1,
            ),
        ]
        events = [e for e in steps if e[0] <= now] or steps[:1]
        return events[-1][1], events
    trip = end - start
    events = [
        (start + trip * f, st, text, where)
        for f, st, text, where in (
            (0.03, ShipmentStatus.LABEL_CREATED, "Shipping label created", _WAREHOUSE),
            (0.12, ShipmentStatus.IN_TRANSIT, f"Picked up by {carrier}", _WAREHOUSE),
            (0.40, ShipmentStatus.IN_TRANSIT, "Arrived at sort facility", hub1),
            (0.48, ShipmentStatus.IN_TRANSIT, "Departed sort facility", hub1),
            (0.78, ShipmentStatus.IN_TRANSIT, "Arrived at local delivery hub", hub2),
            (0.93, ShipmentStatus.OUT_FOR_DELIVERY, "Out for delivery", city),
            (1.0, ShipmentStatus.DELIVERED, "Delivered, left at front door", city),
        )
    ]
    return ShipmentStatus.DELIVERED, events


def _upsert_shipment(db: Session, order: Order, email: str, now: datetime) -> None:
    if order.status not in (OrderStatus.FULFILLING, OrderStatus.DELIVERED):
        db.execute(delete(Shipment).where(Shipment.id == _id("shipment", order.id)))
        return
    rng = _rng("shipment", order.id)
    carrier, service, prefix = (
        ("Serigan Mart E-Gift", "Email", "EG")
        if _is_digital(order)
        else _CARRIERS[rng.randrange(len(_CARRIERS))]
    )
    city = _CITIES.get(email, "Denver, CO")
    status, events = _tracking_events(order, city, carrier, now)
    sid = _id("shipment", order.id)
    shipment = db.get(Shipment, sid)
    if shipment is None:
        shipment = Shipment(
            id=sid,
            order_id=order.id,
            tracking_number=f"{prefix}{rng.randrange(10**11, 10**12)}",
        )
        db.add(shipment)
    shipment.carrier, shipment.service, shipment.status = carrier, service, status
    shipment.is_simulated = True
    shipment.shipped_at = next(
        (at for at, st, _, _ in events if st != ShipmentStatus.LABEL_CREATED), None
    )
    shipment.delivered_at = events[-1][0] if status == ShipmentStatus.DELIVERED else None
    shipment.estimated_delivery_at = order.delivered_at or order.placed_at + timedelta(days=4)
    db.flush()
    db.execute(delete(ShipmentEvent).where(ShipmentEvent.shipment_id == sid))
    for n, (at, st, text, where) in enumerate(events):
        db.add(
            ShipmentEvent(
                id=_id("scan", order.id, n),
                shipment_id=sid,
                occurred_at=at,
                status=st,
                description=text,
                location=where,
            )
        )


def _event(
    user: User,
    key: str,
    type: EventType,
    at: datetime,
    *,
    product_id: uuid.UUID | None = None,
    order_id: uuid.UUID | None = None,
    data: dict[str, object] | None = None,
) -> CustomerEvent:
    return CustomerEvent(
        id=_id("event", user.id, key),
        user_id=user.id,
        type=type,
        occurred_at=at,
        product_id=product_id,
        order_id=order_id,
        data=data or {},
        is_sample=True,
    )


def _search_phrase(title: str) -> str:
    """ "Arc Wireless Over-Ear Headphones" -> "wireless over-ear headphones"."""
    words = [w for w in title.lower().replace(",", "").split() if not any(c.isdigit() for c in w)]
    return " ".join(words[-3:]) if len(words) > 3 else " ".join(words)


def _activity(db: Session, user: User, orders: list[Order], now: datetime) -> list[CustomerEvent]:
    events: list[CustomerEvent] = []
    variant_product: dict[uuid.UUID, uuid.UUID] = {
        vid: pid for vid, pid in db.execute(select(Variant.id, Variant.product_id))
    }
    for order in orders:
        rng = _rng("activity", order.id)
        for n, line in enumerate(order.lines):
            product_id = variant_product.get(line.variant_id)
            looked = order.placed_at - timedelta(hours=rng.randint(6, 70))
            events.append(
                _event(
                    user,
                    f"{order.id}:{n}:search",
                    EventType.SEARCHED,
                    looked - timedelta(minutes=3),
                    data={
                        "query": _search_phrase(line.product_title),
                        "results": rng.randint(3, 14),
                    },
                )
            )
            events.append(
                _event(
                    user,
                    f"{order.id}:{n}:view",
                    EventType.VIEWED_PRODUCT,
                    looked,
                    product_id=product_id,
                )
            )
            events.append(
                _event(
                    user,
                    f"{order.id}:{n}:cart",
                    EventType.ADDED_TO_CART,
                    order.placed_at - timedelta(minutes=rng.randint(4, 40)),
                    product_id=product_id,
                    data={"variant_id": str(line.variant_id), "quantity": line.quantity},
                )
            )
        events.append(
            _event(
                user,
                f"{order.id}:placed",
                EventType.PLACED_ORDER,
                order.placed_at,
                order_id=order.id,
                data={"total_minor": order.total_minor},
            )
        )
        if order.delivered_at:
            events.append(
                _event(
                    user,
                    f"{order.id}:delivered",
                    EventType.ORDER_DELIVERED,
                    order.delivered_at,
                    order_id=order.id,
                )
            )
    # Some browsing that didn't end in a purchase, mostly recent ("recently viewed").
    rng = _rng("browse", user.id)
    products = list(
        db.scalars(select(Product.id).where(Product.is_active.is_(True)).order_by(Product.slug))
    )
    for n, product_id in enumerate(rng.sample(products, k=min(9, len(products)))):
        at = now - timedelta(
            days=rng.choice((0, 0, 1, 1, 2, 4, 6, 9, 13)), hours=rng.randint(0, 20)
        )
        events.append(
            _event(user, f"browse:{n}", EventType.VIEWED_PRODUCT, at, product_id=product_id)
        )
    for n, query in enumerate(
        rng.sample(
            [
                "rain jacket",
                "gift for a coffee lover",
                "desk lamp",
                "kids headphones",
                "yoga mat",
                "camping gear",
            ],
            k=3,
        )
    ):
        at = now - timedelta(days=rng.randint(0, 12), hours=rng.randint(0, 20))
        events.append(
            _event(
                user,
                f"search:{n}",
                EventType.SEARCHED,
                at,
                data={"query": query, "results": rng.randint(2, 12)},
            )
        )
    events.append(_event(user, "signin", EventType.SIGNED_IN, now - timedelta(days=1, hours=3)))
    return [e for e in events if e.occurred_at <= now]


def _support(user: User, orders: list[Order], now: datetime) -> list[SupportCase]:
    cases: list[SupportCase] = []
    tag = int(hashlib.sha256(user.email.encode()).hexdigest(), 16) % 9000 + 1000
    for order in orders:
        if order.status == OrderStatus.DELIVERED and any(
            line.policy_class == "final_sale" for line in order.lines
        ):
            opened = (order.delivered_at or order.placed_at) + timedelta(hours=20)
            cases.append(
                SupportCase(
                    id=_id("case", order.id, "gift"),
                    user_id=user.id,
                    order_id=order.id,
                    reference=f"CS-{tag}{len(cases)}",
                    subject="Can I return a gift card?",
                    summary="Asked to return a gift card bought by mistake. Explained that gift "
                    "cards are final sale under the return policy; no exception was made.",
                    channel=CaseChannel.CHAT,
                    status=CaseStatus.RESOLVED,
                    opened_at=opened,
                    resolved_at=opened + timedelta(minutes=12),
                    is_sample=True,
                )
            )
        if order.status == OrderStatus.FULFILLING:
            opened = order.placed_at + timedelta(hours=18)
            cases.append(
                SupportCase(
                    id=_id("case", order.id, "where"),
                    user_id=user.id,
                    order_id=order.id,
                    reference=f"CS-{tag}{len(cases)}",
                    subject="When will my order arrive?",
                    summary="Asked for a delivery estimate. Shared the tracking link and the "
                    "estimated delivery date; the customer will check back if it's late.",
                    channel=CaseChannel.VOICE,
                    status=CaseStatus.WAITING_ON_CUSTOMER,
                    opened_at=opened,
                    resolved_at=None,
                    is_sample=True,
                )
            )
    return [c for c in cases if c.opened_at <= now]


def seed_order_history(db: Session, now: datetime | None = None) -> dict[str, int]:
    now = now or utcnow()
    counts = {"payments": 0, "shipments": 0, "activity_events": 0, "support_cases": 0}
    customers = db.scalars(
        select(User).where(User.role == Role.CUSTOMER, User.email.like("%@example.com"))
    )
    for user in customers:
        orders = list(
            db.scalars(
                select(Order)
                .options(selectinload(Order.lines))
                .where(Order.user_id == user.id)
                .order_by(Order.placed_at)
            )
        )
        if not orders:
            continue
        for order in orders:
            _upsert_payment(db, order, user.email)
            _upsert_shipment(db, order, user.email, now)
            counts["payments"] += 1
            counts["shipments"] += order.status in (OrderStatus.FULFILLING, OrderStatus.DELIVERED)
        # Sample activity and cases are regenerated each run so their dates track the orders.
        db.execute(
            delete(CustomerEvent).where(
                CustomerEvent.user_id == user.id, CustomerEvent.is_sample.is_(True)
            )
        )
        db.execute(
            delete(SupportCase).where(
                SupportCase.user_id == user.id, SupportCase.is_sample.is_(True)
            )
        )
        db.flush()
        events = _activity(db, user, orders, now)
        cases = _support(user, orders, now)
        db.add_all(events)
        db.add_all(cases)
        for case in cases:
            db.add(
                _event(
                    user,
                    f"case:{case.id}",
                    EventType.CONTACTED_SUPPORT,
                    case.opened_at,
                    order_id=case.order_id,
                    data={"reference": case.reference},
                )
            )
        counts["activity_events"] += len(events) + len(cases)
        counts["support_cases"] += len(cases)
    db.flush()
    return counts
