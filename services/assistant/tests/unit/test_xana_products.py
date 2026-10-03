"""Xena's product answers use the same catalog tools as Steph and stay within their facts."""

from __future__ import annotations

from typing import Any

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

import assistant.commerce as commerce_mod
from assistant.scripted import ScriptedChatModel
from assistant.tools import ToolContext, product_card, search_products, untrusted
from assistant.toolsets import XANA_TOOLS

PRODUCT_ID = "33333333-3333-4333-8333-333333333333"
VOCAB = {
    "product_types": [{"value": "yogurt", "label": "Yogurt"}],
    "tags": [{"value": "sugar-free", "label": "Sugar free"}],
}
NAMES = [tool.name for tool in XANA_TOOLS]


class Catalog:
    def __init__(self) -> None:
        self.paths: list[str] = []

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if path == "/v1/product-details":  # the bulk read, answered one product at a time
            found = []
            for pid in (params or {})["id"]:
                try:
                    found.append(self.get(f"/v1/products/{pid}"))
                except AssertionError:
                    raise
                except Exception:  # noqa: BLE001 - an unknown product is left out
                    pass
            return found
        self.paths.append(path)
        if path == "/v1/catalog/vocabulary":
            return VOCAB
        if path == "/v1/products":
            assert params == {"page_size": 24, "sort": "relevance", "product_type": ["yogurt"]}
            return {"items": [{"id": PRODUCT_ID}], "total": 1, "search": None}
        if path == f"/v1/products/{PRODUCT_ID}":
            return {
                "id": PRODUCT_ID,
                "title": "Plain Greek Yogurt",
                "brand": "Fernbrook",
                "product_type": "yogurt",
                "price_minor": 499,
                "currency": "USD",
                "image_path": "/yogurt.svg",
                "in_stock": True,
                "tags": [],
                "variants": [
                    {"id": PRODUCT_ID, "name": "32 oz", "price_minor": 499, "in_stock": True}
                ],
                "description": "Plain cultured yogurt.",
                "nutrition": None,
                "ingredients": "Cultured milk",
                "allergens": ["milk"],
                "specs": {},
                "category": {"name": "Dairy & Eggs", "policy_class": "perishable"},
            }
        raise AssertionError(path)


def test_xana_has_read_only_product_tools() -> None:
    assert {"search_products", "get_product_details"} <= set(NAMES)
    assert "add_to_cart" not in NAMES


def test_unknown_filter_does_not_run_a_broader_search(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(commerce_mod, "_vocabulary", None)
    client = Catalog()
    result = search_products.invoke(
        {"product_types": ["unknown-type"]},
        config={"configurable": {"ctx": ToolContext(client=client, agent="xana")}},  # type: ignore[arg-type]
    )
    assert "unsupported_filters" in str(result)
    assert client.paths == ["/v1/catalog/vocabulary"]


def test_xana_search_reads_current_product_details(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(commerce_mod, "_vocabulary", None)
    client = Catalog()
    result = search_products.invoke(
        {"product_types": ["yogurt"]},
        config={"configurable": {"ctx": ToolContext(client=client, agent="xana")}},  # type: ignore[arg-type]
    )
    assert "Plain Greek Yogurt" in str(result)
    assert "$4.99" in str(result)
    assert client.paths == [
        "/v1/catalog/vocabulary",
        "/v1/products",
        f"/v1/products/{PRODUCT_ID}",
    ]


def test_search_verifies_specs_and_allergens_before_showing_cards(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(commerce_mod, "_vocabulary", None)
    client = Catalog()
    config = {"configurable": {"ctx": ToolContext(client=client, agent="xana")}}
    result = search_products.invoke(
        {"product_types": ["yogurt"], "required_specs": {"Flavor": "Chocolate"}},
        config=config,  # type: ignore[arg-type]
    )
    assert "Plain Greek Yogurt" not in str(result)
    assert "verified_constraints" in str(result)
    assert '"total_matches": 0' in str(result)

    result = search_products.invoke(
        {"product_types": ["yogurt"], "exclude_allergens": ["milk"]},
        config=config,  # type: ignore[arg-type]
    )
    assert "Plain Greek Yogurt" not in str(result)


def test_product_card_price_is_for_its_selected_variant() -> None:
    detail = Catalog().get(f"/v1/products/{PRODUCT_ID}")
    detail["price_minor"] = 499
    detail["variants"] = [
        {"id": PRODUCT_ID, "name": "16 oz", "price_minor": 499, "in_stock": False},
        {
            "id": "44444444-4444-4444-8444-444444444444",
            "name": "32 oz",
            "price_minor": 799,
            "in_stock": True,
        },
    ]
    card = product_card(detail)
    assert card.variant_name == "32 oz"
    assert card.price_minor == 799
    assert card.in_stock is True
    affordable = product_card(detail, max_price_minor=500)
    assert affordable.variant_name == "16 oz"
    assert affordable.price_minor == 499
    assert affordable.in_stock is False


def test_xana_looks_up_one_product_before_answering_an_allergen_question() -> None:
    model = ScriptedChatModel()
    human = HumanMessage("Does the yogurt contain milk?")
    search_call = model.invoke(
        [human], agent="xana", vocabulary=VOCAB, tool_names=NAMES
    ).tool_calls[0]
    assert search_call["name"] == "search_products"
    assert search_call["args"]["product_types"] == ["yogurt"]

    search_result = ToolMessage(
        untrusted(
            "search_products",
            {"total_matches": 1, "results": [{"product_id": PRODUCT_ID}]},
        ),
        name="search_products",
        tool_call_id=search_call["id"],
    )
    detail_call = model.invoke(
        [human, AIMessage("", tool_calls=[search_call]), search_result],
        agent="xana",
        vocabulary=VOCAB,
        tool_names=NAMES,
    ).tool_calls[0]
    assert detail_call["name"] == "get_product_details"
    assert detail_call["args"] == {"product_id": PRODUCT_ID}

    detail_result = ToolMessage(
        untrusted(
            "get_product_details",
            {"title": "Plain Greek Yogurt", "allergens": ["milk"], "ingredients": "Cultured milk"},
        ),
        name="get_product_details",
        tool_call_id=detail_call["id"],
    )
    answer = model.invoke(
        [
            human,
            AIMessage("", tool_calls=[search_call]),
            search_result,
            AIMessage("", tool_calls=[detail_call]),
            detail_result,
        ],
        agent="xana",
        vocabulary=VOCAB,
        tool_names=NAMES,
    ).content
    assert "listed major allergens" in answer
    assert "milk" in answer
    assert "cross-contact" in answer


def test_xana_asks_which_product_when_a_fact_question_has_multiple_matches() -> None:
    model = ScriptedChatModel()
    human = HumanMessage("Does the yogurt contain milk?")
    search = ToolMessage(
        untrusted(
            "search_products",
            {"results": [{"product_id": PRODUCT_ID}, {"product_id": "another"}]},
        ),
        name="search_products",
        tool_call_id="c1",
    )
    answer = model.invoke(
        [
            human,
            AIMessage("", tool_calls=[{"name": "search_products", "args": {}, "id": "c1"}]),
            search,
        ],
        agent="xana",
        vocabulary=VOCAB,
        tool_names=NAMES,
    ).content
    assert answer == "I found several possible products. Which one do you mean?"


def test_xana_asks_again_on_an_ambiguous_follow_up() -> None:
    cards = ToolMessage(
        "{}",
        name="search_products",
        tool_call_id="c1",
        artifact=[
            {"kind": "product", "id": PRODUCT_ID},
            {"kind": "product", "id": "44444444-4444-4444-8444-444444444444"},
        ],
    )
    reply = ScriptedChatModel().invoke(
        [
            HumanMessage("Show me yogurt"),
            AIMessage("", tool_calls=[{"name": "search_products", "args": {}, "id": "c1"}]),
            cards,
            AIMessage("Here are two products."),
            HumanMessage("What are the ingredients?"),
        ],
        agent="xana",
        vocabulary=VOCAB,
        tool_names=NAMES,
    )
    assert reply.tool_calls == []
    assert "Which product" in reply.content


def test_every_variant_is_shown_so_a_later_size_isnt_read_as_missing() -> None:
    """Found by the golden eval: only the first 6 variants were listed, so diapers in Size 6
    (the 7th, out of stock) were answered as "not offered"."""
    from assistant.tools import _product_for_model

    detail = {
        "id": "p1", "title": "Everyday Diapers", "brand": "Serigan Mart Baby", "product_type": "diapers",
        "price_minor": 1999, "tags": [], "category": {"policy_class": "standard"},
        "variants": [{"id": f"v{i}", "name": f"Size {i}", "price_minor": 1999, "in_stock": i != 6}
                     for i in range(1, 9)],
    }  # fmt: skip
    names = [v["name"] for v in _product_for_model(detail)["variants"]]
    assert names == [f"Size {i}" for i in range(1, 9)]


def test_cards_come_from_the_search_the_answer_is_about() -> None:
    """Found by the golden eval: "only low fat ones" was answered with 1% milk, but the cards
    came from a later near-miss search for 2% reduced-fat milk."""
    from assistant.turns import ProductCards

    def card(title: str) -> dict[str, str]:
        return {"kind": "product", "id": title, "title": title}

    cards = ProductCards()
    cards.take("search_products", [card("1% Low Fat Milk"), card("1% Low Fat Lactose-Free Milk")])
    cards.take("search_products", [card("2% Reduced Fat Milk")])
    shown = cards.final("Serigan Mart Kitchen 1% Low Fat Milk is $2.19 for a half gallon.")
    assert [c["title"] for c in shown] == ["1% Low Fat Milk", "1% Low Fat Lactose-Free Milk"]
    # An answer that names no product keeps the last search, as before.
    assert [c["title"] for c in cards.final("Here are some options.")] == ["2% Reduced Fat Milk"]


def test_a_pack_is_found_by_how_people_say_it() -> None:
    """Found by the golden eval: "the 4-pack of 5.3 oz cups" found no variant named
    "4 x 5.3 oz cups", and the price question was answered "I couldn't find that yogurt"."""
    from assistant.tools import _selected_variant

    detail = {"variants": [
        {"id": "a", "name": "32 oz tub", "price_minor": 599, "in_stock": True},
        {"id": "b", "name": "4 x 5.3 oz cups", "price_minor": 359, "in_stock": True},
    ]}  # fmt: skip
    for terms in (["4-pack"], ["pack of 4"], ["4-pack", "5.3 oz cups"], ["5.3 ounces"]):
        pick = _selected_variant(detail, variant_terms=terms)
        assert pick is not None and pick["id"] == "b", terms
    assert _selected_variant(detail, variant_terms=["6-pack"]) is None
