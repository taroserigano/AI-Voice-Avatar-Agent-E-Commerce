from __future__ import annotations

from collections import Counter

from commerce.catalog.models import PolicyClass
from commerce.seed.data import CATEGORIES, DEV_USERS, PRODUCTS
from commerce.seed.run import make_sku


def test_skus_and_slugs_are_unique() -> None:
    skus = [make_sku(p.slug, v.code) for p in PRODUCTS for v in p.variants]
    assert [s for s, n in Counter(skus).items() if n > 1] == []
    slugs = [p.slug for p in PRODUCTS]
    assert len(slugs) == len(set(slugs))


def test_every_product_has_a_known_category_and_positive_prices() -> None:
    known = {c.slug for c in CATEGORIES}
    for p in PRODUCTS:
        assert p.category in known, p.slug
        assert p.price_cents > 0
        assert all((v.price_cents or p.price_cents) > 0 for v in p.variants)


def test_catalog_covers_the_sandbox_policy_cases() -> None:
    by_class = {c.slug: c.policy_class for c in CATEGORIES}
    classes = {by_class[p.category] for p in PRODUCTS}
    assert {PolicyClass.STANDARD, PolicyClass.INSPECTION, PolicyClass.FINAL_SALE} <= classes
    # Two wireless audio products, so the assistant's "which headphones?" case is testable.
    audio = [p for p in PRODUCTS if "wireless" in p.title.lower() and p.category == "electronics"]
    assert len(audio) >= 2
    # An instant-refund candidate: standard category under $25.
    assert any(
        by_class[p.category] == PolicyClass.STANDARD and p.price_cents < 2500 for p in PRODUCTS
    )
    # Something out of stock, to exercise stock handling.
    assert any(v.stock == 0 for p in PRODUCTS for v in p.variants)


def test_dev_users_include_two_customers_and_one_staff() -> None:
    roles = Counter(u.role for u in DEV_USERS)
    assert roles["customer"] == 2 and roles["staff"] == 1
