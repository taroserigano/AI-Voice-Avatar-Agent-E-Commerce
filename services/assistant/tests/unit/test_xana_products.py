"""Xana's product answers use the same catalog tools as Steph and stay within their facts."""

from __future__ import annotations

from typing import Any

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

import assistant.commerce as commerce_mod
from assistant.scripted import ScriptedChatModel
from assistant.tools import ToolContext, search_products, untrusted
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
