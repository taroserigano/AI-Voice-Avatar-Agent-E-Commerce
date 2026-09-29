"""The product Q&A score checks catalog facts, not just an assistant's wording."""

from __future__ import annotations

import httpx
from assistant_eval import score


def test_catalog_constraints_catch_wrong_allergen_and_specification() -> None:
    product = {
        "title": "Plain Greek Yogurt",
        "specs": {"Style": "Greek", "Flavor": "Plain"},
        "allergens": ["milk"],
        "variants": [{"sku": "DAI-YOG-32OZ"}],
    }
    client = httpx.Client(
        base_url="http://test",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=product)),
    )
    got = {
        "text": "Plain Greek Yogurt",
        "cards": [
            {
                "kind": "product",
                "id": "one",
                "title": "Plain Greek Yogurt",
                "product_type": "yogurt",
                "tags": [],
                "price_minor": 499,
            }
        ],
        "tools": ["search_products"],
        "citations": [],
    }
    expect = {
        "action": "search",
        "result_constraints": {
            "specs": {"Style": "Greek"},
            "allergens_none": ["tree nuts"],
            "variant_code": "32OZ",
        },
    }
    assert score(expect, got, client)["result_constraints"] is True
    assert (
        score({**expect, "result_constraints": {"allergens_none": ["milk"]}}, got, client)[
            "result_constraints"
        ]
        is False
    )
    assert (
        score({**expect, "result_constraints": {"specs": {"Style": "Regular"}}}, got, client)[
            "result_constraints"
        ]
        is False
    )
    assert score(expect, {**got, "tools": []}, client)["uses_catalog"] is False
