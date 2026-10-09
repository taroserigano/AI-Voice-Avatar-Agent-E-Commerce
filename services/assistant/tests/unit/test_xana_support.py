"""What the customer-support sets (evals/xana/support) found Xena couldn't answer (2026-10-08):
order amounts and discounts, whether every order was listed, a price floor, every brand of a
kind, and help-center, shipping, and fair-use questions that never reached the policies."""

from __future__ import annotations

import json
from typing import Any

import assistant.commerce as commerce_mod
import assistant.tools as tools_mod
from assistant.policy_prefetch import retrieval_query, wants_policy
from assistant.tools import ToolContext, list_my_orders, search_products

from .test_xana_accuracy import Orders, PlantMilks


def _payload(content: str) -> dict[str, Any]:
    return json.loads(content.split("\n", 1)[1].rsplit("\n", 1)[0])


def test_an_order_shows_its_payment_summary_and_each_lines_discount() -> None:
    order = tools_mod._order_for_model(
        {
            "id": "e3c5e556-0000-4000-8000-000000000000",
            "status": "paid",
            "placed_at": "2026-09-17T12:00:00+00:00",
            "subtotal_minor": 9000,
            "discount_minor": 1000,
            "shipping_minor": 0,
            "tax_minor": 660,
            "total_minor": 8660,
            "lines": [
                {
                    "id": "l1",
                    "product_title": "Organic Cotton Tee",
                    "variant_name": "M",
                    "quantity": 3,
                    "unit_price_minor": 2200,
                    "amount_discount_minor": 1000,
                    "amount_tax_minor": 462,
                    "amount_total_minor": 6062,
                }
            ],
        }
    )
    assert (order["subtotal"], order["discount"], order["tax"], order["total"]) == (
        "$90.00",
        "$10.00",
        "$6.60",
        "$86.60",
    )
    # "Did my discount apply on the tees?" had no answer before.
    assert order["items"][0]["line_discount"] == "$10.00"
    assert order["items"][0]["line_total"] == "$60.62"
    # The order pages say "Preparing" for a paid order that hasn't shipped.
    assert order["status"] == "Preparing"


def test_a_short_order_list_says_every_order_is_there() -> None:
    tools_mod._BRANDS.clear()
    config = {"configurable": {"ctx": ToolContext(client=Orders(), agent="xana")}}  # type: ignore[arg-type]
    content, _ = list_my_orders.func(config)  # type: ignore[attr-defined]
    assert _payload(content)["all_orders_listed"] is True
    # A filtered list isn't every order, so no all-time totals from it.
    content, _ = list_my_orders.func(config, contains="pens")  # type: ignore[attr-defined]
    assert _payload(content)["all_orders_listed"] is False


def test_a_price_floor_filters_the_search_and_picks_a_variant_above_it() -> None:
    commerce_mod._vocabulary = None
    seen: list[dict[str, Any]] = []

    class Spy(PlantMilks):
        def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
            if path == "/v1/products":
                seen.append(dict(params or {}))
            return super().get(path, params)

    config = {"configurable": {"ctx": ToolContext(client=Spy(), agent="xana")}}
    _, cards = search_products.func(  # type: ignore[attr-defined]
        config, product_types=["plant-milk"], min_price_dollars=3.5
    )
    assert seen[0]["min_price"] == 350
    products = [c for c in cards if c["kind"] == "product"]
    # Each milk's quart is $2.99 and its half gallon $3.99: over $3.50 means the half gallon.
    assert products and {c["variant_name"] for c in products} == {"Half gallon"}
    summary = next(c for c in cards if c["kind"] == "search")
    assert "Over $3.50" in summary["chips"]


def test_a_search_names_every_brand_among_its_matches() -> None:
    commerce_mod._vocabulary = None

    class Branded(PlantMilks):
        def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
            page = super().get(path, params)
            if path == "/v1/products":
                brands = ["Silverleaf", "Oatfield", "Silverleaf"]
                page["items"] = [{**i, "brand": b} for i, b in zip(page["items"], brands, strict=True)]
            return page

    config = {"configurable": {"ctx": ToolContext(client=Branded(), agent="xana")}}
    content, _ = search_products.func(config, product_types=["plant-milk"])  # type: ignore[attr-defined]
    payload = _payload(content)
    assert payload["brands"] == {"Silverleaf": 2, "Oatfield": 1}
    assert payload["brands_cover_every_match"] is True


def test_help_center_and_shipping_questions_search_the_policies_first() -> None:
    for question in [
        "how do I reset my password?",
        "do you take PayPal?",
        "do you have any promo codes?",
        "can I get a receipt for my order?",
        "how do I leave a review?",
        "I want to dispute a charge",
        "do you ship to Canada?",
        "I live in Japan, can I order?",
        "will I get banned for returning too much?",
        "what does Preparing mean on my order?",
    ]:
        assert wants_policy(question), question
    assert not wants_policy("where's my yoga mat?")
    assert not wants_policy("do you have vegan cheese?")


def test_another_country_asks_where_we_ship_and_too_many_returns_asks_for_fair_use() -> None:
    assert "united states only" in retrieval_query("I live in Japan, can I order?")
    assert "fair use" in retrieval_query("will I get banned for returning too much?")
    assert "fair use" not in retrieval_query("how long do I have to return something?")
