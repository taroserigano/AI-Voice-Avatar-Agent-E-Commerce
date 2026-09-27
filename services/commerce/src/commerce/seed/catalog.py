"""The full seed catalog: the hand-written products plus the generated departments.

General merchandise gets its spec table filled in from its own title, description, tags and
options (``commerce.seed.specs``) on the way out.
"""

from __future__ import annotations

from dataclasses import replace

from commerce.seed.data import HANDWRITTEN_PRODUCTS, ProductSeed
from commerce.seed.gen import (
    baby,
    bakery,
    beauty,
    beverages,
    clothing,
    dairy,
    electronics,
    frozen,
    health,
    home,
    household,
    meat,
    office,
    outdoor,
    pantry,
    pet,
    produce,
    snacks,
    sports,
    toys,
)
from commerce.seed.photos import PHOTOGRAPHED, photo_path
from commerce.seed.specs import with_specs

_MODULES = (
    dairy, produce, meat, bakery, frozen, pantry, snacks, beverages, household, health, baby,
    pet, electronics, home, clothing, outdoor, sports, toys, beauty, office,
)  # fmt: skip

GENERATED_PRODUCTS: tuple[ProductSeed, ...] = tuple(
    with_specs(p) for m in _MODULES for p in m.products()
)
PRODUCTS: tuple[ProductSeed, ...] = tuple(
    replace(p, image_path=photo_path(p.slug)) if p.slug in PHOTOGRAPHED else p
    for p in tuple(with_specs(p) for p in HANDWRITTEN_PRODUCTS) + GENERATED_PRODUCTS
)
