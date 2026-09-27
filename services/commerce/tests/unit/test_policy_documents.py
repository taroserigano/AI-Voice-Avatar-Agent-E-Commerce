"""The policy documents must agree with the code that enforces them.

``content/policies/returns-and-refunds.md`` carries its numeric rules in front matter. They're
checked here against the category data, the shipping rule, and the reference return policy in
the assistant eval oracle, so a policy edit that the code doesn't match (or the reverse) fails.
"""

from __future__ import annotations

import json
import re
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from commerce.catalog.models import PolicyClass
from commerce.money import split_evenly
from commerce.policies.documents import POLICY_DIR, load_policies, load_policy, parse_policy
from commerce.seed.data import CATEGORIES
from commerce.seed.orders import FREE_SHIPPING_MINOR, POLICY_VERSION, SHIPPING_MINOR
from tests.unit import test_assistant_scenarios as oracle

RETURNS = load_policy("returns-and-refunds")
REGULATIONS = load_policy("returns-regulations")
EVALS = Path(__file__).resolve().parents[4] / "evals" / "assistant"


def test_rules_match_the_category_policy_classes() -> None:
    classes = RETURNS.rules["policy_classes"]
    by_class = {
        PolicyClass.FINAL_SALE: set(classes["final_sale"]),
        PolicyClass.INSPECTION: set(classes["inspection"]),
        PolicyClass.PERISHABLE: set(classes["perishable"]),
    }
    for cat in CATEGORIES:
        listed = [pc for pc, slugs in by_class.items() if cat.slug in slugs]
        expected = [] if cat.policy_class == PolicyClass.STANDARD else [cat.policy_class]
        assert listed == expected, f"{cat.slug} is {cat.policy_class} in the catalog"


def test_rules_match_shipping_and_version() -> None:
    assert RETURNS.rules["shipping_minor"] == SHIPPING_MINOR
    assert RETURNS.rules["free_shipping_at_minor"] == FREE_SHIPPING_MINOR
    assert RETURNS.version == POLICY_VERSION
    assert RETURNS.rules["restocking_fee_minor"] == 0
    assert RETURNS.rules["refund_destination"] == "original_payment_method"


def _redeliver(order: oracle.BuiltOrder, days: int) -> oracle.BuiltOrder:
    """A copy of a seeded order, delivered ``days`` days before the oracle's NOW."""
    return replace(order, delivered_at=oracle.NOW - timedelta(days=days))


@pytest.mark.parametrize(
    ("slug_order", "window_key"),
    [("alice-pens", "return_window_days"), ("alice-groceries-recent", "perishable_report_days")],
)
def test_windows_match_the_reference_policy(slug_order: str, window_key: str) -> None:
    order = oracle.ORDERS[slug_order]
    slug = order.lines[0].product.slug
    window = RETURNS.rules[window_key]
    last_day = oracle.expected_outcome(order.spec.email, _redeliver(order, window), [slug], 1)
    too_late = oracle.expected_outcome(order.spec.email, _redeliver(order, window + 1), [slug], 1)
    assert last_day["eligible"] is True
    assert too_late["eligible"] is False


def test_instant_refund_threshold_matches_the_reference_policy() -> None:
    threshold = RETURNS.rules["instant_refund_under_minor"]
    order = oracle.ORDERS["alice-pens"]
    line = order.lines[0]
    assert line.unit_price_minor < threshold
    outcome = oracle.expected_outcome(order.spec.email, order, [line.product.slug], 1)
    assert outcome["refund_timing"] == "instant"
    # The oracle's hard-coded threshold is the policy's.
    source = Path(oracle.__file__).read_text(encoding="utf-8")
    assert f"ln.unit_price_minor < {threshold}" in source
    assert f"days > {RETURNS.rules['return_window_days']}" in source
    assert f"days > {RETURNS.rules['perishable_report_days']}" in source


def test_worked_example_adds_up() -> None:
    """Section 7.6's numbers, recomputed with the same cent-splitting the engine uses."""
    disc, tax = split_evenly(1000, 3), split_evenly(289, 3)
    assert (disc, tax) == ([333, 333, 334], [96, 96, 97])
    units = [1500 - d + t for d, t in zip(disc, tax, strict=True)]
    notebook = 400 + 33
    assert units[0] == 1263 and units[1] + units[2] == 2526
    assert sum(units) + notebook == 4222
    assert round((4500 - 1000) * 0.0825) == 289
    body = RETURNS.section("rr-7-6").body
    for amount in ("$12.63", "$25.26", "$4.33", "$42.22", "$0.96, $0.96, $0.97"):
        assert amount in body


@pytest.mark.parametrize("doc", list(load_policies().values()), ids=lambda d: d.id)
def test_documents_are_well_formed(doc) -> None:  # type: ignore[no-untyped-def]
    assert doc.title and doc.version == POLICY_VERSION and doc.effective_date
    # An unquoted "a: b" in a YAML list becomes a mapping, not a sentence.
    assert all(isinstance(line, str) for line in doc.summary), f"{doc.id}: quote summary lines"
    ids = [s.section_id for s in doc.sections]
    assert len(ids) == len(set(ids)), f"{doc.id}: duplicate section IDs"
    if doc.section_prefix:
        assert all(i.startswith(f"{doc.section_prefix}-") for i in ids)


def _links(text: str) -> set[str]:
    return set(re.findall(r"/returns-policy#([a-z]{2}-[\d-]+)|\(#([a-z]{2}-[\d-]+)\)", text))


def test_every_internal_link_resolves() -> None:
    known = {s.section_id for d in (RETURNS, REGULATIONS) for s in d.sections}
    for doc in (RETURNS, REGULATIONS):
        text = (POLICY_DIR / f"{doc.id}.md").read_text(encoding="utf-8")
        for pair in _links(text):
            anchor = pair[0] or pair[1]
            assert anchor in known, f"{doc.id} links to missing section {anchor}"


def test_eval_citations_resolve() -> None:
    docs = load_policies()
    for name in ("product_qa.jsonl", "returns.jsonl"):
        for line in (EVALS / name).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            for turn in json.loads(line).get("turns", []):
                for cite in turn.get("expect", {}).get("cite", []):
                    doc_id, _, section = cite.partition("#")
                    assert doc_id in docs, f"{name}: unknown policy {doc_id}"
                    if section:
                        docs[doc_id].section(section)


def test_parser_numbers_sections() -> None:
    doc = parse_policy(
        "---\nid: x\ntitle: X\nversion: v\neffective_date: 2026-01-01\nsection_prefix: xx\n---\n"
        "# X\n\nIntro.\n\n## 1. First\n\nOne.\n\n### 1.2 Sub\n\nTwo.\n\n## 2. Second\n\nThree.\n"
    )
    assert doc.intro == "Intro."
    assert [(s.section_id, s.title, s.parent_title, s.body) for s in doc.sections] == [
        ("xx-1", "First", None, "One."),
        ("xx-1-2", "Sub", "First", "Two."),
        ("xx-2", "Second", None, "Three."),
    ]


def test_rules_match_the_returns_engine() -> None:
    """The engine that prices returns uses the same numbers the policy states."""
    from commerce.returns.policy import SANDBOX_POLICY
    from commerce.returns.quotes import QUOTE_VALID_MINUTES

    assert SANDBOX_POLICY.version == RETURNS.version
    assert SANDBOX_POLICY.window_days == RETURNS.rules["return_window_days"]
    assert SANDBOX_POLICY.perishable_window_days == RETURNS.rules["perishable_report_days"]
    assert SANDBOX_POLICY.instant_refund_under_minor == RETURNS.rules["instant_refund_under_minor"]
    assert RETURNS.rules["quote_valid_minutes"] == QUOTE_VALID_MINUTES


def test_cart_shipping_matches_the_policy() -> None:
    from commerce.config import Settings

    settings = Settings()
    assert settings.shipping_minor == RETURNS.rules["shipping_minor"]
    assert settings.free_shipping_at_minor == RETURNS.rules["free_shipping_at_minor"]
