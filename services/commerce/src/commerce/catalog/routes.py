from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from commerce.activity.models import EventType
from commerce.activity.service import record
from commerce.api_model import ApiModel
from commerce.auth.deps import CurrentUser
from commerce.catalog.display import type_label
from commerce.catalog.models import Product
from commerce.catalog.schemas import (
    CategoryOut,
    FacetValue,
    ProductDetail,
    ProductPage,
    SearchSuggestions,
    SortOrder,
)
from commerce.catalog.service import (
    ProductFilters,
    get_product,
    get_products,
    list_categories,
    list_products,
)
from commerce.catalog.tags import tag_label
from commerce.db import get_db
from commerce.search.suggest import suggest

router = APIRouter(prefix="/v1", tags=["catalog"])
DbDep = Annotated[Session, Depends(get_db)]


@router.get("/categories", response_model=list[CategoryOut])
def categories(db: DbDep) -> list[CategoryOut]:
    return list_categories(db)


@router.get("/products", response_model=ProductPage)
def products(
    db: DbDep,
    principal: CurrentUser,
    background: BackgroundTasks,
    q: Annotated[str | None, Query(max_length=200, description="Free-text search")] = None,
    category: Annotated[str | None, Query(max_length=80)] = None,
    brand: Annotated[list[str] | None, Query(max_length=20)] = None,
    min_price: Annotated[int | None, Query(ge=0, description="Minor units")] = None,
    max_price: Annotated[int | None, Query(ge=0, description="Minor units")] = None,
    in_stock: bool = False,
    product_type: Annotated[
        list[str] | None,
        # Up to 30: a ranking across a group ("top rated vegetables") is ~20 fresh types.
        Query(max_length=30, description='Any of these types, e.g. "milk", "yogurt"'),
    ] = None,
    tag: Annotated[
        list[str] | None,
        Query(max_length=10, description='Every one of these tags, e.g. "organic", "fat-free"'),
    ] = None,
    exclude_tag: Annotated[
        list[str] | None,
        Query(max_length=10, description='None of these tags, e.g. "whole-milk"'),
    ] = None,
    sort: SortOrder = SortOrder.RELEVANCE,
    page: Annotated[int, Query(ge=1, le=1000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=60)] = 24,
) -> ProductPage:
    filters = ProductFilters(
        category=category,
        brands=tuple(brand or ()),
        min_price_minor=min_price,
        max_price_minor=max_price,
        in_stock=in_stock,
        product_types=tuple(product_type or ()),
        tags=tuple(tag or ()),
        exclude_tags=tuple(exclude_tag or ()),
    )
    result = list_products(db, query=q, filters=filters, sort=sort, page=page, page_size=page_size)
    if q and q.strip() and page == 1:
        background.add_task(
            record,
            principal.id,
            EventType.SEARCHED,
            data={"query": q.strip()[:200], "results": result.total},
        )
    return result


@router.get("/search/suggest", response_model=SearchSuggestions)
def search_suggest(
    db: DbDep,
    principal: CurrentUser,
    response: Response,
    q: Annotated[str, Query(max_length=100, description="What the shopper has typed so far")],
) -> SearchSuggestions:
    """Typeahead for the search box: completed queries, matching types and departments, and a
    few products. Fast word-prefix matching in PostgreSQL; nothing is recorded."""
    # Private (per session) but identical for everyone: a short browser cache makes
    # backspacing and retyping instant.
    response.headers["Cache-Control"] = "private, max-age=60"
    return suggest(db, q)


@router.get("/product-details", response_model=list[ProductDetail])
def product_details(
    db: DbDep,
    principal: CurrentUser,
    product_id: Annotated[
        list[uuid.UUID], Query(alias="id", min_length=1, max_length=60, description="Up to 60 ids")
    ],
) -> list[ProductDetail]:
    """Several products in full (variants with price and stock, nutrition, ingredients,
    allergens, specs), in the order asked. Unknown or inactive ids are left out. For the
    assistant's catalog search, which reads every candidate it verifies: one call instead of one
    per product, and, unlike opening a product page, nothing is recorded as viewed."""
    return get_products(db, product_id)


@router.get(
    "/products/{product_id}",
    response_model=ProductDetail,
    responses={404: {"description": "No such product"}},
)
def product_detail(
    product_id: uuid.UUID, db: DbDep, principal: CurrentUser, background: BackgroundTasks
) -> ProductDetail:
    product = get_product(db, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    background.add_task(record, principal.id, EventType.VIEWED_PRODUCT, product_id=product.id)
    return product


class CatalogVocabulary(ApiModel):
    """Every product type and tag in the active catalog, with counts: the values the assistant
    may pass to the product_type / tag / exclude_tag filters."""

    product_types: list[FacetValue]
    tags: list[FacetValue]


@router.get("/catalog/vocabulary", response_model=CatalogVocabulary)
def vocabulary(db: DbDep) -> CatalogVocabulary:
    active = Product.is_active.is_(True)
    types = db.execute(
        select(Product.product_type, func.count())
        .where(active)
        .group_by(Product.product_type)
        .order_by(Product.product_type)
    )
    tag = func.unnest(Product.tags).label("tag")
    tag_rows = db.execute(select(tag, func.count()).where(active).group_by(tag).order_by(tag))
    return CatalogVocabulary(
        product_types=[FacetValue(value=t, label=type_label(t), count=c) for t, c in types],
        tags=[FacetValue(value=t, label=tag_label(t), count=c) for t, c in tag_rows],
    )
