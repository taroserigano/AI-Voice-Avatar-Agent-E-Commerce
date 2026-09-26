"""Structured product questions: types, required tags, excluded tags, and product facts.

These are the filters the assistant will use for requests like "non-fat organic milk, not
regular milk" or "sugar-free yogurt", so their answers have to be exactly right.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from commerce.seed.catalog import PRODUCTS


def _all(client: TestClient, **params: object) -> list[dict]:  # type: ignore[type-arg]
    items: list[dict] = []  # type: ignore[type-arg]
    page = 1
    while True:
        resp = client.get("/v1/products", params={**params, "page": page, "page_size": 60})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        items += body["items"]
        if len(items) >= body["total"]:
            return items
        page += 1


def _tags(item: dict) -> set[str]:  # type: ignore[type-arg]
    return {t["value"] for t in item["tags"]}


def test_organic_fat_free_milk_and_nothing_else(alice: TestClient) -> None:
    items = _all(alice, product_type="milk", tag=["organic", "fat-free"])
    expected = {
        p.title
        for p in PRODUCTS
        if p.product_type == "milk" and {"organic", "fat-free"} <= set(p.tags)
    }
    assert expected, "the seed catalog should have organic fat-free milk"
    assert {i["title"] for i in items} == expected
    for i in items:
        assert i["product_type"] == "milk"
        assert {"organic", "fat-free"} <= _tags(i)


def test_excluded_tags_are_removed(alice: TestClient) -> None:
    everything = _all(alice, product_type="milk")
    no_whole = _all(alice, product_type="milk", exclude_tag=["whole-milk"])
    assert any("whole-milk" in _tags(i) for i in everything)
    assert no_whole and all("whole-milk" not in _tags(i) for i in no_whole)
    assert len(no_whole) < len(everything)


def test_sugar_free_yogurt_really_has_no_sugar(alice: TestClient) -> None:
    items = _all(alice, product_type="yogurt", tag="sugar-free")
    assert items
    for i in items[:10]:
        detail = alice.get(f"/v1/products/{i['id']}").json()
        assert detail["nutrition"]["total_sugars_g"] < 0.5
        assert "milk" in detail["allergens"] or "dairy-free" in _tags(detail)


def test_product_detail_carries_facts(alice: TestClient) -> None:
    [milk] = [i for i in _all(alice, product_type="milk", tag=["organic", "fat-free"])
              if i["brand"] == "Cedar Hollow Farms" and "lactose-free" not in _tags(i)]  # fmt: skip
    detail = alice.get(f"/v1/products/{milk['id']}").json()
    assert detail["nutrition"]["total_fat_g"] == 0
    assert detail["allergens"] == ["milk"]
    assert detail["specs"]["Milkfat"] == "0%"
    assert "vitamin D3" in detail["ingredients"]
    assert {"value": "organic", "label": "Organic"} in detail["tags"]


def test_facets_offer_types_and_tags(alice: TestClient) -> None:
    body = alice.get("/v1/products", params={"category": "dairy-eggs"}).json()
    types = {f["value"]: f["count"] for f in body["facets"]["product_types"]}
    tags = {f["value"]: f for f in body["facets"]["tags"]}
    assert types["yogurt"] > 0 and types["milk"] > 0
    assert tags["organic"]["label"] == "Organic" and tags["organic"]["count"] > 0
    # Choosing a tag narrows every count to products that have it.
    narrowed = alice.get("/v1/products", params={"category": "dairy-eggs", "tag": "organic"}).json()
    assert (
        narrowed["total"] == {f["value"]: f for f in narrowed["facets"]["tags"]}["organic"]["count"]
    )


def test_text_search_understands_nonfat(alice: TestClient) -> None:
    body = alice.get("/v1/products", params={"q": "nonfat organic milk"}).json()
    top = body["items"][0]
    assert {"organic", "fat-free"} <= _tags(top)
    assert top["product_type"] == "milk"
