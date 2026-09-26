"""Earlier returns for the development orders built for them (see ``seed/orders.py``,
scenarios ``alice-partly-returned`` and ``alice-return-in-progress``), so "quantity already
returned" and "where's my refund?" have real answers.

Each spec finds its order line by customer, SKU, and quantity, so it attaches to those
scenario orders without depending on how they're created, and does nothing if they aren't
there. Refund amounts always come from ``commerce.returns.policy``, never from this file.
Development only; every row is labeled ``is_sample``. Safe to run repeatedly.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce.activity.models import CustomerEvent, EventType
from commerce.auth.models import User
from commerce.orders.models import Order, OrderLine, OrderStatus
from commerce.payments.models import PaymentAttempt, PaymentStatus
from commerce.returns.models import (
    RefundAttempt,
    RefundStatus,
    ReturnItem,
    ReturnRequest,
    ReturnStatus,
)
from commerce.returns.policy import LineFacts, refund_for

_NS = uuid.UUID("3f9b7c21-5e84-4a0d-8c6f-1a2b3c4d5e6f")


@dataclass(frozen=True)
class ReturnSpec:
    key: str  # the order scenario it belongs to
    email: str
    slug: str
    variant_code: str
    line_quantity: int  # to find the right line
    quantity: int  # units in this earlier return
    status: ReturnStatus
    refund: RefundStatus
    reason: str
    condition: str
    started_days_after_delivery: int
    note: str


RETURN_HISTORY: tuple[ReturnSpec, ...] = (
    ReturnSpec(
        key="alice-partly-returned",
        email="alice@example.com",
        slug="quillmark-laptop-backpack",
        variant_code="CHA",
        line_quantity=2,
        quantity=1,
        status=ReturnStatus.CLOSED,
        refund=RefundStatus.SUCCEEDED,
        reason="ordered_too_many",
        condition="unopened",
        started_days_after_delivery=2,
        note="Bought two by mistake; returned one unopened.",
    ),
    ReturnSpec(
        key="alice-return-in-progress",
        email="alice@example.com",
        slug="harbor-home-throw-blanket",
        variant_code="CRE",
        line_quantity=1,
        quantity=1,
        status=ReturnStatus.IN_TRANSIT,
        refund=RefundStatus.NOT_REQUESTED,
        reason="not_as_pictured",
        condition="like_new",
        started_days_after_delivery=4,
        note="The color is more yellow than the photos.",
    ),
)


def _id(*parts: object) -> uuid.UUID:
    return uuid.uuid5(_NS, ":".join(str(p) for p in parts))


def _find_line(db: Session, spec: ReturnSpec) -> tuple[Order, OrderLine] | None:
    from commerce.seed.run import make_sku  # run.py imports this module

    row = db.execute(
        select(Order, OrderLine)
        .join(OrderLine, OrderLine.order_id == Order.id)
        .join(User, User.id == Order.user_id)
        .where(
            User.email == spec.email,
            OrderLine.sku == make_sku(spec.slug, spec.variant_code),
            OrderLine.quantity == spec.line_quantity,
            Order.status == OrderStatus.DELIVERED,
        )
        .order_by(Order.placed_at.desc())
        .limit(1)
    ).first()
    return (row[0], row[1]) if row else None


def seed_return_history(db: Session) -> int:
    seeded = 0
    for spec in RETURN_HISTORY:
        found = _find_line(db, spec)
        if found is None:
            continue  # that scenario order isn't in this database
        order, line = found
        assert order.delivered_at is not None
        payment = db.scalar(select(PaymentAttempt).where(PaymentAttempt.order_id == order.id))
        if payment is None:
            continue  # history needs the order's payment (seed_order_history runs first)

        rid = _id("return", spec.key)
        facts = LineFacts(
            policy_class=line.policy_class,
            quantity=line.quantity,
            unit_price_minor=line.unit_price_minor,
            discount_minor=line.amount_discount_minor,
            tax_minor=line.amount_tax_minor,
        )
        refund_minor = refund_for(facts, spec.quantity)
        started = order.delivered_at + timedelta(days=spec.started_days_after_delivery)

        ret = db.get(ReturnRequest, rid)
        if ret is None:
            ret = ReturnRequest(
                id=rid,
                user_id=order.user_id,
                order_id=order.id,
                operation_key=f"seed:{spec.key}",
                rma_number=f"RMA-{rid.hex[:8].upper()}",
            )
            db.add(ret)
        ret.status = spec.status
        ret.policy_version = line.policy_version or "sandbox-2026-09"
        ret.reason, ret.note, ret.is_sample = spec.reason, spec.note, True
        ret.shipping_refund_minor = 0
        ret.created_at = started
        ret.authorized_at = started + timedelta(minutes=1)
        ret.return_tracking_number = f"LR{rid.int % 10**11:011d}"
        done = spec.status == ReturnStatus.CLOSED
        ret.received_at = started + timedelta(days=3) if done else None
        ret.inspected_at = started + timedelta(days=3, hours=20) if done else None
        ret.closed_at = started + timedelta(days=4) if done else None
        db.flush()

        item_id = _id("item", spec.key)
        item = db.get(ReturnItem, item_id)
        if item is None:
            item = ReturnItem(id=item_id, return_id=rid, order_line_id=line.id)
            db.add(item)
        item.quantity, item.refund_minor, item.condition = (
            spec.quantity,
            refund_minor,
            spec.condition,
        )

        refund_id = _id("refund", spec.key)
        refund = db.get(RefundAttempt, refund_id)
        if spec.refund == RefundStatus.NOT_REQUESTED:
            if refund is not None:
                db.delete(refund)
        else:
            if refund is None:
                refund = RefundAttempt(
                    id=refund_id,
                    return_id=rid,
                    payment_id=payment.id,
                    operation_id=f"refund:{rid}",
                )
                db.add(refund)
            refund.status, refund.amount_minor = spec.refund, refund_minor
            refund.provider_refund_id = f"sim_re_{refund_id.hex[:24]}"
            refund.requested_at = started + timedelta(days=3, hours=21)
            refund.settled_at = (
                refund.requested_at + timedelta(minutes=2)
                if spec.refund == RefundStatus.SUCCEEDED
                else None
            )

        # Keep the payment's refunded total consistent with its succeeded refunds.
        db.flush()
        refunded = sum(
            r.amount_minor
            for r in db.scalars(
                select(RefundAttempt).where(
                    RefundAttempt.payment_id == payment.id,
                    RefundAttempt.status == RefundStatus.SUCCEEDED,
                )
            )
        )
        payment.refunded_minor = refunded
        payment.status = (
            PaymentStatus.REFUNDED
            if refunded >= payment.amount_minor
            else PaymentStatus.PARTIALLY_REFUNDED
            if refunded
            else PaymentStatus.SUCCEEDED
        )

        for suffix, type_, at in (
            ("started", EventType.STARTED_RETURN, ret.authorized_at),
            ("refund", EventType.REFUND_ISSUED, refund.settled_at if refund else None),
        ):
            eid = _id("event", spec.key, suffix)
            existing = db.get(CustomerEvent, eid)
            if at is None:
                if existing is not None:
                    db.delete(existing)
                continue
            if existing is None:
                existing = CustomerEvent(id=eid, user_id=order.user_id, type=type_, is_sample=True)
                db.add(existing)
            existing.occurred_at, existing.order_id = at, order.id
            existing.data = {"rma_number": ret.rma_number, "refund_minor": refund_minor}
        seeded += 1
    db.flush()
    return seeded
