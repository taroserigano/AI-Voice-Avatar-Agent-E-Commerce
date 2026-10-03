"""A named order ("about order E2EA6BC6") is looked up and answered about, not the recent list.

The scripted model's routing and answers, and the order-status tool's resolution of a number to
one of the signed-in customer's own orders. No services: the commerce API is a small fake.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from assistant.commerce import CommerceError
from assistant.scripted import ScriptedChatModel, plan, read_payload
from assistant.scripted_support import named_order_number, plan_support
from assistant.tools import STEPH_TOOLS, ToolContext, _order_for_model, get_order_status
from assistant.toolsets import XANA_TOOLS

ORDER_ID = "4aad7749-58ca-5052-820d-2ff0e2ea6bc6"  # order number E2EA6BC6
OTHER_ID = "4efd4a37-1b2e-5a8c-9e0f-f837e303b415"  # order number E303B415
FOLLOW_UP = (
    'I\'m following up on my request CS-48461 ("When will my order arrive?") about order E2EA6BC6.'
)


def in_transit_order() -> dict[str, Any]:
    """GET /v1/orders/{id} for an order on its way (the shape the commerce API returns)."""
    return {
        "id": ORDER_ID,
        "status": "fulfilling",
        "placed_at": "2026-09-25T17:22:51-05:00",
        "delivered_at": None,
        "estimated_delivery_at": "2026-09-29T17:22:51-05:00",
        "total_minor": 6493,
        "shipping_minor": 0,
        "item_count": 2,
        "shipping_address": {
            "name": "Alice Rivera",
            "line1": "4127 Bluebonnet Ln",
            "line2": "Apt 2B",
            "city": "Plano",
            "state": "TX",
            "postal_code": "75023",
            "country": "US",
            "is_sample": True,
        },
        "payment": {"card_brand": "visa", "card_last4": "4242", "amount_minor": 6493},
        "lines": [
            {
                "id": "2d2bc9cc-3506-5269-9758-88e6b1360a61",
                "product_title": "Grip Yoga Mat, 6 mm",
                "variant_name": "Seafoam",
                "quantity": 1,
                "unit_price_minor": 3999,
                "image_path": "/a.svg",
            },
            {
                "id": "6b8a6f8b-5718-578c-a764-6038cccf1f4f",
                "product_title": "Resistance Band Set, 5 Levels",
                "variant_name": "Standard",
                "quantity": 1,
                "unit_price_minor": 1999,
                "image_path": "/b.svg",
            },
        ],
        "shipments": [
            {
                "carrier": "Swiftline Parcel",
                "service": "2-Day",
                "tracking_number": "SW136076123317",
                "status": "in_transit",
                "shipped_at": "2026-09-26T02:22:51-05:00",
                # 03:00 UTC on the 30th is still the 29th at the store (America/Chicago).
                "estimated_delivery_at": "2026-09-30T03:00:00Z",
                "delivered_at": None,
                "is_simulated": True,
                "events": [
                    {
                        "occurred_at": "2026-09-26T02:22:51-05:00",
                        "status": "in_transit",
                        "description": "Picked up by Swiftline Parcel",
                        "location": "Serigan Mart Fulfillment Center, Fort Worth, TX",
                    },
                    {
                        "occurred_at": "2026-09-26T12:22:51-05:00",
                        "status": "in_transit",
                        "description": "Arrived at sort facility",
                        "location": "Dallas, TX",
                    },
                ],
            }
        ],
        "returns": [],
    }


def delivered_order() -> dict[str, Any]:
    order = in_transit_order()
    order |= {"id": OTHER_ID, "status": "delivered", "delivered_at": "2026-09-23T15:00:00Z"}
    order["estimated_delivery_at"] = None
    order["shipments"][0] |= {"status": "delivered", "delivered_at": "2026-09-23T15:00:00Z"}
    return order


class FakeClient:
    """The signed-in customer's orders only, like the commerce API (404 for anyone else's)."""

    def __init__(self) -> None:
        self.orders = {ORDER_ID: in_transit_order(), OTHER_ID: delivered_order()}
        self.paths: list[str] = []

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
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
        if path == "/v1/orders":
            return [{"id": oid} for oid in self.orders]
        oid = path.removeprefix("/v1/orders/")
        if oid in self.orders:
            return self.orders[oid]
        raise CommerceError(404, "Order not found")


def run_tool(client: FakeClient, **args: Any) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    ctx = ToolContext(client=client, agent="xana")  # type: ignore[arg-type]
    msg = get_order_status.invoke(
        {"type": "tool_call", "id": "c1", "name": "get_order_status", "args": args},
        config={"configurable": {"ctx": ctx}},
    )
    return read_payload(str(msg.content)), list(msg.artifact or [])


def tool_names(tools: list[Any]) -> list[str]:
    return [t.name for t in tools]


# --- Reading the order number -------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "number"),
    [
        (FOLLOW_UP, "E2EA6BC6"),
        ("where is order #e2ea6bc6?", "E2EA6BC6"),
        ("order number E2EA6BC6 hasn't come", "E2EA6BC6"),
        ("has E2EA6BC6 shipped yet", "E2EA6BC6"),
        ("when will my order arrive?", None),
        ("my order from 20260925 is late", None),  # a date, not an order number
        ("I got a DEFACED box", None),
        ("where is my refund for order R-DDDDDDDD", None),
    ],
)
def test_order_numbers_are_read_in_the_sites_form(text: str, number: str | None) -> None:
    assert named_order_number(text) == number


# --- Routing -----------------------------------------------------------------------------


def test_a_case_follow_up_looks_up_the_named_order_not_the_recent_list() -> None:
    calls = plan_support(FOLLOW_UP, {})
    assert calls is not None
    assert [(c["name"], c["args"]) for c in calls] == [
        ("get_order_status", {"order_number": "E2EA6BC6"})
    ]

    model = ScriptedChatModel()
    msg = model.invoke([HumanMessage(FOLLOW_UP)], agent="xana", tool_names=tool_names(XANA_TOOLS))
    assert [c["name"] for c in msg.tool_calls] == ["get_order_status"]
    assert msg.tool_calls[0]["args"] == {"order_number": "E2EA6BC6"}


def test_returns_and_refunds_still_win_over_a_named_order() -> None:
    ret = plan_support("I want to return my yoga mat from order E2EA6BC6", {})
    assert ret is not None and [c["name"] for c in ret] == ["list_my_orders"]
    refund = plan_support("where's my refund for order E2EA6BC6?", {})
    assert refund is not None and [c["name"] for c in refund] == ["get_refund_status"]
    # Without a number, "when will my order arrive?" is still about the recent orders.
    assert plan_support("when will my order arrive?", {}) is None


def test_steph_also_looks_up_a_named_order() -> None:
    tools = set(tool_names(STEPH_TOOLS))
    calls = plan("where is order E2EA6BC6?", [], {}, tools)
    assert [(c["name"], c["args"]) for c in calls] == [
        ("get_order_status", {"order_number": "E2EA6BC6"})
    ]


# --- The tool ----------------------------------------------------------------------------


def test_the_tool_resolves_a_number_among_the_customers_own_orders() -> None:
    client = FakeClient()
    data, cards = run_tool(client, order_number="e2ea6bc6")
    assert data["order_id"] == ORDER_ID and data["order_number"] == "E2EA6BC6"
    assert [c["id"] for c in cards] == [ORDER_ID]
    # It found the id in the customer's own order list, then read that order.
    assert client.paths == ["/v1/orders", f"/v1/orders/{ORDER_ID}"]


def test_a_number_that_isnt_on_the_account_is_not_found() -> None:
    data, cards = run_tool(FakeClient(), order_number="ABCD1234")
    assert data["status"] == 404 and cards == []
    data, cards = run_tool(FakeClient(), order_number="not a number")
    assert "error" in data and cards == []
    data, cards = run_tool(FakeClient())
    assert "error" in data and cards == []


def test_the_model_sees_delivery_and_tracking_but_no_address_or_payment() -> None:
    seen = _order_for_model(in_transit_order())
    assert seen["arriving_by"] == "Tue, Sep 29"
    assert seen["delivery"] == {
        "status": "In transit",
        "carrier": "Swiftline Parcel",
        "service": "2-Day",
        "tracking_number": "SW136076123317",
        "shipped_on": "Sat, Sep 26",
        "arriving_by": "Tue, Sep 29",
        "delivered_on": None,
        "latest_update": "Arrived at sort facility",
        "simulated_tracking": True,
        "parcels": 1,
    }
    dump = json.dumps(seen)
    for private in ("Bluebonnet", "75023", "Plano", "Alice", "4242", "visa", "Dallas", "Fort"):
        assert private not in dump, private
    assert _order_for_model({**in_transit_order(), "shipments": []})["delivery"] is None


# --- Answers -----------------------------------------------------------------------------


def answer_for(text: str, detail: dict[str, Any] | None, *, agent: str = "xana") -> str:
    from assistant.tools import untrusted

    payload = _order_for_model(detail) if detail else {"error": "no order", "status": 404}
    call = {"name": "get_order_status", "args": {"order_number": "X"}, "id": "c1"}
    msgs = [
        HumanMessage(text),
        AIMessage("", tool_calls=[call]),
        ToolMessage(untrusted("get_order_status", payload), tool_call_id="c1", name=call["name"]),
    ]
    tools = tool_names(XANA_TOOLS if agent == "xana" else STEPH_TOOLS)
    return str(ScriptedChatModel().invoke(msgs, agent=agent, tool_names=tools).content)


def test_the_follow_up_answer_is_about_that_orders_delivery() -> None:
    answer = answer_for(FOLLOW_UP, in_transit_order())
    assert answer.startswith("About your request CS-48461: Order #E2EA6BC6")
    assert "on its way with Swiftline Parcel 2-Day" in answer
    assert "should arrive by Tue, Sep 29" in answer
    assert "SW136076123317" in answer
    assert "E303B415" not in answer  # no other orders


def test_delivered_and_missing_orders_are_answered_plainly() -> None:
    delivered = answer_for("did order E303B415 arrive?", delivered_order())
    assert delivered == (
        "Order #E303B415 (Grip Yoga Mat, 6 mm and 1 more) was delivered by Swiftline Parcel "
        "on Wed, Sep 23."
    )
    missing = answer_for("where is order ABCD1234?", None)
    assert "couldn't find order ABCD1234 on your account" in missing
    # Steph writes the same delivery answer.
    assert "should arrive by Tue, Sep 29" in answer_for(
        "where is order E2EA6BC6?", in_transit_order(), agent="steph"
    )
