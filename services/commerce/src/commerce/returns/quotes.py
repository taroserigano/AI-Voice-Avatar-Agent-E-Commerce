"""Return quotes and confirmation (PLAN Step 4, items 2-3).

- :func:`create_quote` prices the requested units with ``commerce.returns.policy`` from the
  amounts saved on the order, and fingerprints the exact terms (``quote_hash``).
- :func:`mint_token` gives the customer's own browser a single-use confirmation token, stored
  only as a hash bound to the customer and the quote hash.
- :func:`confirm` rechecks everything, recomputes the quote (refusing if any term changed), and
  creates exactly one return per quote, however many times it's called.

Refunds are simulated until Stripe checkout exists (Milestone 2): perishables are refunded at
confirmation, other items at the carrier scan, warehouse receipt, or inspection, driven by the
development-only :func:`advance`. The records and states are the ones Stripe will use.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from commerce.activity.models import EventType
from commerce.db import utcnow
from commerce.orders.models import Order, OrderLine
from commerce.outbox.service import emit
from commerce.payments.models import PaymentAttempt, PaymentProvider, PaymentStatus
from commerce.returns.models import (
    INACTIVE_RETURN_STATES,
    RefundAttempt,
    RefundStatus,
    ReturnItem,
    ReturnQuote,
    ReturnRequest,
    ReturnStatus,
)
from commerce.returns.policy import LineFacts, RefundTiming, line_eligibility, refund_for
from commerce.returns.quote_schemas import (
    PERISHABLE_REASONS,
    LineProblem,
    QuoteLineOut,
    QuoteRequest,
    ReturnQuoteOut,
)
from commerce.returns.service import (
    _payment,
    line_message,
    payment_method,
    policy_rules,
    returned_quantities,
)

QUOTE_VALID_MINUTES = 15
RETURN_CONFIRMED = "return.confirmed"


class QuoteError(Exception):
    def __init__(self, status: int, detail: str, problems: list[LineProblem] | None = None):
        super().__init__(detail)
        self.status = status
        self.detail = detail
        self.problems = problems or []


@dataclass(frozen=True)
class PricedLine:
    line: OrderLine
    quantity: int
    refund_minor: int
    unit_refunds: list[int]
    timing: RefundTiming
    message: str


def _shipping_already_refunded(db: Session, order_id: uuid.UUID) -> bool:
    return bool(
        db.scalar(
            select(ReturnRequest.id).where(
                ReturnRequest.order_id == order_id,
                ReturnRequest.shipping_refund_minor > 0,
                ReturnRequest.status.not_in(list(INACTIVE_RETURN_STATES)),
            )
        )
    )


def price_request(
    db: Session, order: Order, req: QuoteRequest, now: datetime
) -> tuple[list[PricedLine], int, str]:
    """Price the requested units, or raise with every line's problem. Returns the priced lines,
    the shipping refund, and the policy version."""
    by_id = {line.id: line for line in order.lines}
    requested: dict[uuid.UUID, int] = {}
    for item in req.lines:
        requested[item.order_line_id] = requested.get(item.order_line_id, 0) + item.quantity
    returned = returned_quantities(db, list(by_id))
    problems: list[LineProblem] = []
    priced: list[PricedLine] = []
    versions: set[str] = set()
    for line_id, quantity in requested.items():
        line = by_id.get(line_id)
        if line is None:
            problems.append(
                LineProblem(
                    order_line_id=line_id,
                    reason="not_in_order",
                    message="That item isn't part of this order.",
                )
            )
            continue
        rules = policy_rules(db, line.policy_version)
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
        if not elig.eligible:
            problems.append(
                LineProblem(
                    order_line_id=line_id,
                    reason=elig.reason.value,
                    message=line_message(elig, rules),
                )
            )
            continue
        if quantity > elig.returnable_quantity:
            problems.append(
                LineProblem(
                    order_line_id=line_id,
                    reason="quantity",
                    message=f"Only {elig.returnable_quantity} of this item can still be returned.",
                )
            )
            continue
        if line.policy_class == "perishable" and req.reason not in PERISHABLE_REASONS:
            problems.append(
                LineProblem(
                    order_line_id=line_id,
                    reason="perishable_reason",
                    message="Fresh and frozen food can be refunded only for a problem with the "
                    "food: damaged, spoiled, or past its date.",
                )
            )
            continue
        start = facts.returned_quantity
        units = [
            refund_for(LineFacts(**{**facts.__dict__, "returned_quantity": start + i}), 1)
            for i in range(quantity)
        ]
        assert elig.refund_timing is not None
        priced.append(
            PricedLine(
                line=line,
                quantity=quantity,
                refund_minor=sum(units),
                unit_refunds=units,
                timing=elig.refund_timing,
                message=line_message(elig, rules),
            )
        )
    if problems:
        raise QuoteError(422, "Some of these items can't be returned as asked.", problems)

    # Shipping comes back only when this return, plus earlier ones, covers every unit.
    shipping = 0
    if order.shipping_minor and not _shipping_already_refunded(db, order.id):
        covered = {p.line.id: p.quantity for p in priced}
        if all(returned.get(ln.id, 0) + covered.get(ln.id, 0) >= ln.quantity for ln in order.lines):
            shipping = order.shipping_minor
    return priced, shipping, ", ".join(sorted(versions))


def _terms(
    user_id: uuid.UUID,
    order_id: uuid.UUID,
    priced: list[PricedLine],
    shipping: int,
    version: str,
    payment_id: uuid.UUID | None,
    reason: str,
) -> dict[str, Any]:
    return {
        "user_id": str(user_id),
        "order_id": str(order_id),
        "policy_version": version,
        "reason": reason,
        "payment_id": str(payment_id) if payment_id else None,
        "shipping_refund_minor": shipping,
        "lines": sorted(
            (
                {
                    "order_line_id": str(p.line.id),
                    "quantity": p.quantity,
                    "refund_minor": p.refund_minor,
                    "refund_timing": p.timing.value,
                }
                for p in priced
            ),
            key=lambda d: d["order_line_id"],
        ),
    }


def quote_hash(terms: dict[str, Any]) -> str:
    canonical = json.dumps(terms, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def _own_order(db: Session, user_id: uuid.UUID, order_id: uuid.UUID) -> Order:
    order = db.scalar(
        select(Order)
        .options(selectinload(Order.lines))
        .where(Order.id == order_id, Order.user_id == user_id)
    )
    if order is None:
        raise QuoteError(404, "Order not found")
    return order


def create_quote(
    db: Session,
    user_id: uuid.UUID,
    req: QuoteRequest,
    *,
    created_via: str,
    now: datetime | None = None,
) -> ReturnQuote:
    now = now or utcnow()
    order = _own_order(db, user_id, req.order_id)
    priced, shipping, version = price_request(db, order, req, now)
    payment = _payment(db, order.id)
    terms = _terms(
        user_id, order.id, priced, shipping, version, payment.id if payment else None, req.reason
    )
    quote = ReturnQuote(
        id=uuid.uuid4(),
        user_id=user_id,
        order_id=order.id,
        lines=[
            {
                "order_line_id": str(p.line.id),
                "quantity": p.quantity,
                "refund_minor": p.refund_minor,
                "unit_refunds": p.unit_refunds,
                "refund_timing": p.timing.value,
                "timing_message": p.message,
                "policy_class": p.line.policy_class,
                "product_title": p.line.product_title,
                "variant_name": p.line.variant_name,
                "image_path": p.line.image_path,
            }
            for p in priced
        ],
        reason=req.reason,
        note=req.note,
        shipping_refund_minor=shipping,
        total_refund_minor=sum(p.refund_minor for p in priced) + shipping,
        currency=order.currency,
        policy_version=version,
        payment_id=payment.id if payment else None,
        quote_hash=quote_hash(terms),
        created_via=created_via,
        created_at=now,
        expires_at=now + timedelta(minutes=QUOTE_VALID_MINUTES),
    )
    db.add(quote)
    db.flush()
    return quote


def quote_status(quote: ReturnQuote, now: datetime | None = None) -> str:
    if quote.confirmed_at is not None:
        return "confirmed"
    return "expired" if (now or utcnow()) >= quote.expires_at else "open"


def quote_out(db: Session, quote: ReturnQuote, now: datetime | None = None) -> ReturnQuoteOut:
    payment = db.get(PaymentAttempt, quote.payment_id) if quote.payment_id else None
    lines = [
        QuoteLineOut(
            order_line_id=uuid.UUID(ln["order_line_id"]),
            product_title=ln["product_title"],
            variant_name=ln["variant_name"],
            image_path=ln["image_path"],
            policy_class=ln["policy_class"],
            quantity=ln["quantity"],
            refund_minor=ln["refund_minor"],
            refund_timing=RefundTiming(ln["refund_timing"]),
            timing_message=ln["timing_message"],
        )
        for ln in quote.lines
    ]
    return ReturnQuoteOut(
        id=quote.id,
        order_id=quote.order_id,
        status=quote_status(quote, now),
        lines=lines,
        reason=quote.reason,
        items_refund_minor=quote.total_refund_minor - quote.shipping_refund_minor,
        shipping_refund_minor=quote.shipping_refund_minor,
        total_refund_minor=quote.total_refund_minor,
        currency=quote.currency,
        refund_destination=payment_method(payment) if payment else None,
        policy_version=quote.policy_version,
        needs_shipping=any(ln.refund_timing != RefundTiming.NO_RETURN_NEEDED for ln in lines),
        expires_at=quote.expires_at,
        return_id=quote.return_id,
    )


def own_quote(
    db: Session, user_id: uuid.UUID, quote_id: uuid.UUID, *, lock: bool = False
) -> ReturnQuote:
    stmt = select(ReturnQuote).where(ReturnQuote.id == quote_id, ReturnQuote.user_id == user_id)
    if lock:
        stmt = stmt.with_for_update()
    quote = db.scalar(stmt)
    if quote is None:
        raise QuoteError(404, "Quote not found")
    return quote


def _token_digest(quote: ReturnQuote, token: str) -> str:
    material = f"{quote.id}:{quote.user_id}:{quote.quote_hash}:{token}"
    return hashlib.sha256(material.encode()).hexdigest()


def mint_token(
    db: Session, user_id: uuid.UUID, quote_id: uuid.UUID, now: datetime | None = None
) -> tuple[str, datetime]:
    """A fresh single-use token for the customer's browser. Minting again replaces the old one."""
    now = now or utcnow()
    quote = own_quote(db, user_id, quote_id, lock=True)
    status = quote_status(quote, now)
    if status == "confirmed":
        raise QuoteError(409, "This return is already confirmed.")
    if status == "expired":
        raise QuoteError(410, "This quote has expired. Please get a new one.")
    token = secrets.token_urlsafe(32)
    quote.token_hash = _token_digest(quote, token)
    quote.token_issued_at = now
    db.flush()
    return token, quote.expires_at


def _rma(return_id: uuid.UUID) -> str:
    return "R-" + return_id.hex[:8].upper()


def _refund(
    db: Session,
    ret: ReturnRequest,
    payment: PaymentAttempt | None,
    amount: int,
    stage: str,
    now: datetime,
) -> int:
    """Record one refund to the original payment. Simulated until Stripe is connected; the
    deterministic operation ID makes a repeat of the same stage a no-op."""
    if amount <= 0 or payment is None:
        return 0
    operation_id = f"refund:{ret.id}:{stage}"
    if db.scalar(select(RefundAttempt.id).where(RefundAttempt.operation_id == operation_id)):
        return 0
    amount = min(amount, payment.amount_minor - payment.refunded_minor)
    if amount <= 0:
        return 0
    db.add(
        RefundAttempt(
            return_id=ret.id,
            payment_id=payment.id,
            operation_id=operation_id,
            status=RefundStatus.SUCCEEDED,
            amount_minor=amount,
            currency=payment.currency,
            provider_refund_id=f"sim_re_{uuid.uuid4().hex[:16]}"
            if payment.provider == PaymentProvider.SIMULATED
            else None,
            requested_at=now,
            settled_at=now,
        )
    )
    payment.refunded_minor += amount
    payment.status = (
        PaymentStatus.REFUNDED
        if payment.refunded_minor >= payment.amount_minor
        else PaymentStatus.PARTIALLY_REFUNDED
    )
    return amount


def _record_activity(
    db: Session,
    user_id: uuid.UUID,
    order_id: uuid.UUID,
    type_: EventType,
    data: dict[str, Any],
    now: datetime,
) -> None:
    from commerce.activity.models import CustomerEvent

    db.add(
        CustomerEvent(user_id=user_id, type=type_, occurred_at=now, order_id=order_id, data=data)
    )


def confirm(
    db: Session,
    user_id: uuid.UUID,
    quote_id: uuid.UUID,
    token: str,
    idempotency_key: str,
    now: datetime | None = None,
) -> tuple[ReturnRequest, int, bool]:
    """Create the return for a quote. Returns (return, refunded now, created by this call).

    One return per quote: a repeat (double click, retry, dropped connection) gets the same
    return back. A wrong, reused, or stale token, an expired quote, or changed terms create
    nothing.
    """
    now = now or utcnow()
    quote = own_quote(db, user_id, quote_id, lock=True)
    if quote.return_id is not None:
        ret = db.get(ReturnRequest, quote.return_id)
        assert ret is not None
        return ret, 0, False
    if quote_status(quote, now) == "expired":
        raise QuoteError(410, "This quote has expired. Please get a new one.")
    if not quote.token_hash or not hmac.compare_digest(
        quote.token_hash, _token_digest(quote, token)
    ):
        raise QuoteError(403, "This confirmation isn't valid. Please confirm again.")

    order = _own_order(db, user_id, quote.order_id)
    req = QuoteRequest(
        order_id=order.id,
        lines=[
            {"order_line_id": ln["order_line_id"], "quantity": ln["quantity"]} for ln in quote.lines
        ],
        reason=quote.reason,
        note=quote.note,
    )
    try:
        priced, shipping, version = price_request(db, order, req, now)
    except QuoteError as exc:
        raise QuoteError(
            409, "Something about this order changed. Please get a new quote.", exc.problems
        ) from None
    payment = _payment(db, order.id)
    terms = _terms(
        user_id, order.id, priced, shipping, version, payment.id if payment else None, quote.reason
    )
    if quote_hash(terms) != quote.quote_hash:
        raise QuoteError(409, "The refund for this return changed. Please get a new quote.")

    return_id = uuid.uuid4()
    all_perishable = all(p.timing == RefundTiming.NO_RETURN_NEEDED for p in priced)
    ret = ReturnRequest(
        id=return_id,
        user_id=user_id,
        order_id=order.id,
        operation_key=f"quote:{quote.id}",
        rma_number=_rma(return_id),
        status=ReturnStatus.CLOSED if all_perishable else ReturnStatus.AUTHORIZED,
        policy_version=version,
        reason=quote.reason,
        note=quote.note,
        shipping_refund_minor=shipping,
        return_tracking_number=None if all_perishable else f"SIM{return_id.int % 10**12:012d}",
        authorized_at=now,
        closed_at=now if all_perishable else None,
    )
    db.add(ret)
    condition = (
        "damaged"
        if quote.reason in ("damaged", "defective", "spoiled_or_expired")
        else "as_received"
    )
    for p in priced:
        db.add(
            ReturnItem(
                return_id=return_id,
                order_line_id=p.line.id,
                quantity=p.quantity,
                refund_minor=p.refund_minor,
                condition=condition,
            )
        )
    db.flush()
    perishable_total = sum(
        p.refund_minor for p in priced if p.timing == RefundTiming.NO_RETURN_NEEDED
    )
    refunded = _refund(
        db, ret, payment, perishable_total + (shipping if all_perishable else 0), "confirm", now
    )
    quote.confirmed_at = now
    quote.token_hash = None  # single use
    quote.idempotency_key = idempotency_key[:120]
    quote.return_id = return_id
    emit(
        db, RETURN_CONFIRMED, str(return_id), {"quote_id": str(quote.id), "order_id": str(order.id)}
    )
    _record_activity(
        db,
        user_id,
        order.id,
        EventType.STARTED_RETURN,
        {"rma": ret.rma_number, "refund_minor": quote.total_refund_minor},
        now,
    )
    if refunded:
        _record_activity(
            db,
            user_id,
            order.id,
            EventType.REFUND_ISSUED,
            {"rma": ret.rma_number, "amount_minor": refunded},
            now,
        )
    db.flush()
    return ret, refunded, True


# --- Development only: move a return along its (simulated) journey -------------------------

# Each stage, in order, and the refund timing that becomes due when it happens.
STAGES: list[tuple[str, ReturnStatus, RefundTiming]] = [
    ("carrier_scan", ReturnStatus.IN_TRANSIT, RefundTiming.INSTANT),
    ("warehouse_receive", ReturnStatus.RECEIVED, RefundTiming.AFTER_RECEIPT),
    ("inspect_pass", ReturnStatus.INSPECTED, RefundTiming.AFTER_INSPECTION),
]
_STAGE_OF_STATUS = {ReturnStatus.IN_TRANSIT: 0, ReturnStatus.RECEIVED: 1, ReturnStatus.INSPECTED: 2}


def advance(
    db: Session, user_id: uuid.UUID, return_id: uuid.UUID, event: str, now: datetime | None = None
) -> ReturnRequest:
    """Simulate the carrier scan, warehouse receipt, or inspection (development only).

    A return only moves forward. Reaching a stage refunds everything due by then, one refund
    per stage (each with its own operation ID), so skipping ahead and repeating an event can't
    refund anything twice. Shipping comes back with the refund that completes the return.
    """
    now = now or utcnow()
    ret = db.scalar(
        select(ReturnRequest)
        .options(selectinload(ReturnRequest.items))
        .where(ReturnRequest.id == return_id, ReturnRequest.user_id == user_id)
        .with_for_update()
    )
    if ret is None:
        raise QuoteError(404, "Return not found")
    if ret.status in (ReturnStatus.CLOSED, ReturnStatus.REJECTED, ReturnStatus.CANCELED):
        return ret
    if event == "inspect_fail":
        ret.status = ReturnStatus.REJECTED
        ret.received_at = ret.received_at or now
        ret.inspected_at = now
        ret.closed_at = now
        return ret
    target = next(i for i, (name, _, _) in enumerate(STAGES) if name == event)
    current = _STAGE_OF_STATUS.get(ret.status, -1)
    if target <= current:
        return ret
    quote = db.scalar(select(ReturnQuote).where(ReturnQuote.return_id == ret.id))
    timing_of = {
        ln["order_line_id"]: RefundTiming(ln["refund_timing"])
        for ln in (quote.lines if quote else [])
    }
    payment = _payment(db, ret.order_id)
    outstanding = {
        i.order_line_id
        for i in ret.items
        if timing_of.get(str(i.order_line_id)) != RefundTiming.NO_RETURN_NEEDED
    }
    for index in range(current + 1, target + 1):
        name, status, timing = STAGES[index]
        due = [i for i in ret.items if timing_of.get(str(i.order_line_id)) == timing]
        outstanding -= {i.order_line_id for i in due}
        amount = sum(i.refund_minor for i in due)
        if not outstanding:
            amount += ret.shipping_refund_minor
        refunded = _refund(db, ret, payment, amount, name, now)
        if refunded:
            _record_activity(
                db,
                user_id,
                ret.order_id,
                EventType.REFUND_ISSUED,
                {"rma": ret.rma_number, "amount_minor": refunded},
                now,
            )
        ret.status = status
        if status == ReturnStatus.RECEIVED:
            ret.received_at = now
        if status == ReturnStatus.INSPECTED:
            ret.received_at = ret.received_at or now
            ret.inspected_at = now
        if not outstanding:
            ret.status = ReturnStatus.CLOSED
            ret.closed_at = now
            break
    db.flush()
    return ret


def reset_customer_returns(db: Session, user_id: uuid.UUID) -> int:
    """Development only: delete a customer's quote-made returns and put their payments' refunded
    totals back to what the remaining (seeded) refunds add up to."""
    made = list(
        db.scalars(
            select(ReturnRequest).where(
                ReturnRequest.user_id == user_id,
                ReturnRequest.is_sample.is_(False),
                ReturnRequest.operation_key.like("quote:%"),
            )
        )
    )
    order_ids = {r.order_id for r in made}
    for quote in db.scalars(select(ReturnQuote).where(ReturnQuote.user_id == user_id)):
        db.delete(quote)
    db.flush()
    for ret in made:
        db.delete(ret)
    db.flush()
    for payment in db.scalars(select(PaymentAttempt).where(PaymentAttempt.order_id.in_(order_ids))):
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
            PaymentStatus.SUCCEEDED
            if refunded == 0
            else PaymentStatus.REFUNDED
            if refunded >= payment.amount_minor
            else PaymentStatus.PARTIALLY_REFUNDED
        )
    db.flush()
    return len(made)
