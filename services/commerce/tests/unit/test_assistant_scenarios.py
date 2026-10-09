"""The assistant eval scripts (evals/assistant/*.jsonl) must agree with the seed data.

Each product question's expected filters must have answers in the catalog (or none, when the
script says so), and every return conversation's expected outcome is recomputed here from
the seeded order and the sandbox return policy. A hand-written refund amount that's off by
a cent fails this test instead of silently teaching the evals the wrong answer.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from commerce.catalog.models import PolicyClass
from commerce.money import split_evenly
from commerce.orders.models import OrderStatus
from commerce.seed.catalog import PRODUCTS
from commerce.seed.data import ProductSeed
from commerce.seed.orders import DEV_ORDERS, BuiltOrder, build_order
from commerce.seed.stores import STORES

EVALS = Path(__file__).resolve().parents[4] / "evals" / "assistant"
NOW = datetime(2026, 9, 26, 12, tzinfo=UTC)
CATALOG = {p.slug: p for p in PRODUCTS}
ORDERS = {spec.key: build_order(spec, CATALOG, NOW) for spec in DEV_ORDERS}


def _load(name: str) -> list[dict[str, Any]]:
    lines = (EVALS / name).read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


PRODUCT_QA = _load("product_qa.jsonl")
RETURNS = _load("returns.jsonl")


# --- Product questions ----------------------------------------------------------------------


def _matches(p: ProductSeed, search: dict[str, Any], rc: dict[str, Any]) -> bool:
    if search.get("product_type") and p.product_type not in search["product_type"]:
        return False
    if not set(search.get("tags", [])) <= set(p.tags):
        return False
    if set(search.get("exclude_tags", [])) & set(p.tags):
        return False
    if "max_price_minor" in search and p.price_cents > search["max_price_minor"]:
        return False
    if set(rc.get("allergens_none", [])) & set(p.allergens):
        return False
    if not all(t in p.title for t in rc.get("title_contains", [])):
        return False
    if any(p.specs.get(k) != v for k, v in rc.get("specs", {}).items()):
        return False
    return not ("variant_code" in rc and all(v.code != rc["variant_code"] for v in p.variants))


def _qa_turns() -> list[tuple[str, dict[str, Any]]]:
    return [(f"{s['id']}#{i}", t["expect"]) for s in PRODUCT_QA for i, t in enumerate(s["turns"])]


@pytest.mark.parametrize(("turn_id", "expect"), _qa_turns(), ids=[t for t, _ in _qa_turns()])
def test_product_question_has_the_expected_answers(turn_id: str, expect: dict[str, Any]) -> None:
    if "product" in expect:
        assert expect["product"] in CATALOG, f"{turn_id}: unknown product slug"
    if "search" not in expect:
        return
    search, rc = expect["search"], expect.get("result_constraints", {})
    hits = [p for p in PRODUCTS if _matches(p, search, rc)]
    if expect.get("expect_empty"):
        assert hits == [], f"{turn_id}: expected no exact match, found {[p.title for p in hits]}"
        return
    assert hits, f"{turn_id}: no product satisfies {search} {rc}"
    if search.get("exclude_tags"):
        # The exclusion must actually remove something, or the question tests nothing.
        without = dict(search, exclude_tags=[])
        assert len([p for p in PRODUCTS if _matches(p, without, rc)]) > len(hits), turn_id
    if expect.get("answer") == "max_protein":
        best = max(p.nutrition.protein_g for p in hits if p.nutrition)
        assert f"{best:g} g" in expect["mentions"], f"{turn_id}: most protein is {best:g} g"
    for name in expect.get("must_not_mention", []):
        assert not any(name == p.title for p in hits), f"{turn_id}: {name} is a correct answer"


# --- Return conversations -------------------------------------------------------------------


def _unit_refunds(order: BuiltOrder, slug: str) -> tuple[list[int], int]:
    line = next(ln for ln in order.lines if ln.product.slug == slug)
    disc = split_evenly(line.discount_minor, line.quantity)
    tax = split_evenly(line.tax_minor, line.quantity)
    return [
        line.unit_price_minor - d + t for d, t in zip(disc, tax, strict=True)
    ], line.unit_price_minor


def expected_outcome(
    user: str,
    order: BuiltOrder,
    slugs: list[str],
    quantity: int,
    returned: dict[str, int] | None = None,
) -> dict[str, Any]:
    """The sandbox return policy (PRODUCT_REQUIREMENTS.md, content/policies), as a reference.

    ``returned``: units of each line already returned (or on their way back) earlier.
    """
    returned = returned or {}
    if order.spec.email != user:
        return {"eligible": False, "reason": "not_owner", "refund_minor": 0}
    if order.spec.status == OrderStatus.CANCELED:
        return {"eligible": False, "reason": "canceled", "refund_minor": 0}
    if order.delivered_at is None:
        return {"eligible": False, "reason": "not_delivered", "refund_minor": 0}
    days = (NOW - order.delivered_at).days
    lines = [ln for ln in order.lines if ln.product.slug in slugs]
    if any(returned.get(ln.product.slug, 0) >= ln.quantity for ln in lines):
        return {"eligible": False, "reason": "fully_returned", "refund_minor": 0}
    classes = {ln.policy_class for ln in lines}
    if PolicyClass.FINAL_SALE in classes:
        return {"eligible": False, "reason": "final_sale", "refund_minor": 0}
    if classes == {PolicyClass.PERISHABLE}:
        if days > 7:
            return {"eligible": False, "reason": "perishable_past_7_days", "refund_minor": 0}
        reason, timing = "perishable_within_7_days", "no_return_needed"
    elif days > 30:
        return {"eligible": False, "reason": "outside_window", "refund_minor": 0}
    else:
        reason = "within_window"
        timings = set()
        for ln in lines:
            if ln.policy_class == PolicyClass.INSPECTION:
                timings.add("after_inspection")
            elif ln.unit_price_minor < 2500:
                timings.add("instant")
            else:
                timings.add("after_receipt")
        timing = timings.pop() if len(timings) == 1 else "after_receipt"
    # Units come back in order, so after earlier returns this request gets the later shares
    # (the last unit takes the leftover cent).
    refund = sum(
        sum(_unit_refunds(order, s)[0][returned.get(s, 0) : returned.get(s, 0) + quantity])
        for s in slugs
    )
    whole_order = {ln.product.slug for ln in order.lines} == set(slugs) and all(
        returned.get(ln.product.slug, 0) + quantity == ln.quantity for ln in lines
    )
    shipping_refunded = whole_order and order.shipping_minor > 0
    if shipping_refunded:
        refund += order.shipping_minor
    return {
        "eligible": True,
        "reason": reason,
        "refund_timing": timing,
        "refund_minor": refund,
        "shipping_refunded": shipping_refunded,
    }


@pytest.mark.parametrize("scenario", [s for s in RETURNS if "outcome" in s], ids=lambda s: s["id"])
def test_return_outcome_matches_the_policy(scenario: dict[str, Any]) -> None:
    order = ORDERS[scenario["order"]]
    outcome = scenario["outcome"]
    if outcome["reason"] == "invalid_request":
        assert outcome["eligible"] is False and outcome["refund_minor"] == 0
        return
    slugs = outcome.get("lines") or ([outcome["line"]] if "line" in outcome else [])
    for slug in slugs:
        assert slug in {ln.product.slug for ln in order.lines}, f"{slug} isn't in {order.spec.key}"
    returned = scenario.get("history", {}).get("returned_units", {})
    expected = expected_outcome(
        scenario["user"], order, slugs, outcome.get("quantity", 1), returned
    )
    for key, value in expected.items():
        assert outcome.get(key) == value, (
            f"{scenario['id']}: {key} should be {value!r}, not {outcome.get(key)!r}"
        )
    assert outcome["confirmation_required"] is expected["eligible"]


def test_every_order_scenario_is_used_by_a_conversation() -> None:
    # This file's conversations, or Xena's golden, support, and holdout sets (evals/xana).
    xana = [
        json.loads(line)
        for f in sorted((EVALS.parent / "xana").rglob("*.jsonl"))
        if "runs" not in f.parts
        for line in f.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    used = {s["order"] for s in [*RETURNS, *xana] if "order" in s}
    assert {spec.key for spec in DEV_ORDERS} <= used


def test_store_answers_match_the_store_data() -> None:
    plano = next(s for s in STORES if s.code == "PLN-LEGACY")
    assert plano.address_line1 == "5800 Legacy Dr" and "Return drop-off" in plano.services
    mckinney = next(s for s in STORES if s.code == "MCK-VIRGINIA")
    assert mckinney.hours["sun"][1] == "21:00"  # "9 PM" in pol-003
