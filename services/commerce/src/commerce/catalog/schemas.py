from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field

from commerce.api_model import ApiModel
from commerce.catalog.models import PolicyClass


class CategoryOut(ApiModel):
    slug: str
    name: str
    policy_class: PolicyClass


class VariantOut(ApiModel):
    id: uuid.UUID
    sku: str
    name: str
    attributes: dict[str, Any]
    price_minor: int
    currency: str
    available: int = Field(description="Units available right now, from PostgreSQL")
    in_stock: bool


class TagOut(ApiModel):
    value: str = Field(description="Tag slug, usable in the tag / exclude_tag filters")
    label: str


class ProductSummary(ApiModel):
    id: uuid.UUID
    slug: str
    title: str
    brand: str
    category: CategoryOut
    product_type: str = Field(description='What a shopper would call it, e.g. "milk"')
    tags: list[TagOut]
    image_path: str
    price_minor: int = Field(description="Lowest current variant price")
    currency: str
    in_stock: bool
    variant_count: int


class Nutrition(ApiModel):
    """Per labeled serving, as on a US nutrition facts panel."""

    serving_size: str
    calories: int
    total_fat_g: float
    saturated_fat_g: float
    sodium_mg: int
    total_carbs_g: float
    fiber_g: float
    total_sugars_g: float
    added_sugars_g: float
    protein_g: float


class ProductDetail(ProductSummary):
    description: str
    nutrition: Nutrition | None = Field(default=None, description="Food only")
    ingredients: str | None = None
    allergens: list[str] = Field(description='Major food allergens, e.g. ["milk", "soy"]')
    specs: dict[str, str] = Field(description='Key facts, e.g. {"Milkfat": "0%"}')
    variants: list[VariantOut]
    as_of: datetime = Field(description="When price and stock were read from PostgreSQL")


class FacetValue(ApiModel):
    value: str
    label: str
    count: int


class Facets(ApiModel):
    categories: list[FacetValue]
    brands: list[FacetValue]
    product_types: list[FacetValue]
    tags: list[FacetValue]


class LegStatus(StrEnum):
    OK = "ok"
    UNAVAILABLE = "unavailable"  # configured but failed for this request
    DISABLED = "disabled"  # not configured (e.g. no PINECONE_API_KEY)


class SearchMeta(ApiModel):
    keyword: LegStatus
    semantic: LegStatus
    notice: str | None = Field(
        default=None, description="Shown to the shopper when search quality is reduced"
    )


class SortOrder(StrEnum):
    RELEVANCE = "relevance"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    NEWEST = "newest"


class ProductPage(ApiModel):
    items: list[ProductSummary]
    total: int
    page: int
    page_size: int
    facets: Facets
    search: SearchMeta | None = Field(default=None, description="Present when a text query was run")
