"""Xena's return flow: find the item, price it, pause for the customer, resume with the outcome.

The commerce API is a fake that behaves like the real one for these routes (the real routes are
tested in services/commerce). What's tested here is the assistant's side: the graph pauses on
``propose_return``, only the browser's outcome resumes it, the outcome is re-checked with the
store, and no confirmation token ever enters the conversation or its checkpoints.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Iterator
from typing import Any

import pytest
from alembic import command as alembic_command
from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import InMemorySaver

import assistant.commerce as commerce_mod
import assistant.main as main_mod
from assistant.commerce import CommerceError, Customer, NotSignedIn
from assistant.db import alembic_config

pytestmark = pytest.mark.integration

ALICE = Customer(
    uuid.UUID("11111111-1111-4111-8111-111111111111"), "Alice Example", "alice@example.com"
)
ORDER_ID = "aaaaaaaa-0000-4000-8000-000000000001"
EARBUDS = "bbbbbbbb-0000-4000-8000-000000000002"
HEADPHONES = "bbbbbbbb-0000-4000-8000-000000000003"


class FakeStore:
    """Just enough of the commerce API, with a quote that the 'browser' can confirm."""

    calls: list[tuple[str, str]] = []
    quote_status = "open"
    # The order's delivery: delivered by default; a test can put it back on the road.
    in_transit = False

    def __init__(self, customer_id: uuid.UUID, settings: Any = None) -> None:
        self.customer_id = customer_id

    def close(self) -> None:
        pass

    def _quote(self) -> dict[str, Any]:
        return {
            "id": "cccccccc-0000-4000-8000-000000000004",
            "order_id": ORDER_ID,
            "status": FakeStore.quote_status,
            "lines": [
                {
                    "order_line_id": EARBUDS,
                    "product_title": "Pulse Sport Earbuds",
                    "variant_name": "Graphite",
                    "image_path": "/images/types/earbuds.svg",
                    "policy_class": "inspection",
                    "quantity": 1,
                    "refund_minor": 8659,
                    "refund_timing": "after_inspection",
                    "timing_message": "Refunded after inspection.",
                }
            ],
            "reason": "defective",
            "items_refund_minor": 8659,
            "shipping_refund_minor": 0,
            "total_refund_minor": 8659,
            "currency": "USD",
            "refund_destination": {"card_brand": "visa", "card_last4": "4242"},
            "policy_version": "sandbox-2026-09",
            "needs_shipping": True,
            "expires_at": "2026-09-26T20:00:00Z",
            "return_id": "dddddddd-0000-4000-8000-000000000005"
            if FakeStore.quote_status == "confirmed"
            else None,
        }

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
        FakeStore.calls.append(("GET", path))
        if path == "/v1/catalog/vocabulary":
            return {"product_types": [], "tags": []}
        if path == "/v1/orders":
            return [{"id": ORDER_ID}]
        if path == f"/v1/orders/{ORDER_ID}":
            return {
                "id": ORDER_ID,
                "status": "fulfilling" if FakeStore.in_transit else "delivered",
                "placed_at": "2026-09-20T00:00:00Z",
                "delivered_at": None if FakeStore.in_transit else "2026-09-23T00:00:00Z",
                "estimated_delivery_at": "2026-09-29T22:00:00Z" if FakeStore.in_transit else None,
                "shipping_address": {"line1": "4127 Bluebonnet Ln", "city": "Plano"},
                "payment": {"card_brand": "visa", "card_last4": "4242"},
                "shipments": [
                    {
                        "carrier": "Swiftline Parcel",
                        "service": "2-Day",
                        "tracking_number": "SW136076123317",
                        "status": "in_transit" if FakeStore.in_transit else "delivered",
                        "shipped_at": "2026-09-21T00:00:00Z",
                        "estimated_delivery_at": "2026-09-29T22:00:00Z",
                        "delivered_at": None if FakeStore.in_transit else "2026-09-23T00:00:00Z",
                        "is_simulated": True,
                        "events": [],
                    }
                ],
                "total_minor": 21658,
                "shipping_minor": 0,
                "item_count": 2,
                "lines": [
                    {
                        "id": HEADPHONES,
                        "product_title": "Arc Wireless Over-Ear Headphones",
                        "variant_name": "Midnight",
                        "quantity": 1,
                        "unit_price_minor": 12999,
                        "image_path": "/x.svg",
                    },
                    {
                        "id": EARBUDS,
                        "product_title": "Pulse Sport Earbuds",
                        "variant_name": "Graphite",
                        "quantity": 1,
                        "unit_price_minor": 7999,
                        "image_path": "/y.svg",
                    },
                ],
            }
        if path == f"/v1/orders/{ORDER_ID}/return-options":
            return {
                "order_id": ORDER_ID,
                "policy_version": "sandbox-2026-09",
                "refund_destination": {"card_brand": "visa", "card_last4": "4242"},
                "whole_order_shipping_refund_minor": 0,
                "lines": [
                    {
                        "order_line_id": EARBUDS,
                        "product_title": "Pulse Sport Earbuds",
                        "variant_name": "Graphite",
                        "image_path": "/y.svg",
                        "eligible": True,
                        "reason": "within_window",
                        "returnable_quantity": 1,
                        "returned_quantity": 0,
                        "max_refund_minor": 8659,
                        "refund_timing": "after_inspection",
                        "message": "Refunded after inspection.",
                    },
                ],
            }
        if path.startswith("/v1/returns/quotes/"):
            return self._quote()
        if path == "/v1/returns":
            return (
                [
                    {
                        "id": "dddddddd-0000-4000-8000-000000000005",
                        "rma_number": "R-DDDDDDDD",
                        "status": "authorized",
                        "created_at": "2026-09-26T19:00:00Z",
                        "items": [],
                        "refund": None,
                    }
                ]
                if FakeStore.quote_status == "confirmed"
                else []
            )
        raise AssertionError(f"unexpected GET {path}")

    def post(self, path: str, body: dict[str, Any]) -> Any:
        FakeStore.calls.append(("POST", path))
        if path == "/v1/returns/quote":
            assert body["lines"] == [{"order_line_id": EARBUDS, "quantity": 1}]
            assert body["reason"] == "defective"  # read from the conversation by Jev (simulator)
            return self._quote()
        raise CommerceError(404, f"unexpected POST {path}")


@pytest.fixture(scope="session", autouse=True)
def _migrated() -> None:
    alembic_command.upgrade(alembic_config(), "head")


@pytest.fixture
def saver() -> InMemorySaver:
    return InMemorySaver()


@pytest.fixture
def alice(monkeypatch: pytest.MonkeyPatch, saver: InMemorySaver) -> Iterator[TestClient]:
    def fake_resolve(token: str | None, settings: Any = None) -> Customer:
        if token != "alice-session":
            raise NotSignedIn
        return ALICE

    monkeypatch.setattr(main_mod, "resolve_customer", fake_resolve)
    monkeypatch.setattr(main_mod, "CommerceClient", FakeStore)
    monkeypatch.setattr(commerce_mod, "_vocabulary", None)
    FakeStore.calls = []
    FakeStore.quote_status = "open"
    FakeStore.in_transit = False
    with TestClient(main_mod.create_app(checkpointer=saver)) as client:
        client.cookies.set("ac_session", "alice-session")
        yield client


def events(body: str) -> list[tuple[str, Any]]:
    out = []
    for block in body.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        out.append((lines["event"], json.loads(lines["data"])))
    return out


def text_of(evs: list[tuple[str, Any]]) -> str:
    return "".join(d["delta"] for e, d in evs if e == "text")


def start_return(alice: TestClient) -> tuple[str, dict[str, Any]]:
    conv = alice.post("/v1/assistant/conversations", json={"agent": "xana"}).json()
    evs = events(
        alice.post(
            f"/v1/assistant/conversations/{conv['id']}/messages",
            json={"text": "I want to return my earbuds, they stopped working"},
        ).text
    )
    tools = [d["tool"] for e, d in evs if e == "status"]
    assert tools == ["list_my_orders", "get_return_options", "quote_return", "propose_return"]
    quote = next(d for e, d in evs if e == "quote")
    return conv["id"], quote


def test_a_return_pauses_for_the_customer_and_resumes_confirmed(
    alice: TestClient, saver: InMemorySaver
) -> None:
    conv_id, quote = start_return(alice)
    assert quote["kind"] == "return_quote" and quote["total_refund_minor"] == 8659
    # The read-back is built by code from the quote: item, amount, destination, timing.
    assert quote["readback"].startswith("Here's your return: 1 × Pulse Sport Earbuds (Graphite).")
    assert "$86.59" in quote["readback"] and "Visa ending in 4242" in quote["readback"]

    detail = alice.get(f"/v1/assistant/conversations/{conv_id}").json()
    assert detail["pending_quote"]["quote_id"] == quote["quote_id"]

    # A typed "yes" doesn't confirm: it points to the button and keeps the quote waiting.
    typed = events(
        alice.post(f"/v1/assistant/conversations/{conv_id}/messages", json={"text": "yes"}).text
    )
    assert "tap Confirm return" in text_of(typed)
    assert alice.get(f"/v1/assistant/conversations/{conv_id}").json()["pending_quote"] is not None

    # The browser confirmed with the store; the assistant resumes and checks with the store.
    FakeStore.quote_status = "confirmed"
    resumed = events(
        alice.post(
            f"/v1/assistant/conversations/{conv_id}/resume",
            json={"quote_id": quote["quote_id"], "outcome": "confirmed"},
        ).text
    )
    assert "Return R-DDDDDDDD is confirmed" in text_of(resumed)
    assert any(
        e == "card" and d["kind"] == "return_status" and d["outcome"] == "confirmed"
        for e, d in resumed
    )
    assert alice.get(f"/v1/assistant/conversations/{conv_id}").json()["pending_quote"] is None

    # The assistant never asked the store for a confirmation token or to confirm.
    assert not [p for _, p in FakeStore.calls if "confirm" in p]
    # And nothing token-like is in the conversation's saved state.
    dump = json.dumps([list(v) for v in saver.storage.values()], default=str)
    assert "confirmation_token" not in dump and "token_hash" not in dump


def test_the_store_decides_what_happened_not_the_resume_message(alice: TestClient) -> None:
    conv_id, quote = start_return(alice)
    # The browser claims "confirmed", but the store says the quote is still open.
    resumed = events(
        alice.post(
            f"/v1/assistant/conversations/{conv_id}/resume",
            json={"quote_id": quote["quote_id"], "outcome": "confirmed"},
        ).text
    )
    assert "nothing was returned" in text_of(resumed).lower()
    assert not any(d.get("outcome") == "confirmed" for e, d in resumed if e == "card")


def test_resume_needs_the_waiting_quote(alice: TestClient) -> None:
    conv_id, _ = start_return(alice)
    wrong = alice.post(
        f"/v1/assistant/conversations/{conv_id}/resume",
        json={"quote_id": str(uuid.uuid4()), "outcome": "confirmed"},
    )
    assert wrong.status_code == 409


def test_moving_on_closes_the_quote_quietly(alice: TestClient) -> None:
    conv_id, _ = start_return(alice)
    evs = events(
        alice.post(
            f"/v1/assistant/conversations/{conv_id}/messages",
            json={"text": "actually where's my refund?"},
        ).text
    )
    assert [d["tool"] for e, d in evs if e == "status"] == ["get_refund_status"]
    detail = alice.get(f"/v1/assistant/conversations/{conv_id}").json()
    assert detail["pending_quote"] is None
    assert [m["role"] for m in detail["messages"]].count("assistant") == 2


def test_voice_confirmation_is_checked_by_the_app(alice: TestClient) -> None:
    conv_id, quote = start_return(alice)
    base = {
        "conversation_id": conv_id,
        "quote_id": quote["quote_id"],
        "final": True,
        "readback_complete": True,
        "speech_ms": 800,
    }
    ok = alice.post(
        "/v1/assistant/voice/confirm-check", json={**base, "text": "yes, confirm"}
    ).json()
    assert ok["decision"] == "yes"
    for text in ("mm-hmm", "yeah maybe", "yes but"):
        assert (
            alice.post("/v1/assistant/voice/confirm-check", json={**base, "text": text}).json()[
                "decision"
            ]
            == "unclear"
        )
    cut_off = alice.post(
        "/v1/assistant/voice/confirm-check",
        json={**base, "text": "yes", "readback_complete": False},
    ).json()
    assert cut_off["decision"] == "unclear"
    assert (
        alice.post("/v1/assistant/voice/confirm-check", json={**base, "text": "no"}).json()[
            "decision"
        ]
        == "no"
    )


def test_a_case_follow_up_answers_about_the_named_order(
    alice: TestClient, saver: InMemorySaver
) -> None:
    """The Support page's "Continue with Xena" message names the order; Xena answers about its
    delivery (from the store's shipment data), not with a list of recent orders."""
    FakeStore.in_transit = True
    conv = alice.post("/v1/assistant/conversations", json={"agent": "xana"}).json()
    evs = events(
        alice.post(
            f"/v1/assistant/conversations/{conv['id']}/messages",
            json={
                "text": 'I\'m following up on my request CS-48461 ("When will my order arrive?") '
                "about order 00000001."
            },
        ).text
    )
    assert [d["tool"] for e, d in evs if e == "status"] == ["get_order_status"]
    answer = text_of(evs)
    assert answer.startswith("About your request CS-48461: Order #00000001")
    assert "Swiftline Parcel" in answer and "arrive by Tue, Sep 29" in answer
    assert [d["id"] for e, d in evs if e == "card" and d["kind"] == "order"] == [ORDER_ID]
    # The number was resolved from Alice's own order list; the address and card never reach
    # the model's context.
    assert ("GET", "/v1/orders") in FakeStore.calls
    dump = json.dumps([list(v) for v in saver.storage.values()], default=str)
    assert "Bluebonnet" not in dump and "4242" not in dump
