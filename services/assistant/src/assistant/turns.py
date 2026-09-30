"""Running one chat turn and turning it into server-sent events; rebuilding history for display.

Events (``event: <name>`` / ``data: <json>``):

- ``signals``  Jev's typed read of the turn (intent, confidence, simulated or not)
- ``status``   ``{"tool": "search_products", "label": "Searching the catalog…"}``
- ``text``     ``{"delta": "..."}``  (append to the answer)
- ``card``     a product / order / store / cart / handoff / return card from a tool result
- ``quote``    a return quote waiting for the customer's own confirmation (the turn
               pauses here; the browser confirms with the store, then resumes)
- ``citations`` ``{"valid": [CitationCard...], "invalid": ["doc#section", ...]}``
- ``done``     ``{"model": "...", "simulated": bool, "prompt_version": "..."}``
- ``error``    ``{"message": "..."}``

Citations: the answer marks them inline as ``[[cite:<doc>#<section>]]``. A marker is valid only
if a ``search_policies`` result in the same turn returned that section; invalid ones are
reported (and the browser drops them), so the assistant can't cite a policy it didn't read.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Iterator
from typing import Any, cast

from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    ToolMessage,
)
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from assistant.models import choose_model
from assistant.prompts import prompt_version
from assistant.schemas import CitationCard, MessageOut
from assistant.tools import ToolContext

log = logging.getLogger(__name__)

CITE = re.compile(r"\[\[cite:([a-z0-9-]+(?:#[a-z]{2}(?:-\d+)+)?)\]\]")
# A whole-document citation sometimes comes back as "doc#doc": it means the document.
DOC_AS_SECTION = re.compile(r"\[\[cite:([a-z0-9-]+)#\1\]\]")
TOOL_LABELS = {
    "search_products": "Searching the catalog…",
    "get_product_details": "Reading the product details…",
    "add_to_cart": "Adding to your cart…",
    "list_my_orders": "Looking up your orders…",
    "get_order_status": "Checking your order…",
    "list_stores": "Finding stores…",
    "search_policies": "Checking our policies…",
    "handoff_to_person": "Opening a support case…",
    "suggest_xana": "Finding the right help…",
    "get_return_options": "Checking what can be returned…",
    "quote_return": "Pricing your return…",
    "propose_return": "Preparing your quote…",
    "get_refund_status": "Checking your refunds…",
}


def sse(event: str, data: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str, ensure_ascii=False)}\n\n"


def message_text(message: BaseMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    return "".join(
        block.get("text", "") if isinstance(block, dict) and block.get("type") == "text" else ""
        for block in content
    )


def split_citations(
    text: str, citable: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[str]]:
    valid: dict[str, dict[str, Any]] = {}
    invalid: list[str] = []
    text = DOC_AS_SECTION.sub(r"[[cite:\1]]", text)
    for cite in CITE.findall(text):
        if cite in citable:
            valid.setdefault(cite, citable[cite])
        elif cite not in invalid:
            invalid.append(cite)
    return list(valid.values()), invalid


class ProductCards:
    """Which product cards a turn shows: every product read in detail, then the results of the
    turn's last catalog search. Earlier searches that the assistant refined away (a broad
    keyword search before the verified one) were near misses and stay off the screen."""

    def __init__(self) -> None:
        self.search: list[dict[str, Any]] = []
        self.details: list[dict[str, Any]] = []

    def take(self, tool: str | None, cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Keep this tool's product cards for the end of the turn; return the others now."""
        if tool == "search_products":
            self.search = list(cards)
            return []
        if tool == "get_product_details":
            self.details += cards
            return []
        return cards

    def final(self) -> list[dict[str, Any]]:
        summary = [c for c in self.search if c.get("kind") != "product"]
        out: list[dict[str, Any]] = []
        seen: set[str] = set()
        for card in [*self.details, *self.search]:
            if card.get("kind") == "product" and card.get("id") not in seen:
                seen.add(card["id"])
                out.append(card)
        return summary + out


def run_turn(
    graph: CompiledStateGraph,  # type: ignore[type-arg]
    *,
    conversation_id: str,
    agent: str,
    ctx: ToolContext,
    text: str | None = None,
    resume: dict[str, Any] | None = None,
) -> Iterator[str]:
    """Run a customer message (``text``) or resume a paused turn (``resume``) as SSE."""
    choice = choose_model()
    config: RunnableConfig = {
        "configurable": {"thread_id": conversation_id, "ctx": ctx},
        "recursion_limit": 20,
        "metadata": {"agent": agent, "prompt_version": prompt_version(agent), "model": choice.name},
        "run_name": f"{agent}-turn",
    }
    answer: list[str] = []
    citable: dict[str, dict[str, Any]] = {}
    products = ProductCards()
    current_id: str | None = None
    # Text streamed during the current agent step: its final message repeats it, and the
    # Responses API gives the chunks and the final message different ids.
    streamed_this_step = False

    def emit_text(message_id: str | None, delta: str) -> Iterator[str]:
        nonlocal current_id
        if not delta:
            return
        if message_id != current_id and answer:
            answer.append("\n\n")
            yield sse("text", {"delta": "\n\n"})
        current_id = message_id
        answer.append(delta)
        yield sse("text", {"delta": delta})

    try:
        graph_input: Any = (
            Command(resume=resume)
            if resume is not None
            else {"messages": [HumanMessage(content=text or "")], "agent": agent}
        )
        stream = graph.stream(graph_input, config, stream_mode=["messages", "updates"])
        for mode, chunk in cast(Iterator[tuple[str, Any]], stream):
            if mode == "messages":
                message, meta = chunk
                if meta.get("langgraph_node") == "agent" and isinstance(message, AIMessageChunk):
                    delta = message_text(message)
                    if delta:
                        streamed_this_step = True
                    yield from emit_text(message.id, delta)
                continue
            for node, update in (chunk or {}).items():
                if node == "__interrupt__":
                    for pending in update:
                        yield sse("quote", pending.value)
                    continue
                if node == "route" and update and update.get("signals"):
                    yield sse("signals", update["signals"])
                for message in (update or {}).get("messages", []):
                    if isinstance(message, AIMessage):
                        for call in message.tool_calls:
                            label = TOOL_LABELS.get(call["name"], "Working on it…")
                            yield sse("status", {"tool": call["name"], "label": label})
                        if not streamed_this_step:
                            yield from emit_text(message.id, message_text(message))
                        streamed_this_step = False
                    elif isinstance(message, ToolMessage):
                        cards = []
                        for card in message.artifact or []:
                            if card.get("kind") == "citation":
                                citable[card["cite"]] = card
                            else:
                                cards.append(card)
                        for card in products.take(message.name, cards):
                            yield sse("card", card)
    except Exception:
        log.exception("assistant turn failed")
        yield sse(
            "error", {"message": "Sorry, something went wrong on our side. Please try again."}
        )
        return

    for card in products.final():
        yield sse("card", card)
    valid, invalid = split_citations("".join(answer), citable)
    if invalid:
        log.warning("answer cited sections it didn't retrieve: %s", invalid)
    yield sse("citations", {"valid": valid, "invalid": invalid})
    yield sse(
        "done",
        {
            "model": choice.name,
            "simulated": choice.simulated,
            "prompt_version": prompt_version(agent),
        },
    )


def pending_quote(graph: CompiledStateGraph, conversation_id: str) -> dict[str, Any] | None:  # type: ignore[type-arg]
    """The quote this conversation is paused on, waiting for the customer, if any."""
    snapshot = graph.get_state({"configurable": {"thread_id": conversation_id}})
    for pending in getattr(snapshot, "interrupts", ()) or ():
        value = getattr(pending, "value", None)
        if isinstance(value, dict) and value.get("kind") == "return_quote":
            return value
    return None


def history(messages: list[BaseMessage]) -> list[MessageOut]:
    """The conversation as the customer saw it: their messages, and one answer per turn with
    the cards and valid citations from that turn's tool results."""
    out: list[MessageOut] = []
    turn: dict[str, Any] | None = None

    def close() -> None:
        if turn is None:
            return
        text = "\n\n".join(t for t in turn["texts"] if t)
        valid, _ = split_citations(text, turn["citable"])
        out.append(
            MessageOut(
                id=turn["id"],
                role="assistant",
                text=text,
                cards=turn["cards"] + turn["products"].final(),
                citations=[CitationCard(**c) for c in valid],
            )
        )

    for i, m in enumerate(messages):
        if isinstance(m, HumanMessage):
            close()
            turn = None
            out.append(MessageOut(id=m.id or f"u{i}", role="user", text=message_text(m)))
            continue
        if turn is None:
            turn = {
                "id": m.id or f"a{i}",
                "texts": [],
                "cards": [],
                "citable": {},
                "products": ProductCards(),
            }
        if isinstance(m, AIMessage):
            turn["texts"].append(message_text(m))
        elif isinstance(m, ToolMessage):
            cards = []
            for card in m.artifact or []:
                if card.get("kind") == "citation":
                    turn["citable"][card["cite"]] = card
                else:
                    cards.append(card)
            turn["cards"] += turn["products"].take(m.name, cards)
    close()
    return out
