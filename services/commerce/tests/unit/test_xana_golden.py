"""Xana's golden sets (evals/xana/*.jsonl) must agree with the seed data and the policies.

The builder (evals/xana/build_golden.py) reads every expected fact from the seed data; this
test reads the written files back and checks them again, so a catalog, order, store, or policy
change that makes a golden answer wrong fails here instead of silently scoring Xana against it.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from commerce.seed.catalog import PRODUCTS
from commerce.seed.data import ProductSeed
from commerce.seed.orders import DEV_ORDERS
from commerce.seed.stores import STORES

from .test_assistant_scenarios import ORDERS, expected_outcome

ROOT = Path(__file__).resolve().parents[4]
CATALOG = {p.slug: p for p in PRODUCTS}
POLICIES = ROOT / "content" / "policies"


def _load(name: str) -> list[dict[str, Any]]:
    lines = (ROOT / "evals" / "xana" / name).read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


PRODUCT_CASES = _load("products.jsonl")
RETURN_CASES = _load("returns.jsonl")


def _min_price(p: ProductSeed) -> int:
    return min((v.price_cents or p.price_cents) for v in p.variants)


def _matches(p: ProductSeed, search: dict[str, Any], rc: dict[str, Any]) -> bool:
    return (
        (not search.get("product_type") or p.product_type in search["product_type"])
        and set(search.get("tags", [])) <= set(p.tags)
        and not (set(search.get("exclude_tags", [])) & set(p.tags))
        and ("max_price_minor" not in search or _min_price(p) <= search["max_price_minor"])
        and not (set(rc.get("allergens_none", [])) & set(p.allergens))
        and all(t.lower() in p.title.lower() for t in rc.get("title_contains", []))
        and all(p.specs.get(k) == v for k, v in rc.get("specs", {}).items())
        and ("variant_code" not in rc or any(v.code == rc["variant_code"] for v in p.variants))
    )


def _listing_text(p: ProductSeed) -> str:
    """Everything a listing says about a product, as the assistant's tools show it."""
    n = p.nutrition
    parts = [p.title, p.brand, p.description, p.ingredients or "", " ".join(p.allergens)]
    parts += [f"{k}: {v}" for k, v in p.specs.items()]
    parts += [
        f"{v.name} ${(v.price_cents or p.price_cents) / 100:,.2f} "
        + ("in stock" if v.stock > 0 else "out of stock")
        for v in p.variants
    ]
    if n:
        parts.append(
            f"{n.calories} calories {n.protein_g:g} g protein {n.total_fat_g:g} g fat "
            f"{n.sodium_mg} mg sodium {n.fiber_g:g} g fiber {n.total_sugars_g:g} g sugar "
            f"{n.added_sugars_g:g} g added sugar"
        )
    return "\n".join(parts)


def test_each_golden_set_has_200_unique_cases() -> None:
    for cases in (PRODUCT_CASES, RETURN_CASES):
        assert len(cases) == 200
        assert len({c["id"] for c in cases}) == 200


@pytest.mark.parametrize("case", PRODUCT_CASES, ids=lambda c: c["id"])
def test_product_case_agrees_with_the_catalog(case: dict[str, Any]) -> None:
    for t in case["turns"]:
        expect = t["expect"]
        if "search" in expect and expect["action"] == "search":
            found = [
                p for p in PRODUCTS
                if _matches(p, expect["search"], expect.get("result_constraints", {}))
            ]  # fmt: skip
            if expect.get("expect_empty"):
                assert found == [], f"{case['id']}: expected no match, found {found[0].title}"
            else:
                assert found, f"{case['id']}: nothing satisfies the expected filters"
        if "product" in expect:
            p = CATALOG[expect["product"]]
            assert expect["product_title"] == p.title
            if case["category"] not in ("allergy",):
                listing = _listing_text(p)
                for pattern in expect.get("mentions_re", []):
                    assert re.search(pattern, listing, re.IGNORECASE), (
                        f"{case['id']}: the listing for {p.title} doesn't support /{pattern}/"
                    )
            if case["category"] == "allergy":
                assert expect.get("no_safety_claim") is True
        if "winner" in expect:
            winner = CATALOG[expect["winner"]]
            assert expect["winner_title"] == winner.title
            listing = _listing_text(winner)
            assert any(re.search(pat, listing, re.IGNORECASE) for pat in expect["mentions_re"])


def _policy_sections() -> set[str]:
    sections: set[str] = set()
    for path in POLICIES.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        doc = re.search(r"^id:\s*(\S+)", text, re.MULTILINE).group(1)  # type: ignore[union-attr]
        m = re.search(r"^section_prefix:\s*(\S+)", text, re.MULTILINE)
        sections.add(doc)
        if m:
            for num in re.findall(r"^#{2,3} (\d+(?:\.\d+)?)\.? ", text, re.MULTILINE):
                sections.add(f"{doc}#{m.group(1)}-{num.replace('.', '-')}")
    return sections


SECTIONS = _policy_sections()


@pytest.mark.parametrize("case", RETURN_CASES, ids=lambda c: c["id"])
def test_return_case_agrees_with_orders_policy_and_stores(case: dict[str, Any]) -> None:
    for t in case["turns"]:
        expect = t["expect"]
        for cite in expect.get("cite_any", []) + expect.get("cite", []):
            assert cite in SECTIONS, f"{case['id']}: {cite} isn't a policy section"
        quote = expect.get("quote")
        if quote:
            order = ORDERS[case["order"]]
            titles = {ln.product.slug: ln.product.title for ln in order.lines}
            outcome = case["outcome"]
            returned = {"alice-partly-returned": {"quillmark-laptop-backpack": 1}}.get(
                case["order"]
            )
            if "quantities" in outcome:
                refund = sum(
                    expected_outcome(case["user"], order, [slug], qty)["refund_minor"]
                    for slug, qty in outcome["quantities"].items()
                )
            else:
                ref = expected_outcome(
                    case["user"], order, outcome["lines"], outcome["quantity"], returned
                )
                assert ref["eligible"], f"{case['id']}: the reference says {ref['reason']}"
                refund = ref["refund_minor"]
                assert quote["shipping_refunded"] == ref["shipping_refunded"]
            assert quote["refund_minor"] == refund, f"{case['id']}: refund should be {refund}"
            assert {ln["title"] for ln in quote["lines"]} <= set(titles.values())
    outcome = case.get("outcome")
    if outcome and not outcome["eligible"] and outcome["reason"] not in ("invalid_request",):
        order = ORDERS[case["order"]]
        returned = {
            "alice-return-in-progress": {"harbor-home-throw-blanket": 1},
            "alice-partly-returned": {"quillmark-laptop-backpack": 1},
        }.get(case["order"])
        ref = expected_outcome(case["user"], order, outcome["lines"], 1, returned)
        assert ref["reason"] == outcome["reason"], f"{case['id']}: reference says {ref['reason']}"


def test_store_answers_come_from_the_store_list() -> None:
    facts = "\n".join(
        f"{s.name} {s.address_line1} {s.city} {s.phone} "
        + " ".join(f"{d} {o}-{c}" for d, (o, c) in s.hours.items())
        for s in STORES
    )
    for case in RETURN_CASES:
        if case["category"] != "stores":
            continue
        for pattern in case["turns"][-1]["expect"]["mentions_re"]:
            if re.search(r"\d", pattern) and "AM" not in pattern and "PM" not in pattern:
                assert re.search(pattern, facts), (
                    f"{case['id']}: /{pattern}/ isn't in the store data"
                )


def test_every_order_scenario_is_used() -> None:
    used = {c["order"] for c in RETURN_CASES if "order" in c}
    assert {spec.key for spec in DEV_ORDERS} <= used
