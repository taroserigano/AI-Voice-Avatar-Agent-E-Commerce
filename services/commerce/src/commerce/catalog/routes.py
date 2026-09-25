from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from commerce.catalog.schemas import CategoryOut, ProductDetail, ProductPage, SortOrder
from commerce.catalog.service import ProductFilters, get_product, list_categories, list_products
from commerce.db import get_db

router = APIRouter(prefix="/v1", tags=["catalog"])
DbDep = Annotated[Session, Depends(get_db)]


@router.get("/categories", response_model=list[CategoryOut])
def categories(db: DbDep) -> list[CategoryOut]:
    return list_categories(db)


@router.get("/products", response_model=ProductPage)
def products(
    db: DbDep,
    q: Annotated[str | None, Query(max_length=200, description="Free-text search")] = None,
    category: Annotated[str | None, Query(max_length=80)] = None,
    brand: Annotated[list[str] | None, Query(max_length=20)] = None,
    min_price: Annotated[int | None, Query(ge=0, description="Minor units")] = None,
    max_price: Annotated[int | None, Query(ge=0, description="Minor units")] = None,
    in_stock: bool = False,
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
    )
    return list_products(db, query=q, filters=filters, sort=sort, page=page, page_size=page_size)


@router.get(
    "/products/{product_id}",
    response_model=ProductDetail,
    responses={404: {"description": "No such product"}},
)
def product_detail(product_id: uuid.UUID, db: DbDep) -> ProductDetail:
    product = get_product(db, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    return product
