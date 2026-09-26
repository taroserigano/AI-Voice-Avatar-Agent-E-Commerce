from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import Session

from commerce.catalog.models import InventoryBalance, Price
from commerce.search import keyword as keyword_module
from commerce.seed.catalog import PRODUCTS

from .conftest import variant_id_for

pytestmark = pytest.mark.integration


def _titles(page: dict) -> list[str]:  # type: ignore[type-arg]
    return [item["title"] for item in page["items"]]


def test_wireless_headphones_query_finds_headphones_first(alice: TestClient) -> None:
    page = alice.get("/v1/products", params={"q": "wireless headphones"}).json()
    top = page["items"][:5]
    assert all(i["product_type"] in {"headphones", "earbuds"} for i in top)
    assert all("wireless" in {t["value"] for t in i["tags"]} for i in top)
    assert "Arc Wireless Over-Ear Headphones" in _titles(page)[:5]
    assert page["search"]["keyword"] == "ok"


def test_rain_shoes_query_finds_waterproof_footwear(alice: TestClient) -> None:
    page = alice.get("/v1/products", params={"q": "waterproof shoes for rain"}).json()
    footwear = {"boots", "running-shoes", "sneakers", "sandals"}
    assert all(i["product_type"] in footwear for i in page["items"][:5])
    assert _titles(page)[0] == "Puddle Waterproof Rain Boots"


def test_search_prices_come_from_postgres_not_the_index(alice: TestClient, db: Session) -> None:
    vid = variant_id_for(db, "sonora-arc-wireless-headphones", "MID")
    db.execute(update(Price).where(Price.variant_id == vid).values(amount_minor=100))
    db.commit()
    # No reindex: the search projection is stale, but the numbers must not be.
    page = alice.get("/v1/products", params={"q": "arc headphones"}).json()
    arc = next(i for i in page["items"] if i["title"].startswith("Arc"))
    assert arc["price_minor"] == 100


def test_product_detail_has_fresh_price_and_stock(alice: TestClient, db: Session) -> None:
    page = alice.get("/v1/products", params={"q": "camp chair"}).json()
    product_id = page["items"][0]["id"]
    vid = variant_id_for(db, "summit-forge-camp-chair", "STD")

    before = alice.get(f"/v1/products/{product_id}").json()
    assert before["variants"][0]["available"] == 1

    db.execute(update(InventoryBalance).where(InventoryBalance.variant_id == vid).values(on_hand=0))
    db.commit()
    after = alice.get(f"/v1/products/{product_id}").json()
    assert after["variants"][0]["available"] == 0
    assert after["in_stock"] is False


def test_filters_and_facets(alice: TestClient) -> None:
    page = alice.get(
        "/v1/products", params={"category": "electronics", "max_price": 5000, "in_stock": "true"}
    ).json()
    assert page["total"] > 0
    assert all(i["category"]["slug"] == "electronics" for i in page["items"])
    assert all(i["price_minor"] <= 5000 and i["in_stock"] for i in page["items"])
    # The category facet ignores its own filter, so other categories still show counts.
    assert len(page["facets"]["categories"]) > 1


def test_in_stock_filter_hides_sold_out_products(alice: TestClient) -> None:
    params = {"q": "mixing bowls", "category": "home-kitchen"}
    all_kitchen = _titles(alice.get("/v1/products", params=params).json())
    in_stock = _titles(alice.get("/v1/products", params={**params, "in_stock": "true"}).json())
    assert "Nesting Stainless Mixing Bowls, Set of 5" in all_kitchen
    assert "Nesting Stainless Mixing Bowls, Set of 5" not in in_stock


def test_sorting_and_pagination(alice: TestClient) -> None:
    first = alice.get("/v1/products", params={"sort": "price_asc", "page_size": 5}).json()
    second = alice.get(
        "/v1/products", params={"sort": "price_asc", "page_size": 5, "page": 2}
    ).json()
    prices = [i["price_minor"] for i in first["items"] + second["items"]]
    assert prices == sorted(prices)
    assert first["total"] == len(PRODUCTS)
    assert not set(_titles(first)) & set(_titles(second))


def test_search_degrades_instead_of_failing_when_opensearch_is_down(
    alice: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Broken:
        def search(self, *a, **k):  # type: ignore[no-untyped-def]
            raise ConnectionError("opensearch down")

    monkeypatch.setattr("commerce.catalog.service.get_keyword_index", lambda: Broken())
    page = alice.get("/v1/products", params={"q": "yoga mat"}).json()
    assert page["search"]["keyword"] == "unavailable"
    assert page["search"]["notice"]
    assert "Grip Yoga Mat, 6 mm" in _titles(page)  # SQL fallback still finds it
    assert keyword_module  # module import kept for clarity of what is patched


def test_unknown_product_is_404(alice: TestClient) -> None:
    assert alice.get("/v1/products/00000000-0000-0000-0000-000000000000").status_code == 404
