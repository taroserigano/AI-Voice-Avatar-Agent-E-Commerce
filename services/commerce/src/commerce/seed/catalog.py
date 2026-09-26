"""The full seed catalog: the hand-written products plus the generated departments."""

from __future__ import annotations

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

_MODULES = (
    dairy, produce, meat, bakery, frozen, pantry, snacks, beverages, household, health, baby,
    pet, electronics, home, clothing, outdoor, sports, toys, beauty, office,
)  # fmt: skip

GENERATED_PRODUCTS: tuple[ProductSeed, ...] = tuple(p for m in _MODULES for p in m.products())
PRODUCTS: tuple[ProductSeed, ...] = HANDWRITTEN_PRODUCTS + GENERATED_PRODUCTS
