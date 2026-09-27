"""Read-side return logic: what each order line can return right now, and the order's
payment, tracking, and return history. Every number here comes from saved order data and
``commerce.returns.policy``; nothing is taken from the caller."""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from commerce.db import utcnow
from commerce.orders.models import Order, OrderLine
from commerce.payments.models import PaymentAttempt, PaymentProvider
from commerce.returns.models import (
    INACTIVE_RETURN_STATES,
    PolicyVersion,
    ReturnItem,
    ReturnRequest,
    ReturnStatus,
)
from commerce.returns.policy import (
    SANDBOX_POLICY,
    LineEligibility,
    LineFacts,
    PolicyRules,
    Reason,
    RefundTiming,
    line_eligibility,
    whole_order_shipping_refund,
)
from commerce.returns.schemas import (
    LineReturnOption,
    PaymentMethodOut,
    PaymentOut,
    RefundOut,
    ReturnItemOut,
    ReturnOptions,
    ReturnOut,
    ShipmentEventOut,
    ShipmentOut,
)
from commerce.shipping.models import Shipment


def policy_rules(db: Session, version: str | None) -> PolicyRules:
    """The rules an order line was sold under; the sandbox policy if none was recorded."""
    if version:
        row = db.scalar(select(PolicyVersion).where(PolicyVersion.version == version))
        if row is not None:
            return PolicyRules.from_json(row.rules)
    return SANDBOX_POLICY


def returned_quantities(db: Session, line_ids: Iterable[uuid.UUID]) -> dict[uuid.UUID, int]:
    ids = list(line_ids)
    if not ids:
        return {}
    rows = db.execute(
        select(ReturnItem.order_line_id, func.sum(ReturnItem.quantity))
        .join(ReturnRequest, ReturnRequest.id == ReturnItem.return_id)
        .where(
            ReturnItem.order_line_id.in_(ids),
            ReturnRequest.status.not_in(list(INACTIVE_RETURN_STATES)),
        )
        .group_by(ReturnItem.order_line_id)
    )
    return {line_id: int(qty) for line_id, qty in rows}


def line_message(elig: LineEligibility, rules: PolicyRules) -> str:
    if elig.eligible:
        return {
            RefundTiming.INSTANT: "Refunded to your original payment method as soon as the "
            "carrier or a Serigan Mart store scans your package.",
            RefundTiming.AFTER_RECEIPT: "Refunded to your original payment method once our "
            "warehouse receives and checks the item.",
            RefundTiming.AFTER_INSPECTION: "Refunded to your original payment method after our "
            "warehouse inspects it, usually 3-5 business days after it arrives.",
            RefundTiming.NO_RETURN_NEEDED: "Tell us what was wrong and we'll refund it to your "
            "original payment method. There's nothing to send back.",
        }[elig.refund_timing or RefundTiming.AFTER_RECEIPT]
    return {
        Reason.NOT_DELIVERED: "You can start a return once this order is delivered.",
        Reason.CANCELED: "This order was canceled, so there's nothing to return.",
        Reason.FINAL_SALE: "Final sale: this item can't be returned.",
        Reason.OUTSIDE_WINDOW: f"The {rules.window_days}-day return window for this item has "
        "closed.",
        Reason.PERISHABLE_PAST_7_DAYS: f"Fresh and frozen food can be refunded only within "
        f"{rules.perishable_window_days} days of delivery.",
        Reason.FULLY_RETURNED: "Everything from this line has already been returned.",
    }[elig.reason]


def _payment(db: Session, order_id: uuid.UUID) -> PaymentAttempt | None:
    return db.scalar(
        select(PaymentAttempt)
        .where(PaymentAttempt.order_id == order_id)
        .order_by(PaymentAttempt.created_at)
        .limit(1)
    )


def payment_method(payment: PaymentAttempt) -> PaymentMethodOut:
    return PaymentMethodOut(
        provider=payment.provider,
        card_brand=payment.card_brand,
        card_last4=payment.card_last4,
        is_simulated=payment.provider == PaymentProvider.SIMULATED,
    )


def payment_out(payment: PaymentAttempt) -> PaymentOut:
    return PaymentOut(
        **payment_method(payment).model_dump(),
        status=payment.status,
        amount_minor=payment.amount_minor,
        refunded_minor=payment.refunded_minor,
        currency=payment.currency,
        captured_at=payment.captured_at,
    )


def return_options(db: Session, order: Order, now: datetime | None = None) -> ReturnOptions:
    now = now or utcnow()
    returned = returned_quantities(db, [line.id for line in order.lines])
    shipping_refunded = bool(
        db.scalar(
            select(func.coalesce(func.sum(ReturnRequest.shipping_refund_minor), 0)).where(
                ReturnRequest.order_id == order.id,
                ReturnRequest.status.not_in(list(INACTIVE_RETURN_STATES)),
            )
        )
    )
    pairs: list[tuple[LineFacts, LineEligibility]] = []
    options: list[LineReturnOption] = []
    versions: set[str] = set()
    rules_by_version: dict[str | None, PolicyRules] = {}
    for line in order.lines:
        if line.policy_version not in rules_by_version:
            rules_by_version[line.policy_version] = policy_rules(db, line.policy_version)
        rules = rules_by_version[line.policy_version]
        versions.add(rules.version)
        facts = LineFacts(
            policy_class=line.policy_class,
            quantity=line.quantity,
            unit_price_minor=line.unit_price_minor,
            discount_minor=line.amount_discount_minor,
            tax_minor=line.amount_tax_minor,
            returned_quantity=returned.get(line.id, 0),
        )
        elig = line_eligibility(
            facts,
            order_status=order.status.value,
            delivered_at=order.delivered_at,
            now=now,
            rules=rules,
        )
        pairs.append((facts, elig))
        options.append(
            LineReturnOption(
                order_line_id=line.id,
                product_title=line.product_title,
                variant_name=line.variant_name,
                image_path=line.image_path,
                quantity=line.quantity,
                returned_quantity=facts.returned_quantity,
                returnable_quantity=elig.returnable_quantity,
                eligible=elig.eligible,
                reason=elig.reason,
                message=line_message(elig, rules),
                window_ends_at=elig.window_ends_at,
                inspection_required=elig.inspection_required,
                refund_timing=elig.refund_timing,
                max_refund_minor=elig.max_refund_minor,
                currency=order.currency,
            )
        )
    payment = _payment(db, order.id)
    return ReturnOptions(
        order_id=order.id,
        policy_version=", ".join(sorted(versions)) or SANDBOX_POLICY.version,
        refund_destination=payment_method(payment) if payment else None,
        lines=options,
        whole_order_shipping_refund_minor=whole_order_shipping_refund(
            pairs, order.shipping_minor, shipping_refunded
        ),
        as_of=now,
    )


def order_payment(db: Session, order_id: uuid.UUID) -> PaymentOut | None:
    payment = _payment(db, order_id)
    return payment_out(payment) if payment else None


def order_shipments(db: Session, order_id: uuid.UUID) -> list[ShipmentOut]:
    shipments = db.scalars(
        select(Shipment)
        .options(selectinload(Shipment.events))
        .where(Shipment.order_id == order_id)
        .order_by(Shipment.created_at)
    )
    return [
        ShipmentOut(
            id=s.id,
            carrier=s.carrier,
            service=s.service,
            tracking_number=s.tracking_number,
            status=s.status,
            shipped_at=s.shipped_at,
            estimated_delivery_at=s.estimated_delivery_at,
            delivered_at=s.delivered_at,
            is_simulated=s.is_simulated,
            events=[
                ShipmentEventOut(
                    occurred_at=e.occurred_at,
                    status=e.status,
                    description=e.description,
                    location=e.location,
                )
                for e in reversed(s.events)  # newest first, like a carrier's tracking page
            ],
        )
        for s in shipments
    ]


def order_returns(db: Session, order: Order) -> list[ReturnOut]:
    lines = {line.id: line for line in order.lines}
    returns = db.scalars(
        select(ReturnRequest)
        .options(selectinload(ReturnRequest.items), selectinload(ReturnRequest.refunds))
        .where(ReturnRequest.order_id == order.id)
        .order_by(ReturnRequest.created_at.desc())
    )
    out = []
    for r in returns:
        latest = r.refunds[-1] if r.refunds else None
        items = []
        for item in r.items:
            line: OrderLine | None = lines.get(item.order_line_id)
            if line is None:
                continue
            items.append(
                ReturnItemOut(
                    order_line_id=item.order_line_id,
                    product_title=line.product_title,
                    variant_name=line.variant_name,
                    image_path=line.image_path,
                    quantity=item.quantity,
                    refund_minor=item.refund_minor,
                    condition=item.condition,
                )
            )
        out.append(
            ReturnOut(
                id=r.id,
                order_id=r.order_id,
                rma_number=r.rma_number,
                status=r.status,
                reason=r.reason,
                created_at=r.created_at,
                closed_at=r.closed_at,
                shipping_refund_minor=r.shipping_refund_minor,
                items=items,
                refund=RefundOut(
                    status=latest.status,
                    amount_minor=latest.amount_minor,
                    currency=latest.currency,
                    requested_at=latest.requested_at,
                    settled_at=latest.settled_at,
                    failure_reason=latest.failure_reason,
                )
                if latest
                else None,
                is_sample=r.is_sample,
            )
        )
    return out


OPEN_RETURN_STATES = (
    ReturnStatus.REQUESTED,
    ReturnStatus.AUTHORIZED,
    ReturnStatus.IN_TRANSIT,
    ReturnStatus.RECEIVED,
    ReturnStatus.INSPECTED,
    ReturnStatus.REVIEW,
)


def orders_with_open_returns(db: Session, order_ids: list[uuid.UUID]) -> set[uuid.UUID]:
    if not order_ids:
        return set()
    return set(
        db.scalars(
            select(ReturnRequest.order_id)
            .where(
                ReturnRequest.order_id.in_(order_ids),
                ReturnRequest.status.in_(OPEN_RETURN_STATES),
            )
            .distinct()
        )
    )


def estimated_deliveries(db: Session, order_ids: list[uuid.UUID]) -> dict[uuid.UUID, datetime]:
    if not order_ids:
        return {}
    rows = db.execute(
        select(Shipment.order_id, func.max(Shipment.estimated_delivery_at))
        .where(Shipment.order_id.in_(order_ids), Shipment.delivered_at.is_(None))
        .group_by(Shipment.order_id)
    )
    return {order_id: at for order_id, at in rows if at is not None}


def return_window_ends_at(db: Session, order: Order, now: datetime) -> datetime | None:
    """The latest moment any line of the order can still be returned, if one can."""
    if order.delivered_at is None:
        return None
    ends = [
        line.window_ends_at
        for line in return_options(db, order, now).lines
        if line.eligible and line.window_ends_at is not None
    ]
    return max(ends) if ends else None
