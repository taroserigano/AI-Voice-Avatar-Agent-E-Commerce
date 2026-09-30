"""Fixes found by Xana's golden-set eval (evals/xana_eval.py): what the customer sees in a turn."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

from langchain_core.messages import AIMessage, AIMessageChunk

import assistant.tools as tools_mod
from assistant.commerce import CommerceError
from assistant.return_tools import quote_return
from assistant.tools import ToolContext, list_my_orders
from assistant.turns import ProductCards, run_turn


class FakeGraph:
    """Streams what LangGraph streams for one turn: text chunks, then the node updates."""

    def __init__(self, events: list[tuple[str, Any]]) -> None:
        self.events = events

    def stream(self, *_: Any, **__: Any) -> Iterator[tuple[str, Any]]:
        yield from self.events


def sse_events(chunks: Iterator[str]) -> list[tuple[str, Any]]:
    out = []
    for block in chunks:
        head, data = block.strip().split("\n", 1)
        out.append((head.removeprefix("event: "), json.loads(data.removeprefix("data: "))))
    return out


def product(pid: str, title: str) -> dict[str, Any]:
    return {"kind": "product", "id": pid, "title": title}


def test_an_answer_streamed_in_chunks_is_not_repeated_by_its_final_message() -> None:
    # The Responses API gives the streamed chunks and the final message different ids.
    agent = {"langgraph_node": "agent"}
    final = AIMessage(content="It arrives Friday.", id="msg-9")
    graph = FakeGraph(
        [
            ("messages", (AIMessageChunk(content="It arrives ", id="chunk-1"), agent)),
            ("messages", (AIMessageChunk(content="Friday.", id="chunk-1"), agent)),
            ("updates", {"agent": {"messages": [final]}}),
        ]
    )
    events = sse_events(
        run_turn(graph, conversation_id="c", agent="xana", ctx=ToolContext(client=None), text="?")  # type: ignore[arg-type]
    )
    text = "".join(d["delta"] for e, d in events if e == "text")
    assert text == "It arrives Friday."


def test_a_refined_search_replaces_the_near_misses_on_screen() -> None:
    cards = ProductCards()
    broad = [
        {"kind": "search", "total": 30},
        product("1", "Dark Roast"),
        product("2", "Light Roast"),
    ]
    verified = [{"kind": "search", "total": 1}, product("2", "Light Roast")]
    order = [{"kind": "order", "id": "o"}]
    assert cards.take("search_products", broad) == []
    assert cards.take("search_products", verified) == []
    assert cards.take("list_my_orders", order) == order  # not a product card: shown at once
    assert [c.get("title") for c in cards.final()] == [None, "Light Roast"]


def test_products_read_in_detail_come_first_and_appear_once() -> None:
    cards = ProductCards()
    cards.take("search_products", [product("1", "A"), product("2", "B")])
    cards.take("get_product_details", [product("2", "B")])
    assert [c["title"] for c in cards.final()] == ["B", "A"]


class Orders:
    def __init__(self) -> None:
        self.product_reads = 0

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        if path == "/v1/orders":
            return [{"id": "o1"}]
        if path == "/v1/orders/o1":
            return {
                "id": "11111111-1111-4111-8111-111111111111",
                "status": "delivered",
                "placed_at": "2026-09-20T12:00:00+00:00",
                "delivered_at": "2026-09-23T12:00:00+00:00",
                "total_minor": 1897,
                "item_count": 1,
                "lines": [
                    {
                        "id": "l1",
                        "product_id": "p-pens",
                        "product_title": "Quick-Dry Gel Pens, 12-Pack",
                        "variant_name": "Standard",
                        "quantity": 1,
                        "unit_price_minor": 1298,
                        "image_path": "/pens.svg",
                    }
                ],
            }
        if path == "/v1/products/p-pens":
            self.product_reads += 1
            return {"brand": "Quillmark"}
        raise AssertionError(path)


def test_an_order_item_is_found_by_its_brand() -> None:
    tools_mod._BRANDS.clear()
    client = Orders()
    config = {"configurable": {"ctx": ToolContext(client=client, agent="xana")}}  # type: ignore[arg-type]
    content, cards = list_my_orders.func(config, contains="Quillmark pens")  # type: ignore[attr-defined]
    assert '"brand": "Quillmark"' in content and '"count": 1' in content and cards
    list_my_orders.func(config, contains="quillmark")  # type: ignore[attr-defined]
    assert client.product_reads == 1  # a product's brand is read once


ORDER = "7a762eb8-e306-5151-bbc2-33e29b160f12"
OTTER = "e7ac7b91-9288-5034-b8b2-25d838992422"
NOTEBOOK = "b16e9b06-17ee-5271-b8aa-37c3362d7de9"


class Returns:
    """One order with two lines; records the quote it was asked for."""

    def __init__(self, reject: str | None = None) -> None:
        self.reject = reject
        self.quoted: dict[str, Any] | None = None

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        if path == "/v1/orders":
            return [{"id": ORDER}]
        assert path == f"/v1/orders/{ORDER}/return-options"
        return {"order_id": ORDER, "lines": [{"order_line_id": OTTER}, {"order_line_id": NOTEBOOK}]}

    def post(self, path: str, body: dict[str, Any]) -> Any:
        if self.reject:
            raise CommerceError(
                422, "not returnable", [{"reason": self.reject, "message": "Quality only."}]
            )
        self.quoted = body
        return {
            "id": "q1",
            "total_refund_minor": 1623,
            "shipping_refund_minor": 0,
            "needs_shipping": True,
            "expires_at": "later",
            "lines": [],
        }


def quote(client: Returns, order_id: str, line: str) -> str:
    config = {"configurable": {"ctx": ToolContext(client=client, agent="xana")}}  # type: ignore[arg-type]
    content, _ = quote_return.func(  # type: ignore[attr-defined]
        config, order_id=order_id, lines=[{"order_line_id": line, "quantity": 1}]
    )
    return str(content)


def test_a_food_quote_without_a_quality_reason_says_how_to_recover() -> None:
    content = quote(Returns(reject="perishable_reason"), ORDER, NOTEBOOK)
    assert "spoiled_or_expired" in content and "don't quote it" in content


def test_a_return_line_is_named_by_its_short_handle_and_a_spliced_id_is_refused() -> None:
    store = Returns()
    quote(store, ORDER, NOTEBOOK[:8])
    assert store.quoted and store.quoted["lines"][0]["order_line_id"] == NOTEBOOK
    quote(store, "9B160F12", NOTEBOOK)  # the order number the customer sees
    assert store.quoted["order_id"] == ORDER
    # Seen live: the notebook's handle spliced onto the otter's id. The handle decides, and
    # the quote card the customer confirms names the item.
    quote(store, ORDER, "b16e9b06-17ee-5271-b8b2-25d838992422")
    assert store.quoted["lines"][0]["order_line_id"] == NOTEBOOK
    content = quote(Returns(), ORDER, "ffffffff")
    assert "isn't an order_line_id" in content


def milk(pid: str, title: str, flavor: str) -> dict[str, Any]:
    return {
        "id": pid,
        "title": title,
        "brand": "Silverleaf",
        "product_type": "plant-milk",
        "price_minor": 299,
        "currency": "USD",
        "image_path": "/m.svg",
        "in_stock": True,
        "tags": [],
        "specs": {"Flavor": flavor},
        "allergens": ["tree nuts"],
        "variants": [
            {"id": pid + "-qt", "name": "1 quart", "price_minor": 299, "in_stock": True},
            {"id": pid + "-hg", "name": "Half gallon", "price_minor": 399, "in_stock": True},
        ],
    }


class PlantMilks:
    MILKS = {
        "a1": milk("a1", "Unsweetened Vanilla Almond Milk", "Unsweetened Vanilla"),
        "a2": milk("a2", "Unsweetened Original Almond Milk", "Unsweetened Original"),
        "a3": milk("a3", "Vanilla Almond Milk", "Vanilla"),
    }

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        if path == "/v1/catalog/vocabulary":
            return {"product_types": [{"value": "plant-milk", "label": "Plant milk"}], "tags": []}
        if path == "/v1/products":
            return {"items": [{"id": k} for k in self.MILKS], "total": 3, "search": None}
        return self.MILKS[path.rsplit("/", 1)[1]]


def search(**args: Any) -> list[dict[str, Any]]:
    import assistant.commerce as commerce_mod
    from assistant.tools import search_products

    commerce_mod._vocabulary = None
    config = {"configurable": {"ctx": ToolContext(client=PlantMilks(), agent="xana")}}
    _, cards = search_products.func(config, product_types=["plant-milk"], **args)  # type: ignore[attr-defined]
    return [c for c in cards if c["kind"] == "product"]


def test_a_flavor_matches_as_words_but_an_exact_flavor_wins() -> None:
    assert [c["title"] for c in search(required_specs={"Flavor": "Vanilla"})] == [
        "Vanilla Almond Milk"
    ]
    found = search(required_specs={"Flavor": "Unsweetened Vanilla"})
    assert [c["title"] for c in found] == ["Unsweetened Vanilla Almond Milk"]
    words = search(required_specs={"Flavor": "Original"})
    assert [c["title"] for c in words] == ["Unsweetened Original Almond Milk"]


def test_a_requested_size_shows_that_sizes_price() -> None:
    for args in ({"variant_terms": ["half gallon"]}, {"required_specs": {"Size": "Half gallon"}}):
        cards = search(**args)
        assert len(cards) == 3
        assert {(c["variant_name"], c["price_minor"]) for c in cards} == {("Half gallon", 399)}
    assert search(variant_terms=["gallon jug"]) == []


def test_a_named_product_is_verified_by_its_brand_too() -> None:
    # The brand isn't in the title: a model that puts it in the title terms or the specs
    # still finds the product.
    named = search(required_title_terms=["Silverleaf Vanilla"])
    assert [c["title"] for c in named] == ["Vanilla Almond Milk"]
    assert len(search(required_title_terms=["Silverleaf"])) == 3
    assert len(search(required_specs={"Brand": "Silverleaf"})) == 3
    assert search(required_specs={"Brand": "Fernbrook"}) == []


class ManyCereals:
    """70 cereals over two pages; the most fiber is on the second page."""

    def __init__(self) -> None:
        self.ids = [f"c{i:02d}" for i in range(70)]

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        if path == "/v1/catalog/vocabulary":
            return {"product_types": [{"value": "cereal", "label": "Cereal"}], "tags": []}
        if path == "/v1/products":
            page = (params or {}).get("page", 1)
            size = (params or {})["page_size"]
            chunk = self.ids[(page - 1) * size : page * size]
            return {"items": [{"id": i} for i in chunk], "total": len(self.ids), "search": None}
        pid = path.rsplit("/", 1)[1]
        n = int(pid[1:])
        detail = milk(pid, f"Cereal {n}", "Plain")
        detail["product_type"] = "cereal"
        detail["nutrition"] = {
            "serving_size": "1 cup",
            "calories": 120,
            "protein_g": 3.0,
            "total_fat_g": 1.0,
            "added_sugars_g": 4.0,
            "fiber_g": 13.0 if n == 64 else n % 7,
            "sodium_mg": 100 + n,
        }
        return detail


def test_a_nutrient_sort_ranks_every_match_not_the_first_page() -> None:
    import assistant.commerce as commerce_mod
    from assistant.tools import search_products

    commerce_mod._vocabulary = None
    config = {"configurable": {"ctx": ToolContext(client=ManyCereals(), agent="xana")}}
    content, cards = search_products.func(  # type: ignore[attr-defined]
        config, product_types=["cereal"], sort="fiber_desc"
    )
    titles = [c["title"] for c in cards if c["kind"] == "product"]
    assert titles[0] == "Cereal 64"
    assert '"ranked_among": 70' in content and '"verification_limited": false' in content
    _, cards = search_products.func(config, product_types=["cereal"], sort="sodium_asc")  # type: ignore[attr-defined]
    assert [c["title"] for c in cards if c["kind"] == "product"][0] == "Cereal 0"


def test_products_that_say_every_search_word_come_before_near_misses() -> None:
    titles = [c["title"] for c in search(query="vanilla almond milk")]
    assert titles == ["Unsweetened Vanilla Almond Milk", "Vanilla Almond Milk"]
    # No product says them all: the relevance results stay.
    assert len(search(query="something for breakfast")) == 3
