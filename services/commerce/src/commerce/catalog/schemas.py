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


class ProductSummary(ApiModel):
    id: uuid.UUID
    slug: str
    title: str
    brand: str
    category: CategoryOut
    image_path: str
    price_minor: int = Field(description="Lowest current variant price")
    currency: str
    in_stock: bool
    variant_count: int
    rating_average: float | None = Field(
        description="Mean review rating to one decimal; null with no reviews"
    )
    rating_count: int


class ProductDetail(ProductSummary):
    description: str
    variants: list[VariantOut]
    as_of: datetime = Field(description="When price and stock were read from PostgreSQL")


class FacetValue(ApiModel):
    value: str
    label: str
    count: int


class Facets(ApiModel):
    categories: list[FacetValue]
    brands: list[FacetValue]


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
    TOP_RATED = "top_rated"


class ProductPage(ApiModel):
    items: list[ProductSummary]
    total: int
    page: int
    page_size: int
    facets: Facets
    search: SearchMeta | None = Field(default=None, description="Present when a text query was run")
