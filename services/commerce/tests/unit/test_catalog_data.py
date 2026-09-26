"""The seed catalog is data the assistant will answer from, so it has to be right.

These check that tags mean what catalog/tags.py says they mean (a "fat free" product really
has under 0.5 g fat), that allergens agree with dietary claims, and that every product can
be found, priced, and pictured.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import pytest

from commerce.catalog.models import PolicyClass
from commerce.catalog.tags import TAGS
from commerce.seed.catalog import GENERATED_PRODUCTS, PRODUCTS
from commerce.seed.data import CATEGORIES, ProductSeed
from commerce.seed.gen.common import ALLERGENS
from commerce.seed.run import make_sku

PUBLIC = Path(__file__).resolve().parents[4] / "apps" / "web" / "public"
FOOD_CATEGORIES = {
    "dairy-eggs", "produce", "meat-seafood", "bakery", "frozen", "pantry", "snacks", "beverages",
}  # fmt: skip
# Grocery food, plus anything else with nutrition facts (supplements, baby food).
FOODS = [p for p in PRODUCTS if p.category in FOOD_CATEGORIES or p.nutrition is not None]


def _ids(p: ProductSeed) -> str:
    return p.slug


def test_catalog_is_large_and_covers_every_department() -> None:
    assert len(PRODUCTS) >= 1500
    per_category = Counter(p.category for p in PRODUCTS)
    for c in CATEGORIES:
        if c.slug != "gift-cards":
            assert per_category[c.slug] >= 20, f"{c.slug} has only {per_category[c.slug]}"


def test_slugs_and_skus_are_unique() -> None:
    slugs = Counter(p.slug for p in PRODUCTS)
    assert [s for s, n in slugs.items() if n > 1] == []
    skus = Counter(v.sku or make_sku(p.slug, v.code) for p in PRODUCTS for v in p.variants)
    assert [s for s, n in skus.items() if n > 1] == []


def test_titles_are_unique_within_a_brand() -> None:
    pairs = Counter((p.brand, p.title) for p in PRODUCTS)
    assert [k for k, n in pairs.items() if n > 1] == []


@pytest.mark.parametrize("p", PRODUCTS, ids=_ids)
def test_product_basics(p: ProductSeed) -> None:
    assert p.category in {c.slug for c in CATEGORIES}
    assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", p.product_type), p.product_type
    assert p.variants, "no variants"
    assert all((v.price_cents or p.price_cents) > 0 for v in p.variants)
    assert len({v.code for v in p.variants}) == len(p.variants), "duplicate variant codes"
    assert len(p.title) <= 200 and len(p.brand) <= 120 and len(p.slug) <= 160
    assert all(len(v.name) <= 120 for v in p.variants)
    assert len(p.description) >= 40, "description too thin to search or answer from"
    unknown = set(p.tags) - TAGS.keys()
    assert not unknown, f"tags not in the vocabulary: {unknown}"
    assert set(p.allergens) <= set(ALLERGENS)
    image = p.image_path or f"/images/products/{p.slug}.svg"
    assert (PUBLIC / image.lstrip("/")).is_file(), f"missing image {image}"


@pytest.mark.parametrize("p", FOODS, ids=_ids)
def test_food_has_facts_and_tags_match_them(p: ProductSeed) -> None:
    n = p.nutrition
    assert n is not None and p.ingredients, "food needs nutrition facts and ingredients"
    assert 0 <= n.saturated_fat_g <= n.total_fat_g
    assert 0 <= n.added_sugars_g <= n.total_sugars_g <= n.total_carbs_g + 0.5
    assert n.fiber_g <= n.total_carbs_g + 0.5
    tags = set(p.tags)
    rules = {
        "fat-free": n.total_fat_g < 0.5,
        "low-fat": n.total_fat_g <= 3,
        "sugar-free": n.total_sugars_g < 0.5,
        "no-added-sugar": n.added_sugars_g == 0,
        "unsweetened": n.added_sugars_g == 0,
        "low-sugar": n.total_sugars_g <= 6,
        "zero-calorie": n.calories < 5,
        "high-protein": n.protein_g >= 10,
        "high-fiber": n.fiber_g >= 5,
        "keto": n.net_carbs_g <= 5,
        "low-sodium": n.sodium_mg <= 140,
    }
    broken = [t for t, ok in rules.items() if t in tags and not ok]
    assert not broken, f"{p.title}: tags contradict nutrition facts: {broken}"
    if "whole-milk" in tags:
        assert not tags & {"fat-free", "low-fat", "reduced-fat"}, p.title
    if "fat-free" in tags:
        assert not tags & {"low-fat", "reduced-fat", "whole-milk"}, p.title


@pytest.mark.parametrize("p", PRODUCTS, ids=_ids)
def test_dietary_claims_agree_with_allergens_and_ingredients(p: ProductSeed) -> None:
    tags, allergens = set(p.tags), set(p.allergens)
    ingredients = (p.ingredients or "").lower()
    if tags & {"dairy-free", "vegan"}:
        assert "milk" not in allergens, p.title
    if "vegan" in tags:
        assert not allergens & {"egg", "fish", "shellfish"}, p.title
        assert "honey" not in ingredients and "gelatin" not in ingredients, p.title
    if "dairy-free" in tags:
        assert "lactase" not in ingredients, f"{p.title}: lactase only belongs in dairy"
    if "gluten-free" in tags:
        assert "wheat" not in allergens, p.title
    if "nut-free" in tags:
        assert not allergens & {"tree nuts", "peanuts"}, p.title
    if "unsweetened" in tags:
        for sweetener in ("cane sugar", "corn syrup", "honey", "sucralose", "stevia"):
            assert sweetener not in ingredients, f"{p.title} contains {sweetener}"
    if "organic" in tags and p.category in FOOD_CATEGORIES:
        assert "organic" in p.title.lower(), f"{p.title}: organic foods say so in the title"


def test_policy_cases_are_all_present() -> None:
    by_class = {c.slug: c.policy_class for c in CATEGORIES}
    classes = {by_class[p.category] for p in PRODUCTS}
    assert set(PolicyClass) <= classes
    # An instant-refund candidate: standard, under $25.
    assert any(
        by_class[p.category] == PolicyClass.STANDARD and p.price_cents < 2500 for p in PRODUCTS
    )
    assert any(v.stock == 0 for p in PRODUCTS for v in p.variants)


def test_generated_products_use_type_images_and_explicit_skus() -> None:
    for p in GENERATED_PRODUCTS:
        assert p.image_path == f"/images/types/{p.product_type}.svg"
        assert all(v.sku for v in p.variants)
