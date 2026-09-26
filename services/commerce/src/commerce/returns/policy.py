"""The sandbox return policy as plain code: who may return what, and for how much.

Pure functions only (no database), so every money rule is unit tested directly. The rules
come from PRODUCT_REQUIREMENTS.md ("Sandbox return policy"); a ``PolicyRules`` value is the
machine-readable form of one saved policy version. The model never decides any of this: the
assistant and the order page only display what these functions return.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime, timedelta

from commerce.money import split_evenly


@dataclass(frozen=True)
class PolicyRules:
    version: str
    window_days: int = 30
    # Fresh and frozen food isn't sent back; damage reported within this many days is refunded.
    perishable_window_days: int = 7
    # Items under this unit price that don't need inspection are refunded at the carrier scan.
    instant_refund_under_minor: int = 2500

    def to_json(self) -> dict[str, int | str]:
        return {
            "version": self.version,
            "window_days": self.window_days,
            "perishable_window_days": self.perishable_window_days,
            "instant_refund_under_minor": self.instant_refund_under_minor,
        }

    @classmethod
    def from_json(cls, data: dict[str, object]) -> PolicyRules:
        return cls(
            version=str(data["version"]),
            window_days=int(data.get("window_days", 30)),  # type: ignore[call-overload]
            perishable_window_days=int(data.get("perishable_window_days", 7)),  # type: ignore[call-overload]
            instant_refund_under_minor=int(data.get("instant_refund_under_minor", 2500)),  # type: ignore[call-overload]
        )


SANDBOX_POLICY = PolicyRules(version="sandbox-2026-09")


class Reason(enum.StrEnum):
    """Same codes as the assistant eval set (evals/assistant/returns.jsonl)."""

    WITHIN_WINDOW = "within_window"
    PERISHABLE_WITHIN_7_DAYS = "perishable_within_7_days"
    NOT_DELIVERED = "not_delivered"
    CANCELED = "canceled"
    FINAL_SALE = "final_sale"
    OUTSIDE_WINDOW = "outside_window"
    PERISHABLE_PAST_7_DAYS = "perishable_past_7_days"
    FULLY_RETURNED = "fully_returned"


class RefundTiming(enum.StrEnum):
    INSTANT = "instant"  # under $25, no inspection: refunded at the carrier or store scan
    AFTER_RECEIPT = "after_receipt"  # refunded once the warehouse receives and checks it
    AFTER_INSPECTION = "after_inspection"  # electronics: refunded after a full inspection
    NO_RETURN_NEEDED = "no_return_needed"  # perishables: refunded without sending it back


@dataclass(frozen=True)
class LineFacts:
    """What an order line saved at purchase time, plus what has been returned since."""

    policy_class: str  # "standard" | "inspection" | "final_sale" | "perishable"
    quantity: int
    unit_price_minor: int
    discount_minor: int  # the whole line's discount, as charged
    tax_minor: int  # the whole line's tax, as charged
    returned_quantity: int = 0  # units in returns that weren't rejected or canceled


@dataclass(frozen=True)
class LineEligibility:
    eligible: bool
    reason: Reason
    returnable_quantity: int
    window_ends_at: datetime | None
    inspection_required: bool
    refund_timing: RefundTiming | None
    # Refund if every remaining unit is returned now (never more than what's left of the line).
    max_refund_minor: int


def unit_refunds(line: LineFacts) -> list[int]:
    """What each unit of the line refunds, in order: saved price − discount share + tax share.

    Discount and tax are each split evenly across the units, with the last unit taking any
    remainder, so the shares always add up to exactly the line's saved total.
    """
    discounts = split_evenly(line.discount_minor, line.quantity)
    taxes = split_evenly(line.tax_minor, line.quantity)
    return [line.unit_price_minor - d + t for d, t in zip(discounts, taxes, strict=True)]


def refund_for(line: LineFacts, quantity: int) -> int:
    """Refund for returning ``quantity`` more units. Units are consumed in order, so the last
    unit ever returned is the one that carries the rounding remainder."""
    start = line.returned_quantity
    if quantity < 1 or start + quantity > line.quantity:
        raise ValueError("quantity is more than what's left to return on this line")
    return sum(unit_refunds(line)[start : start + quantity])


def line_eligibility(
    line: LineFacts,
    *,
    order_status: str,
    delivered_at: datetime | None,
    now: datetime,
    rules: PolicyRules,
) -> LineEligibility:
    inspection = line.policy_class == "inspection"
    perishable = line.policy_class == "perishable"
    remaining = max(line.quantity - line.returned_quantity, 0)
    window_days = rules.perishable_window_days if perishable else rules.window_days
    # Whole days: an item delivered 30 days and 23 hours ago is still on day 30, so the window
    # lasts until just before day 31 starts.
    window_ends_at = (
        delivered_at + timedelta(days=window_days + 1) - timedelta(microseconds=1)
        if delivered_at
        else None
    )

    def no(reason: Reason) -> LineEligibility:
        return LineEligibility(
            eligible=False,
            reason=reason,
            returnable_quantity=0,
            window_ends_at=window_ends_at,
            inspection_required=inspection,
            refund_timing=None,
            max_refund_minor=0,
        )

    if order_status == "canceled":
        return no(Reason.CANCELED)
    if line.policy_class == "final_sale":
        return no(Reason.FINAL_SALE)
    if delivered_at is None or order_status != "delivered":
        return no(Reason.NOT_DELIVERED)
    if remaining == 0:
        return no(Reason.FULLY_RETURNED)
    assert window_ends_at is not None
    if now > window_ends_at:
        return no(Reason.PERISHABLE_PAST_7_DAYS if perishable else Reason.OUTSIDE_WINDOW)

    if perishable:
        timing = RefundTiming.NO_RETURN_NEEDED
    elif inspection:
        timing = RefundTiming.AFTER_INSPECTION
    elif line.unit_price_minor < rules.instant_refund_under_minor:
        timing = RefundTiming.INSTANT
    else:
        timing = RefundTiming.AFTER_RECEIPT
    return LineEligibility(
        eligible=True,
        reason=Reason.PERISHABLE_WITHIN_7_DAYS if perishable else Reason.WITHIN_WINDOW,
        returnable_quantity=remaining,
        window_ends_at=window_ends_at,
        inspection_required=inspection,
        refund_timing=timing,
        max_refund_minor=refund_for(line, remaining),
    )


def whole_order_shipping_refund(
    lines: list[tuple[LineFacts, LineEligibility]], shipping_minor: int, shipping_refunded: bool
) -> int:
    """Shipping comes back only when the whole order is returned: every unit of every line
    either already returned or returnable right now, and shipping not refunded before."""
    if shipping_refunded or shipping_minor == 0 or not lines:
        return 0
    for facts, elig in lines:
        if facts.returned_quantity + elig.returnable_quantity < facts.quantity:
            return 0
    if all(elig.returnable_quantity == 0 for _, elig in lines):
        return 0  # nothing left to send back
    return shipping_minor
