"""Xena's voice brain over her real support tools, with a scripted model and a fake store."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Iterator
from datetime import date
from typing import Any

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langgraph.checkpoint.memory import InMemorySaver

from ai_commerce_voice.brain import (
    XanaBrain,
    build_voice_graph,
    make_context,
    orders_snapshot,
    system_prompt,
)
from ai_commerce_voice.ports import CardOut, QuoteOut, TextDelta, ToolStarted, TurnEnded
from assistant.tools import ToolContext

ORDER_ID = "00000000-0000-4000-8000-0000e2ea6bc6"
QUOTE_ID = str(uuid.UUID(int=7))


def order(status: str = "fulfilling") -> dict[str, Any]:
    return {
        "id": ORDER_ID,
        "status": status,
        "item_count": 2,
        "placed_at": "2026-09-20T15:00:00Z",
        "delivered_at": None,
        "estimated_delivery_at": "2026-09-30T20:00:00Z",
        "total_minor": 2599,
        "shipping_minor": 599,
        "lines": [
            {
                "id": "11111111-1111-4111-8111-111111111111",
                "product_title": "Oat milk",
                "variant_name": "64 oz",
                "quantity": 2,
                "unit_price_minor": 499,
                "image_path": "/images/products/oat-milk.webp",
            }
        ],
        "shipments": [],
    }


class FakeStore:
    """The commerce API as the tools see it (acting for one customer)."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.quote_status = "open"

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        self.calls.append(path)
        if path == "/v1/orders":
            return [{"id": ORDER_ID}]
        if path == "/v1/policies/search":
            return {
                "results": [
                    {
                        "cite": "returns-and-refunds#rr-4-1",
                        "doc_title": "Returns and refunds",
                        "number": "4.1",
                        "title": "Standard items",
                        "version": "2026-09",
                        "url": "/returns-policy#rr-4-1",
                        "body": "Send items back with everything that came with them. "
                        "Opened items are fine.",
                    }
                ]
            }
        if path == f"/v1/orders/{ORDER_ID}":
            return order()
        if path == f"/v1/orders/{ORDER_ID}/return-options":
            # The read-back says units returned before; none here.
            return {
                "lines": [
                    {
                        "order_line_id": "11111111-1111-4111-8111-111111111111",
                        "returned_quantity": 0,
                    }
                ]
            }
        if path == f"/v1/returns/quotes/{QUOTE_ID}":
            return {
                "id": QUOTE_ID,
                "order_id": ORDER_ID,
                "status": self.quote_status,
                "return_id": None,
                "lines": [
                    {
                        "order_line_id": "11111111-1111-4111-8111-111111111111",
                        "product_title": "Oat milk",
                        "variant_name": "64 oz",
                        "image_path": None,
                        "quantity": 1,
                        "refund_minor": 499,
                        "refund_timing": "no_return_needed",
                        "timing_message": "",
                    }
                ],
                "items_refund_minor": 499,
                "shipping_refund_minor": 0,
                "total_refund_minor": 499,
                "currency": "USD",
                "refund_destination": {"type": "card", "brand": "visa", "last4": "4242"},
                "needs_shipping": False,
                "expires_at": "2026-09-26T23:00:00Z",
                "policy_version": "v1",
            }
        raise AssertionError(f"unexpected GET {path}")

    def close(self) -> None:
        return None


class ScriptModel(BaseChatModel):
    """Streams scripted replies; a reply is text or a tool call. Records what it was shown."""

    replies: list[Any]
    seen: list[list[BaseMessage]] = []

    @property
    def _llm_type(self) -> str:
        return "script"

    def bind_tools(self, tools: Any, **kwargs: Any) -> ScriptModel:
        return self

    def _next(self, messages: list[BaseMessage]) -> AIMessage:
        self.seen.append(list(messages))
        reply = self.replies.pop(0)
        if isinstance(reply, str):
            return AIMessage(content=reply, id=f"ai-{len(self.seen)}")
        name, args = reply
        return AIMessage(
            content="",
            id=f"ai-{len(self.seen)}",
            tool_calls=[
                {"name": name, "args": args, "id": f"call-{len(self.seen)}", "type": "tool_call"}
            ],
        )

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        return ChatResult(generations=[ChatGeneration(message=self._next(messages))])

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        if self.replies and isinstance(self.replies[0], tuple) and self.replies[0][0] == "fail":
            # Says these words, then the connection drops (e.g. an OpenAI timeout).
            _, words = self.replies.pop(0)
            self.seen.append(list(messages))
            for word in words.split():
                yield ChatGenerationChunk(message=AIMessageChunk(content=word + " ", id="ai-x"))
            raise TimeoutError("Request timed out.")
        msg = self._next(messages)
        if msg.tool_calls:
            call = msg.tool_calls[0]
            import json

            yield ChatGenerationChunk(
                message=AIMessageChunk(
                    content="",
                    id=msg.id,
                    tool_call_chunks=[
                        {
                            "name": call["name"],
                            "args": json.dumps(call["args"]),
                            "id": call["id"],
                            "index": 0,
                        }
                    ],
                )
            )
            return
        for word in str(msg.content).split(" "):
            yield ChatGenerationChunk(message=AIMessageChunk(content=word + " ", id=msg.id))


def brain_with(replies: list[Any]) -> tuple[XanaBrain, FakeStore, ScriptModel]:
    store = FakeStore()
    model = ScriptModel(replies=replies, seen=[])
    snapshot = orders_snapshot([order()])
    ctx = ToolContext(client=store, agent="xana", first_name="Alice", voice=True)  # type: ignore[arg-type]
    brain = XanaBrain(
        build_voice_graph(InMemorySaver()),
        conversation_id="conv-1",
        ctx=ctx,
        voice=make_context(
            model,
            system=system_prompt("Alice", date(2026, 9, 26), snapshot),
            max_tool_calls=6,
        ),
        model="script",
        simulated=True,
    )
    return brain, store, model


async def collect(it: Any) -> list[Any]:
    return [ev async for ev in it]


def test_a_tool_call_is_announced_as_soon_as_its_name_streams_and_the_answer_follows() -> None:
    brain, store, _ = brain_with(
        [("get_order_status", {"order_number": "E2EA6BC6"}), "It arrives Wednesday, September 30."]
    )
    events = asyncio.run(collect(brain.turn("Where's order E two E A six B C six?")))

    kinds = [type(e).__name__ for e in events]
    assert kinds[0] == "ToolStarted"  # before the call finished, so the filler can start
    assert [e.name for e in events if isinstance(e, ToolStarted)] == ["get_order_status"]  # once
    assert any(isinstance(e, CardOut) and e.card["kind"] == "order" for e in events)
    text = "".join(e.text for e in events if isinstance(e, TextDelta))
    assert text.strip() == "It arrives Wednesday, September 30."
    end = events[-1]
    assert isinstance(end, TurnEnded) and end.error is None and end.first_token_ms is not None
    assert f"/v1/orders/{ORDER_ID}" in store.calls


def test_a_failure_after_she_answered_ends_the_turn_without_an_error() -> None:
    # Found live (2026-10-02): an OpenAI timeout after a full answer put "something went
    # wrong" under it.
    brain, _, _ = brain_with([("fail", "We have 34 milk products.")])
    events = asyncio.run(collect(brain.turn("How many kinds of milk do you have?")))
    assert "34 milk" in "".join(e.text for e in events if isinstance(e, TextDelta))
    end = events[-1]
    assert isinstance(end, TurnEnded) and end.error is None


def test_a_stall_before_any_answer_is_retried_once() -> None:
    """Found by the golden eval: an OpenAI read timeout before the first word failed the turn."""
    brain, _, model = brain_with([("fail", ""), "We have 34 milk products."])
    events = asyncio.run(collect(brain.turn("How many kinds of milk do you have?")))
    assert "34 milk" in "".join(e.text for e in events if isinstance(e, TextDelta))
    end = events[-1]
    assert isinstance(end, TurnEnded) and end.error is None
    assert len(model.seen) == 2


def test_a_second_failure_before_any_answer_still_says_so() -> None:
    brain, _, _ = brain_with([("fail", ""), ("fail", "")])
    end = asyncio.run(collect(brain.turn("How many kinds of milk do you have?")))[-1]
    assert isinstance(end, TurnEnded) and end.error and "went wrong" in end.error


def test_the_catalog_size_is_in_the_prompt() -> None:
    vocab = {
        "product_types": [
            {"value": "milk", "label": "Milk", "count": 34},
            {"value": "tv", "label": "TV", "count": 8},
        ],
        "tags": [],
    }
    system = system_prompt("Alice", date(2026, 9, 26), None, vocab)
    assert "42 products" in system and "milk 34" in system and "tv 8" in system


def test_the_model_sees_the_recent_orders_snapshot_as_untrusted_data() -> None:
    brain, _, model = brain_with(["It shipped and arrives Wednesday."])
    asyncio.run(collect(brain.turn("Where's my oat milk?")))
    system = str(model.seen[0][0].content)
    assert '<untrusted_data source="orders_snapshot">' in system
    assert "Oat milk" in system and "E2EA6BC6" in system
    assert "4242" not in system  # no payment details in what the model reads


def test_a_restarted_turn_replaces_its_draft_message_instead_of_adding_one() -> None:
    brain, _, model = brain_with(["first", "second"])

    async def t() -> None:
        await collect(brain.turn("Where's my refill", message_id="item-9"))
        await collect(brain.turn("Where's my refund?", message_id="item-9"))

    asyncio.run(t())
    humans = [m for m in model.seen[1] if m.type == "human"]
    assert [m.content for m in humans] == ["Where's my refund?"]


def test_a_proposed_return_pauses_on_the_quote_and_only_the_store_says_it_was_confirmed() -> None:
    brain, store, _ = brain_with(
        [("propose_return", {"quote_id": QUOTE_ID}), "Okay, nothing was returned."]
    )
    events = asyncio.run(collect(brain.turn("Return one oat milk, it was spoiled.")))
    (quote,) = [e.quote for e in events if isinstance(e, QuoteOut)]
    assert (
        quote["quote_id"] == QUOTE_ID
        and "Do you want me to confirm this return?" in quote["readback"]
    )
    assert asyncio.run(brain.pending_quote()) is not None

    # The browser says "confirmed", but the store says the quote is still open: not confirmed.
    events = asyncio.run(collect(brain.resume("confirmed")))
    graph_state = asyncio.run(brain.graph.aget_state({"configurable": {"thread_id": "conv-1"}}))
    tool_results = [m for m in graph_state.values["messages"] if isinstance(m, ToolMessage)]
    assert '"outcome": "declined"' in str(tool_results[-1].content)
    assert asyncio.run(brain.pending_quote()) is None


def test_a_policy_question_is_answered_in_one_model_call_from_prefetched_sections() -> None:
    brain, store, model = brain_with(
        ["Opened items are fine to return. [[cite:returns-and-refunds#rr-4-1]]"]
    )
    events = asyncio.run(collect(brain.turn("Can I return opened headphones?", message_id="m1")))

    assert len(model.seen) == 1  # no tool round trip
    shown = model.seen[0]
    assert [m.type for m in shown[-3:]] == ["human", "ai", "tool"]
    assert "Opened items are fine" in str(shown[-1].content)
    end = events[-1]
    assert isinstance(end, TurnEnded)
    assert [c["cite"] for c in end.citations] == ["returns-and-refunds#rr-4-1"]
    # The prefetch shows on screen as a step; the model itself made no tool call.
    assert [e.name for e in events if isinstance(e, ToolStarted)] == ["search_policies"]


def test_an_order_question_skips_the_policy_prefetch() -> None:
    brain, store, model = brain_with(["It arrives Wednesday."])
    asyncio.run(collect(brain.turn("When does my oat milk arrive?")))
    assert "/v1/policies/search" not in store.calls
    assert model.seen[0][-1].type == "human"
