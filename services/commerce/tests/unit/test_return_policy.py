"""The sandbox return policy's money and eligibility rules (PRODUCT_REQUIREMENTS.md)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from commerce.returns.policy import (
    SANDBOX_POLICY,
    LineFacts,
    Reason,
    RefundTiming,
    line_eligibility,
    refund_for,
    unit_refunds,
    whole_order_shipping_refund,
)

NOW = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)


def facts(**kw: object) -> LineFacts:
    base: dict[str, object] = {
        "policy_class": "standard",
        "quantity": 1,
        "unit_price_minor": 5000,
        "discount_minor": 0,
        "tax_minor": 0,
    }
    base.update(kw)
    return LineFacts(**base)  # type: ignore[arg-type]


def check(line: LineFacts, *, delivered_days_ago: float | None = 3, status: str = "delivered"):  # type: ignore[no-untyped-def]
    delivered = NOW - timedelta(days=delivered_days_ago) if delivered_days_ago is not None else None
    return line_eligibility(
        line, order_status=status, delivered_at=delivered, now=NOW, rules=SANDBOX_POLICY
    )


def test_discount_splits_333_333_334_and_the_last_unit_takes_the_remainder() -> None:
    tees = facts(quantity=3, unit_price_minor=2200, discount_minor=1000, tax_minor=0)
    assert unit_refunds(tees) == [2200 - 333, 2200 - 333, 2200 - 334]


def test_per_unit_refunds_add_up_to_exactly_the_line_total() -> None:
    line = facts(quantity=7, unit_price_minor=1999, discount_minor=1001, tax_minor=1103)
    assert sum(unit_refunds(line)) == 7 * 1999 - 1001 + 1103


def test_partial_returns_never_exceed_the_line_total() -> None:
    line = facts(quantity=3, unit_price_minor=2200, discount_minor=1000, tax_minor=463)
    first = refund_for(line, 1)
    rest = refund_for(facts(**{**line.__dict__, "returned_quantity": 1}), 2)
    assert first + rest == 3 * 2200 - 1000 + 463
    with pytest.raises(ValueError):
        refund_for(facts(**{**line.__dict__, "returned_quantity": 2}), 2)


def test_returnable_through_day_30_after_delivery() -> None:
    for days in (0, 29.9, 30.9):
        elig = check(facts(), delivered_days_ago=days)
        assert elig.eligible and elig.reason == Reason.WITHIN_WINDOW, days


def test_window_closes_when_day_31_starts() -> None:
    elig = check(facts(), delivered_days_ago=31)
    assert not elig.eligible and elig.reason == Reason.OUTSIDE_WINDOW
    assert elig.max_refund_minor == 0
    assert elig.window_ends_at is not None and elig.window_ends_at < NOW


@pytest.mark.parametrize(
    ("status", "delivered", "reason"),
    [
        ("fulfilling", None, Reason.NOT_DELIVERED),
        ("paid", None, Reason.NOT_DELIVERED),
        ("canceled", None, Reason.CANCELED),
    ],
)
def test_undelivered_and_canceled_orders_are_not_returnable(
    status: str, delivered: None, reason: Reason
) -> None:
    assert check(facts(), delivered_days_ago=delivered, status=status).reason == reason


def test_gift_cards_are_final_sale() -> None:
    elig = check(facts(policy_class="final_sale"), delivered_days_ago=1)
    assert not elig.eligible and elig.reason == Reason.FINAL_SALE


def test_electronics_need_inspection() -> None:
    elig = check(facts(policy_class="inspection", unit_price_minor=1500))
    assert elig.inspection_required
    # Under $25 but inspected: not an instant refund.
    assert elig.refund_timing == RefundTiming.AFTER_INSPECTION


def test_items_under_25_dollars_refund_at_the_scan_and_the_rest_on_receipt() -> None:
    assert check(facts(unit_price_minor=2499)).refund_timing == RefundTiming.INSTANT
    assert check(facts(unit_price_minor=2500)).refund_timing == RefundTiming.AFTER_RECEIPT


def test_perishables_have_a_7_day_window_and_no_return_shipment() -> None:
    fresh = check(facts(policy_class="perishable"), delivered_days_ago=2)
    assert fresh.reason == Reason.PERISHABLE_WITHIN_7_DAYS
    assert fresh.refund_timing == RefundTiming.NO_RETURN_NEEDED
    late = check(facts(policy_class="perishable"), delivered_days_ago=8)
    assert late.reason == Reason.PERISHABLE_PAST_7_DAYS


def test_already_returned_units_reduce_what_can_be_returned() -> None:
    line = facts(quantity=3, unit_price_minor=2200, discount_minor=1000, returned_quantity=1)
    elig = check(line)
    assert elig.returnable_quantity == 2
    assert elig.max_refund_minor == (2200 - 333) + (2200 - 334)
    assert check(facts(quantity=3, returned_quantity=3)).reason == Reason.FULLY_RETURNED


def test_shipping_is_refunded_only_when_the_whole_order_comes_back() -> None:
    a, b = facts(unit_price_minor=1200), facts(unit_price_minor=900)
    both = [(a, check(a)), (b, check(b))]
    assert whole_order_shipping_refund(both, 599, shipping_refunded=False) == 599
    assert whole_order_shipping_refund(both, 599, shipping_refunded=True) == 0

    gift = facts(policy_class="final_sale")
    with_final_sale = [(a, check(a)), (gift, check(gift))]
    assert whole_order_shipping_refund(with_final_sale, 599, shipping_refunded=False) == 0

    # One line already sent back earlier, the other returnable now: the whole order comes back.
    a_done = facts(unit_price_minor=1200, returned_quantity=1)
    assert whole_order_shipping_refund([(a_done, check(a_done)), (b, check(b))], 599, False) == 599
