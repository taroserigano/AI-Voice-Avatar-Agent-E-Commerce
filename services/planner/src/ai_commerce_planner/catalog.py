"""The planner's read-only view of the catalog, from the commerce API.

Prices, stock, tags, and allergens always come from here (PostgreSQL behind the API), never
from the model. The planner's commerce identity may only read the catalog: it has no
cart, order, or return access (least privilege; see PLANNER_ROUTES in commerce).
"""

from __future__ import annotations

import uuid
from typing import Any, Protocol

import httpx
from pydantic import BaseModel


class VariantFacts(BaseModel):
    id: uuid.UUID
    name: str
    price_minor: int
    available: int


class ProductHit(BaseModel):
    """A search result: enough to choose what to look at."""

    id: uuid.UUID
    title: str
    brand: str
    product_type: str
    tags: list[str]
    price_minor: int
    in_stock: bool


class ProductFacts(BaseModel):
    id: uuid.UUID
    title: str
    brand: str
    category: str
    product_type: str
    tags: list[str]
    allergens: list[str]
    # True when the catalog has label data (ingredients or a nutrition panel). Without it,
    # an empty allergen list means "unknown", not "none".
    has_label: bool
    variants: list[VariantFacts]
    image_path: str = ""
    currency: str = "USD"


class CatalogPort(Protocol):
    def search(
        self,
        *,
        text: str | None = None,
        product_types: list[str] | None = None,
        tags: list[str] | None = None,
        exclude_tags: list[str] | None = None,
        max_price_minor: int | None = None,
        limit: int = 10,
    ) -> list[ProductHit]: ...

    def facts(self, product_id: uuid.UUID) -> ProductFacts | None: ...


class CommerceCatalog:
    """:class:`CatalogPort` over the commerce API, acting for one signed-in customer.

    ``headers`` carry the planner's service identity (``Authorization`` and
    ``X-On-Behalf-Of``). They're set by server code, never by the model.
    """

    def __init__(self, base_url: str, headers: dict[str, str], timeout_s: float = 5.0) -> None:
        self._http = httpx.Client(base_url=base_url, headers=headers, timeout=timeout_s)
        self._facts: dict[uuid.UUID, ProductFacts | None] = {}

    def close(self) -> None:
        self._http.close()

    def search(
        self,
        *,
        text: str | None = None,
        product_types: list[str] | None = None,
        tags: list[str] | None = None,
        exclude_tags: list[str] | None = None,
        max_price_minor: int | None = None,
        limit: int = 10,
    ) -> list[ProductHit]:
        params: list[tuple[str, Any]] = [
            ("page_size", min(max(limit, 1), 60)),
            ("in_stock", "true"),
        ]
        if text:
            params.append(("q", text[:200]))
        params += [("product_type", t) for t in (product_types or [])[:10]]
        params += [("tag", t) for t in (tags or [])[:10]]
        params += [("exclude_tag", t) for t in (exclude_tags or [])[:10]]
        if max_price_minor is not None:
            params.append(("max_price", max_price_minor))
        resp = self._http.get("/v1/products", params=params)
        resp.raise_for_status()
        return [
            ProductHit(
                id=item["id"],
                title=item["title"],
                brand=item["brand"],
                product_type=item["product_type"],
                tags=[t["value"] for t in item["tags"]],
                price_minor=item["price_minor"],
                in_stock=item["in_stock"],
            )
            for item in resp.json()["items"]
        ]

    def facts(self, product_id: uuid.UUID) -> ProductFacts | None:
        if product_id in self._facts:
            return self._facts[product_id]
        resp = self._http.get(f"/v1/products/{product_id}")
        if resp.status_code == 404:
            self._facts[product_id] = None
            return None
        resp.raise_for_status()
        self._facts[product_id] = facts_from_detail(resp.json())
        return self._facts[product_id]


def facts_from_detail(d: dict[str, Any]) -> ProductFacts:
    return ProductFacts(
        id=d["id"],
        title=d["title"],
        brand=d["brand"],
        category=d["category"]["slug"],
        product_type=d["product_type"],
        tags=[t["value"] for t in d["tags"]],
        allergens=list(d.get("allergens") or []),
        has_label=bool(d.get("ingredients") or d.get("nutrition")),
        variants=[
            VariantFacts(
                id=v["id"], name=v["name"], price_minor=v["price_minor"], available=v["available"]
            )
            for v in d["variants"]
        ],
        image_path=d.get("image_path", ""),
        currency=d.get("currency", "USD"),
    )
