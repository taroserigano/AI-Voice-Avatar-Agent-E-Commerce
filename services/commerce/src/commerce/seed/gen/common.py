"""Shared helpers for the generated catalog.

Generation is deterministic: every random choice comes from ``rng(slug)``, seeded by the
product's own slug, so adding or reordering products never changes the others' stock or
SKUs. Brands are invented for this project.
"""

from __future__ import annotations

import hashlib
import random
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from commerce.seed.data import Nutrition, ProductSeed, VariantSeed

# Department code used as the SKU prefix.
DEPT_CODES: dict[str, str] = {
    "dairy-eggs": "DRY",
    "produce": "PRD",
    "meat-seafood": "MEA",
    "bakery": "BAK",
    "frozen": "FRZ",
    "pantry": "PAN",
    "snacks": "SNK",
    "beverages": "BEV",
    "household": "HHD",
    "health-wellness": "HLT",
    "baby": "BAB",
    "pet": "PET",
    "electronics": "ELE",
    "home-kitchen": "HOM",
    "clothing-shoes": "CLO",
    "outdoor": "OUT",
    "sports": "SPT",
    "toys": "TOY",
    "beauty": "BTY",
    "office": "OFF",
}

STORE_BRAND = "Larkspur Kitchen"  # the store's own grocery brand

# The nine major US food allergens, spelled the way ``allergens`` uses them.
ALLERGENS = ("milk", "egg", "fish", "shellfish", "tree nuts", "peanuts", "wheat", "soy", "sesame")

REFRIGERATED = "Keep refrigerated at or below 40°F."
FROZEN = "Keep frozen at 0°F or below."
PANTRY = "Store in a cool, dry place."


def rng(slug: str) -> random.Random:
    # Reproducible demo data, not security: the same slug must always give the same stock.
    return random.Random(f"larkspur:{slug}")  # noqa: S311


def slugify(*parts: str) -> str:
    text = "-".join(parts).lower().replace("%", "pct").replace("&", "and")
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def sku(category: str, slug: str, variant_code: str) -> str:
    """e.g. DRY-3F9A2C-GAL: department, a stable hash of the slug, the variant code."""
    digest = hashlib.sha1(slug.encode(), usedforsecurity=False).hexdigest()[:6].upper()
    return f"{DEPT_CODES[category]}-{digest}-{variant_code.upper()}"


def stock(r: random.Random) -> int:
    """Mostly in stock; about 1 in 20 variants is sold out so stock handling gets exercised."""
    return 0 if r.random() < 0.05 else r.randint(6, 120)


@dataclass(frozen=True)
class Size:
    """A purchasable size of one product."""

    code: str  # short, SKU-safe: "GAL", "HG", "32OZ"
    label: str  # shown to shoppers: "1 gallon"
    price_cents: int
    oz: float | None = None  # net contents in ounces, for unit prices


def variants(category: str, slug: str, sizes: Sequence[Size]) -> tuple[VariantSeed, ...]:
    r = rng(slug)
    out = []
    for s in sizes:
        attrs: dict[str, object] = {"size": s.label}
        if s.oz is not None:
            attrs["net_oz"] = s.oz
        out.append(
            VariantSeed(
                code=s.code,
                name=s.label,
                stock=stock(r),
                price_cents=s.price_cents,
                attributes=attrs,
                sku=sku(category, slug, s.code),
            )
        )
    return tuple(out)


def options(
    category: str, slug: str, names: Sequence[str], price_cents: int, attribute: str
) -> tuple[VariantSeed, ...]:
    """Same-price options such as colors or apparel sizes."""
    r = rng(slug)
    return tuple(
        VariantSeed(
            code=slugify(n).upper()[:12],
            name=n,
            stock=stock(r),
            price_cents=price_cents,
            attributes={attribute: n},
            sku=sku(category, slug, slugify(n).upper()[:12]),
        )
        for n in names
    )


def cents(dollars: float) -> int:
    """Round a dollar amount to a shelf price ending in 9 (e.g. 4.43 -> 449)."""
    whole = round(dollars * 100)
    return max(99, whole - whole % 10 + 9)


def nutrition_tags(n: Nutrition, claims: Iterable[str]) -> tuple[str, ...]:
    """The subset of ``claims`` that ``n`` actually supports (definitions in catalog/tags.py).

    Families pass only the claims a shopper would look for on that product, so apples don't
    all end up tagged "fat free".
    """
    rules = {
        "fat-free": n.total_fat_g < 0.5,
        "low-fat": 0.5 <= n.total_fat_g <= 3,
        "sugar-free": n.total_sugars_g < 0.5,
        "no-added-sugar": n.added_sugars_g == 0,
        "low-sugar": n.total_sugars_g <= 6,
        "zero-calorie": n.calories < 5,
        "high-protein": n.protein_g >= 10,
        "high-fiber": n.fiber_g >= 5,
        "keto": n.net_carbs_g <= 5,
        "low-sodium": n.sodium_mg <= 140,
    }
    return tuple(c for c in claims if rules[c])


def facts_sentence(n: Nutrition) -> str:
    def g(x: float) -> str:
        return f"{x:g} g"

    sugar = g(n.total_sugars_g)
    if n.total_sugars_g:
        sugar += f" ({g(n.added_sugars_g)} added)"
    return (
        f"Per {n.serving_size}: {n.calories} calories, {g(n.total_fat_g)} fat, "
        f"{g(n.protein_g)} protein, {sugar} sugar, {n.sodium_mg} mg sodium."
    )


def food(
    *,
    category: str,
    product_type: str,
    brand: str,
    title: str,
    sizes: Sequence[Size],
    nutrition: Nutrition,
    ingredients: str,
    allergens: Iterable[str] = (),
    tags: Iterable[str] = (),
    claims: Iterable[str] = (),
    specs: dict[str, str] | None = None,
    intro: str,
    storage: str,
    slug: str | None = None,
) -> ProductSeed:
    """A food product: title, facts, and tags that agree with each other.

    ``tags`` are asserted facts (organic, lactose-free, ...); ``claims`` are
    nutrition-based tags added only when ``nutrition`` supports them.
    """
    slug = slug or slugify(brand, title)
    all_tags = tuple(dict.fromkeys([*tags, *nutrition_tags(nutrition, claims)]))
    allergens = tuple(allergens)
    contains = f" Contains: {', '.join(allergens)}." if allergens else ""
    description = f"{intro} {facts_sentence(nutrition)}{contains} {storage}".strip()
    return ProductSeed(
        slug=slug,
        title=title,
        brand=brand,
        category=category,
        price_cents=min(s.price_cents for s in sizes),
        description=description,
        variants=variants(category, slug, sizes),
        product_type=product_type,
        tags=all_tags,
        nutrition=nutrition,
        ingredients=ingredients,
        allergens=allergens,
        specs={**(specs or {}), "Storage": storage},
        image_path=f"/images/types/{product_type}.svg",
    )


def item(
    *,
    category: str,
    product_type: str,
    brand: str,
    title: str,
    description: str,
    variants_: tuple[VariantSeed, ...] | None = None,
    sizes: Sequence[Size] = (),
    tags: Iterable[str] = (),
    specs: dict[str, str] | None = None,
    slug: str | None = None,
) -> ProductSeed:
    """A non-food product. Pass ``sizes`` (priced variants) or ready-made ``variants_``."""
    slug = slug or slugify(brand, title)
    built = variants_ if variants_ is not None else variants(category, slug, sizes)
    return ProductSeed(
        slug=slug,
        title=title,
        brand=brand,
        category=category,
        price_cents=min(v.price_cents or 0 for v in built),
        description=description,
        variants=built,
        product_type=product_type,
        tags=tuple(dict.fromkeys(tags)),
        specs=dict(specs or {}),
        image_path=f"/images/types/{product_type}.svg",
    )
