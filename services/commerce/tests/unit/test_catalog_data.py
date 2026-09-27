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


def test_gift_cards_are_digital_final_sale_in_several_designs() -> None:
    cards = [p for p in PRODUCTS if p.category == "gift-cards"]
    assert len(cards) >= 4
    for p in cards:
        assert "final sale" in p.description.lower(), p.title
        assert p.specs["Returns"].lower().startswith("final sale"), p.title
        assert all(v.attributes.get("value") == v.name for v in p.variants), p.title
        assert all((v.price_cents or 0) == int(v.name.strip("$")) * 100 for v in p.variants)


# --- General merchandise specs ------------------------------------------------------------------

GENERAL_MERCHANDISE = [p for p in PRODUCTS if p.nutrition is None]


@pytest.mark.parametrize("p", GENERAL_MERCHANDISE, ids=_ids)
def test_general_merchandise_has_a_real_spec_table(p: ProductSeed) -> None:
    # Brand, type and department are shown anyway; these are the product's own facts.
    assert len(p.specs) >= 4, f"{p.title}: only {sorted(p.specs)}"
    assert all(k.strip() and str(v).strip() for k, v in p.specs.items())


# The single fact a spec row states, and the units it's stated in. When the title,
# description or option names give that fact in the same unit, the row must say the same
# number ("Capacity: 20,000 mAh" for "20,000 mAh portable charger"). A row may add detail
# ("8.5 W (60 W equivalent)") but not a different figure.
_UNITS = {
    "mAh": r"(\d[\d,]*)\s?mAh\b",
    "SPF": r"\bSPF\s?(\d+)",
    "oz": r"(\d+(?:\.\d+)?)\s?(?:fl\.? )?oz\b",
    "lumens": r"(\d[\d,]*)[- ]lumens?\b",
    "watts": r"(\d+(?:\.\d+)?)\s?W\b",
    "GB": r"(\d+)\s?GB\b",
    "mph": r"(\d+)\s?mph\b",
    "dB": r"(\d+)\s?dB\b",
    "°F": r"(\d+)°F",
}
_FACT_UNITS = {
    "Capacity": ("mAh", "oz"),
    "SPF": ("SPF",),
    "Brightness": ("lumens",),
    "Wattage": ("watts",),
    "Storage": ("GB",),
    "Top speed": ("mph",),
    "Volume limit": ("dB",),
    "Temperature rating": ("°F",),
    "Size": ("oz",),
}


def _numbers(pattern: str, text: str) -> set[str]:
    return {m.replace(",", "") for m in re.findall(pattern, text)}


@pytest.mark.parametrize("p", GENERAL_MERCHANDISE, ids=_ids)
def test_specs_dont_contradict_the_numbers_in_the_listing(p: ProductSeed) -> None:
    listing = " ".join([p.title, p.description, *(v.name for v in p.variants)])
    for key, units in _FACT_UNITS.items():
        value = p.specs.get(key)
        if not value:
            continue
        for unit in units:
            pattern = _UNITS[unit]
            said = _numbers(pattern, listing)
            stated = _numbers(pattern, f"SPF {value}" if key == "SPF" else value)
            if said and stated:
                assert stated & said, f"{p.title}: {key}={value!r}, listing says {sorted(said)}"


_UNSCENTED = {"unscented", "fragrance-free", "fragrance free", "none"}
# Words that name a scent or flavor anywhere in the catalog ("lavender", "mint", "cedar"),
# less the ones that also mean something else in a title.
_NOT_A_SCENT = {
    "and", "with", "free", "fresh", "clean", "original", "classic", "mild", "light", "sport",
    "sensitive", "fragrance", "unscented", "none", "scent", "lightly", "scented", "natural",
    "baby", "butter", "shea", "cocoa", "oatmeal", "honey", "breeze", "blossom", "tea", "green",
    "sea", "salt", "extra", "cool", "spring", "rain", "cotton", "cream", "oil",
}  # fmt: skip
_SCENT_WORDS = {
    w
    for p in PRODUCTS
    for k, v in p.specs.items()
    if k in {"Scent", "Flavor"}
    for w in re.findall(r"[a-z]{3,}", v.lower())
} - _NOT_A_SCENT


@pytest.mark.parametrize("p", GENERAL_MERCHANDISE, ids=_ids)
def test_scent_flavor_and_color_agree_with_the_listing(p: ProductSeed) -> None:
    specs = {k.lower(): v for k, v in p.specs.items()}
    scent = specs.get("scent", specs.get("fragrance", "")).lower()
    if "fragrance-free" in p.tags:
        assert scent in _UNSCENTED | {""}, f"{p.title}: fragrance free but scent {scent!r}"
    elif scent in {"fragrance-free", "fragrance free"}:
        pytest.fail(f"{p.title}: spec says fragrance free but the tag is missing")
    # A scent or flavor the title names ("Deodorant, Lavender") is the one the spec gives.
    stated = " ".join(specs.get(k, "") for k in ("scent", "scents", "flavor")).lower()
    if stated.strip():
        named = set(re.findall(r"[a-z]{3,}", p.title.lower())) & _SCENT_WORDS
        missing = {w for w in named if w not in stated}
        assert not missing, f"{p.title}: title says {sorted(missing)}, spec says {stated!r}"
    # A single color is the option's color; a list is exactly the options.
    colors = [str(v.attributes["color"]) for v in p.variants if "color" in v.attributes]
    if "color" in specs and colors:
        assert specs["color"] in colors, p.title
    if "colors available" in specs:
        assert specs["colors available"] == ", ".join(dict.fromkeys(colors)), p.title


def test_description_spec_notes_name_real_products() -> None:
    from commerce.seed.spec_notes import DESCRIPTION_SPECS

    assert set(DESCRIPTION_SPECS) <= {p.slug for p in PRODUCTS}


def test_the_20k_power_bank_and_spf_moisturizer_list_their_key_facts() -> None:
    by_slug = {p.slug: p for p in PRODUCTS}
    bank = by_slug["lumen-power-bank-20k"].specs
    assert bank["Capacity"] == "20,000 mAh"
    assert {"USB-C", "In the box", "Warranty"} <= bank.keys()
    cream = by_slug["verdant-botanicals-face-moisturizer"]
    assert cream.specs["SPF"].startswith("30")
    assert cream.specs["Key ingredients"] == "Hyaluronic acid"
    assert "fragrance-free" in cream.tags


# --- Tags agree with descriptions ---------------------------------------------------------------

# A description that says one of these (not "not X") must carry the tag, so the filter finds it.
_SAID_MEANS_TAGGED = {
    "fragrance-free": r"fragrance[- ]free",
    "sulfate-free": r"sulfate[- ]free",
    "bpa-free": r"\bbpa[- ]free",
    "hypoallergenic": r"hypoallergenic",
    "tear-free": r"tear[- ]free",
    "aluminum-free": r"aluminum[- ]free",
    "noise-cancelling": r"noise[- ]cancell?ing",
    "cruelty-free": r"cruelty[- ]free",
}
_NEGATED = re.compile(r"\b(not|isn't|no|never|without)\s+(\w+\s+)?$")
# "lid is BPA free", "case is ...": a part, not the whole product.
_PART = re.compile(r"\b(lid|straw|case)\b[^.]*$")


@pytest.mark.parametrize("p", PRODUCTS, ids=_ids)
def test_tags_agree_with_what_the_description_says(p: ProductSeed) -> None:
    text = f"{p.title}. {p.description}".lower()
    for tag, pattern in _SAID_MEANS_TAGGED.items():
        for m in re.finditer(pattern, text):
            before = text[max(0, m.start() - 20) : m.start()]
            if _NEGATED.search(before) or _PART.search(before):
                continue
            assert tag in p.tags, f"{p.title}: says {m[0]!r} but isn't tagged {tag}"
    if p.product_type in {"coffee", "tea"}:
        # The facts are for the brewed cup; "zero calorie" coffee grounds is an odd claim.
        assert "zero-calorie" not in p.tags, p.title
