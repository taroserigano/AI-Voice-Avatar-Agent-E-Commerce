"""Xena's brain for voice: a LangGraph agent ⇄ tools loop over Xena's own support tools.

The same narrow tools, server-side identity, and PostgreSQL checkpoint as Xena in the chat
(services/assistant), so a voice call is saved as a normal Xena conversation. What's
different is tuned for speaking in real time:

- the model is ``gpt-6-luna`` on the Responses API at low reasoning effort with priority
  processing (measured first token ~450-590 ms with this prompt and tools, against ~600-950
  ms on the default tier), streaming; its text goes straight to the speech engine;
- a tool call is announced the moment its name streams in, not when the call is complete, so
  the "Let me check that order" filler starts ~a second sooner;
- a snapshot of the customer's recent orders (with delivery status) is read when the call
  starts and given to the model (as untrusted data), so "where's my order?" needs no tool round
  trip;
- a question about returns, refunds, or policy runs the policy search (hybrid: keywords plus
  LlamaIndex/Qdrant meaning search, ~300 ms) *before* the model, recorded in the conversation as
  a real ``search_policies`` call. The model answers in one call instead of calling the tool and
  then answering (each model call is ~1-1.7 s), and its citations are checked as usual;
- the prompt is short and fixed per session (the dynamic part last) so OpenAI's prompt cache
  hits from the second turn on.

No planning agent here: a deep agent's plan-and-delegate loop costs seconds, which is right
for building a basket (services/planner) and wrong for a phone call.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any, Literal, TypedDict, cast

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    AnyMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    message_chunk_to_message,
)
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Command

from ai_commerce_voice.escalation import TOOL_ERRORS, escalation_reason, tool_errors_this_turn
from ai_commerce_voice.ports import AgentEvent, CardOut, QuoteOut, TextDelta, ToolStarted, TurnEnded
from assistant.graph import _superseded_proposal, recent_history
from assistant.policy_prefetch import (
    PREFETCH_SECTIONS,
    PREFETCH_TIMEOUT_S,
    prefetched_messages,
    retrieval_query,
    wants_policy,
)
from assistant.prompts import catalog_size
from assistant.tools import (
    ToolContext,
    _order_for_model,
    friendly_date,
    money,
    policy_search,
    untrusted,
)
from assistant.toolsets import XANA_TOOLS
from assistant.turns import (
    TOOL_LABELS,
    ProductCards,
    earlier_citations,
    message_text,
    split_citations,
)

log = logging.getLogger(__name__)

PROMPT_VERSION = "xana.voice.v7"
PROMPT_DIR = Path(__file__).resolve().parent / "prompts"
SNAPSHOT_ORDERS = 12


@lru_cache
def _template() -> str:
    return (PROMPT_DIR / f"{PROMPT_VERSION}.md").read_text(encoding="utf-8")


def orders_snapshot(details: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The recent orders the model may read at once: the chat tool's own whitelist, shortened.

    Each order starts with its items (with their size or color), so "which carrier brought my
    headphones?" is read off the right order; measured on the golden eval, a nested layout with
    the items last had the voice model take dates and carriers from a neighbouring order."""
    out = []
    for d in details[:SNAPSHOT_ORDERS]:
        o = _order_for_model(d)

        # Found by the golden eval: "returnable now" on 2 backpacks when 1 was already
        # returned, and "fully_returned" read aloud as done while that return was in transit.
        def can_return(ln: dict[str, Any]) -> str:
            done = ln.get("returned_quantity") or 0
            if ln["reason"] == "fully_returned":
                return " (already in a return: see this order's returns for where it stands)"
            if not ln["eligible"]:
                return f" (not returnable: {ln['reason']})"
            if done:
                left = ln["returnable_quantity"]
                return f" (returnable now: {left} of {ln['quantity']}; {done} already returned)"
            return " (returnable now)"

        returnable = {
            str(ln["order_line_id"]): can_return(ln)
            for ln in (d.get("return_options") or {}).get("lines", [])
        }
        delivery = o.get("delivery") or {}

        def item(i: dict[str, Any]) -> str:
            variant = i.get("variant") or ""
            shown = (
                variant
                and variant.lower() not in ("standard", "each")
                and variant.lower() not in i["title"].lower()
            )
            return (
                f"{i['quantity']} × "
                + (f"{i['brand']} " if i.get("brand") else "")
                + i["title"]
                + (f", {variant}" if shown else "")
                + returnable.get(i["line_id"], "")
            )

        out.append(
            {
                "items": [item(i) for i in o["items"]][:6],
                "order_number": o["order_number"],
                "status": o["status"],
                "placed_on": o["placed_on"],
                "delivered_on": o["delivered_on"],
                "arriving_by": o["arriving_by"],
                "carrier": delivery.get("carrier"),
                "tracking_number": delivery.get("tracking_number"),
                "latest_update": delivery.get("latest_update"),
                "total": o["total"],
                "shipping": o["shipping"],
                "returns": [_return_for_snapshot(r) for r in d.get("returns") or []],
                "order_id": o["order_id"],
            }
        )
    return out


def _return_for_snapshot(r: dict[str, Any]) -> dict[str, Any]:
    """A return on the order as get_refund_status shows it: its RMA, where it stands, and the
    refund (none until the warehouse receives and checks the item)."""
    refund = r.get("refund") or {}
    return {
        "rma_number": r["rma_number"],
        "status": str(r["status"]).replace("_", " "),
        "items": [f"{i['quantity']} × {i['product_title']}" for i in r.get("items", [])],
        "refund": (
            f"{refund['status']}, {money(refund['amount_minor'])}"
            + (f" on {friendly_date(refund['settled_at'])}" if refund.get("settled_at") else "")
            if refund
            else "not issued yet"
        ),
    }


def system_prompt(
    first_name: str,
    today: date,
    snapshot: list[dict[str, Any]] | None,
    vocabulary: dict[str, Any] | None = None,
) -> str:
    # Fixed instructions first (cacheable), then this call's facts.
    orders = (
        untrusted("orders_snapshot", {"order_count": len(snapshot), "orders": snapshot})
        if snapshot is not None
        else "(not loaded: use list_my_orders)"
    )
    vocab = vocabulary or {}
    types = ", ".join(str(t["value"]) for t in vocab.get("product_types", []))
    tags = ", ".join(f"{t['value']} ({t['label']})" for t in vocab.get("tags", []))
    return (
        f"{_template()}\n\n## This call\n\nYou're talking with {first_name or 'the customer'}, "
        f"who is signed in. Today is {today.strftime('%A, %B %d, %Y')}.\n\n"
        f"## Your orders right now\n\n{orders}\n\n"
        f"## Catalog filters\n\nUse only these exact values in product search. "
        f"Product types: {types or '(unavailable)'}. Tags: {tags or '(unavailable)'}.\n"
        f"{catalog_size(vocab)}\n"
    )


@dataclass
class VoiceContext:
    """Per-session model setup. Lives in the run config, never in checkpointed state."""

    system: str
    model: Runnable[Any, Any]
    bound: Runnable[Any, Any]
    max_tool_calls: int
    # The stronger model for turns the escalation rules move up (decision 26), if any.
    strong: Runnable[Any, Any] | None = None
    strong_bound: Runnable[Any, Any] | None = None
    strong_name: str | None = None


class VoiceState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    agent: str
    tool_calls_this_turn: int
    # Why this turn is answered by the stronger model (ai_commerce_voice.escalation), or None.
    escalated: str | None


def _voice(config: RunnableConfig) -> VoiceContext:
    vc = (config.get("configurable") or {}).get("voice")
    if not isinstance(vc, VoiceContext):
        raise RuntimeError("voice turn without a voice context")
    return vc


async def agent(state: VoiceState, config: RunnableConfig) -> dict[str, Any]:
    if _superseded_proposal(state["messages"]):
        return {}
    vc = _voice(config)
    used = state.get("tool_calls_this_turn", 0)
    escalated = state.get("escalated")
    if not escalated and tool_errors_this_turn(state["messages"]) >= TOOL_ERRORS:
        escalated = "tool_errors"
    model: Runnable[Any, Any] = vc.bound if used < vc.max_tool_calls else vc.model
    strong = False
    if escalated and vc.strong is not None and vc.strong_bound is not None:
        strong = True
        model = vc.strong_bound if used < vc.max_tool_calls else vc.strong
    messages: list[AnyMessage] = [
        SystemMessage(content=vc.system),
        *recent_history(state["messages"]),
    ]
    started = time.perf_counter()
    first: float | None = None
    merged: AIMessageChunk | None = None
    async for chunk in model.astream(messages, config):
        if first is None:
            first = time.perf_counter()
        merged = chunk if merged is None else merged + chunk
    response = message_chunk_to_message(merged) if merged is not None else AIMessage(content="")
    calls = len(response.tool_calls) if isinstance(response, AIMessage) else 0
    usage = getattr(response, "usage_metadata", None) or {}
    log.info(
        "voice model call (%s): first chunk %.0f ms, done %.0f ms, %s in (%s cached), %s out "
        "(%s reasoning), %d tool calls",
        f"{vc.strong_name}, {escalated}" if strong else "default",
        ((first or started) - started) * 1000,
        (time.perf_counter() - started) * 1000,
        usage.get("input_tokens"),
        (usage.get("input_token_details") or {}).get("cache_read"),
        usage.get("output_tokens"),
        (usage.get("output_token_details") or {}).get("reasoning"),
        calls,
    )
    return {"messages": [response], "tool_calls_this_turn": used + calls, "escalated": escalated}


def after_agent(state: VoiceState) -> str:
    last = state["messages"][-1]
    return "tools" if isinstance(last, AIMessage) and last.tool_calls else END


def build_voice_graph(checkpointer: BaseCheckpointSaver[Any] | None) -> CompiledStateGraph:  # type: ignore[type-arg]
    builder = StateGraph(VoiceState)
    builder.add_node("agent", agent)
    builder.add_node("tools", ToolNode(XANA_TOOLS, handle_tool_errors=True))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", after_agent, ["tools", END])
    builder.add_edge("tools", "agent")
    return builder.compile(checkpointer=checkpointer)


def make_context(
    model: BaseChatModel,
    *,
    system: str,
    max_tool_calls: int,
    bind_extra: dict[str, Any] | None = None,
    strong: BaseChatModel | None = None,
    strong_name: str | None = None,
) -> VoiceContext:
    bound = model.bind_tools(XANA_TOOLS, **(bind_extra or {}))
    return VoiceContext(
        system=system,
        model=model,
        bound=bound,
        max_tool_calls=max_tool_calls,
        strong=strong,
        strong_bound=strong.bind_tools(XANA_TOOLS, **(bind_extra or {})) if strong else None,
        strong_name=strong_name,
    )


class XanaBrain:
    def __init__(
        self,
        graph: CompiledStateGraph,  # type: ignore[type-arg]
        *,
        conversation_id: str,
        ctx: ToolContext,
        voice: VoiceContext,
        model: str,
        simulated: bool,
    ) -> None:
        self.graph = graph
        self.conversation_id = conversation_id
        self.ctx = ctx
        self.voice = voice
        self.model = model
        self.simulated = simulated

    def _config(self) -> RunnableConfig:
        return {
            "configurable": {
                "thread_id": self.conversation_id,
                "ctx": self.ctx,
                "voice": self.voice,
            },
            "recursion_limit": 20,
            "metadata": {
                "agent": "xana",
                "channel": "voice",
                "prompt_version": PROMPT_VERSION,
                "model": self.model,
            },
            "run_name": "xana-voice-turn",
        }

    async def turn(self, text: str, message_id: str | None = None) -> AsyncIterator[AgentEvent]:
        # Fixed ids: a turn restarted on a corrected transcript replaces its draft messages
        # (the customer's words and any prefetched policy search) instead of adding to them.
        mid = message_id or str(uuid.uuid4())
        messages: list[AnyMessage] = [HumanMessage(content=text, id=mid)]
        snapshot = await self.graph.aget_state(self._config())
        history: list[AnyMessage] = [m for m in snapshot.values.get("messages", []) if m.id != mid]
        # A section read earlier in the call stays citable (as in the chat).
        citable: dict[str, dict[str, Any]] = earlier_citations(history)
        escalated = escalation_reason(text, history)
        prefetched = await self._prefetch_policies(text, mid)
        if prefetched is not None:
            messages += prefetched
            for card in prefetched[1].artifact or []:
                if card.get("kind") == "citation":
                    citable[card["cite"]] = card
        graph_input = {
            "messages": messages,
            "agent": "xana",
            # The prefetch isn't the model's call: it doesn't use up the model's tool budget
            # (a return that needs six calls of its own would stop before the quote).
            "tool_calls_this_turn": 0,
            "escalated": escalated if self.voice.strong is not None else None,
        }
        async for ev in self._stream(graph_input, citable):
            yield ev

    async def _prefetch_policies(self, text: str, mid: str) -> list[Any] | None:
        """Search the policies with the customer's own words before the model, when the
        question is about policy, and record it as a ``search_policies`` call with the tool's
        own output format. It asks for more sections than the tool (a general rule and the
        item's category rule often both matter: "opened items are fine" plus "electronics are
        inspected"). None, so the model may call the tool itself, when the question isn't about
        policy or the search is slow or fails."""
        if not wants_policy(text):
            return None
        question = retrieval_query(text)[:300]
        started = time.perf_counter()
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(policy_search, self.ctx.client, question, PREFETCH_SECTIONS),
                PREFETCH_TIMEOUT_S,
            )
            messages: list[Any] = prefetched_messages(question, result, mid)
        except Exception as exc:  # noqa: BLE001 - the model can still call the tool
            log.warning("policy prefetch skipped: %s", type(exc).__name__)
            return None
        log.info("policy prefetch: %.0f ms", (time.perf_counter() - started) * 1000)
        return messages

    def resume(
        self, outcome: Literal["confirmed", "declined", "superseded"]
    ) -> AsyncIterator[AgentEvent]:
        return self._stream(Command(resume={"outcome": outcome}))

    async def pending_quote(self) -> dict[str, Any] | None:
        snapshot = await self.graph.aget_state(
            {"configurable": {"thread_id": self.conversation_id}}
        )
        for pending in getattr(snapshot, "interrupts", ()) or ():
            value = getattr(pending, "value", None)
            if isinstance(value, dict) and value.get("kind") == "return_quote":
                return value
        return None

    async def _stream(
        self, graph_input: Any, citable: dict[str, dict[str, Any]] | None = None
    ) -> AsyncIterator[AgentEvent]:
        started = time.perf_counter()
        first_token_ms: float | None = None
        answer: list[str] = []
        citable = dict(citable or {})
        announced: set[str] = set()
        # Calls already announced from their streamed name, not yet seen complete.
        early: list[str] = []
        products = ProductCards()
        # A model call that stalls before she has said anything is retried once from the
        # checkpoint (input None resumes the failed step; finished tool calls aren't rerun), so
        # the caller hears the filler a little longer instead of "something went wrong". Seen
        # on the golden eval: 14 of 1,997 voice cases hit an OpenAI read timeout (2026-10-03).
        attempts = 0
        while True:
            attempts += 1
            try:
                async for event in self._step(
                    graph_input, answer, citable, products, announced, early
                ):
                    if isinstance(event, TextDelta) and first_token_ms is None:
                        first_token_ms = (time.perf_counter() - started) * 1000
                    yield event
                break
            except Exception as exc:
                if not answer and attempts == 1 and _transient(exc):
                    log.warning("voice model step failed (%s); retrying once", type(exc).__name__)
                    graph_input = None
                    continue
                log.exception("voice turn failed")
                # She already answered (a later step failed, e.g. a network timeout): end the
                # turn there rather than put an error under an answer the customer just heard.
                yield TurnEnded(
                    first_token_ms=first_token_ms,
                    error=None
                    if answer
                    else "Sorry, something went wrong on our side. Please try again.",
                )
                return
        for card in products.final("".join(answer)):
            yield CardOut(card)
        valid, invalid = split_citations("".join(answer), citable)
        if invalid:
            log.warning("voice answer cited sections it didn't retrieve: %s", invalid)
        yield TurnEnded(
            citations=valid, invalid_citations=list(invalid), first_token_ms=first_token_ms
        )

    async def _step(
        self,
        graph_input: Any,
        answer: list[str],
        citable: dict[str, dict[str, Any]],
        products: ProductCards,
        announced: set[str],
        early: list[str],
    ) -> AsyncIterator[AgentEvent]:
        """One run of the graph to its end or its next interrupt, as events."""
        # Text streamed during the current agent step: its final message repeats it (the
        # Responses API gives the chunks and the final message different ids).
        streamed_this_step = False
        stream = self.graph.astream(
            graph_input, self._config(), stream_mode=["messages", "updates"]
        )
        async for mode, chunk in cast(AsyncIterator[tuple[str, Any]], stream):
            if mode == "messages":
                message, meta = chunk
                if meta.get("langgraph_node") != "agent" or not isinstance(message, AIMessageChunk):
                    continue
                for tc in message.tool_call_chunks or []:
                    name = tc.get("name")
                    key = tc.get("id") or f"{message.id}:{tc.get('index')}"
                    if name and key not in announced:
                        announced.add(key)
                        early.append(name)
                        yield ToolStarted(name, TOOL_LABELS.get(name, "Working on it…"))
                delta = message_text(message)
                if delta:
                    streamed_this_step = True
                    answer.append(delta)
                    yield TextDelta(delta)
                continue
            for node, update in (chunk or {}).items():
                if node == "__interrupt__":
                    for pending in update:
                        yield QuoteOut(dict(pending.value))
                    continue
                for message in (update or {}).get("messages", []):
                    if isinstance(message, AIMessage):
                        for call in message.tool_calls:
                            if call["name"] in early:
                                early.remove(call["name"])
                            else:
                                yield ToolStarted(
                                    call["name"],
                                    TOOL_LABELS.get(call["name"], "Working on it…"),
                                )
                        if not streamed_this_step and (text := message_text(message)):
                            answer.append(text)
                            yield TextDelta(text)
                        streamed_this_step = False
                    elif isinstance(message, ToolMessage):
                        cards = []
                        for card in message.artifact or []:
                            if card.get("kind") == "citation":
                                citable[card["cite"]] = card
                            else:
                                cards.append(card)
                        for card in products.take(message.name, cards):
                            yield CardOut(card)


def _transient(exc: BaseException) -> bool:
    """A timeout or dropped connection to the model provider, worth one more try."""
    names = {type(e).__name__ for e in (exc, exc.__cause__, exc.__context__) if e is not None}
    return isinstance(exc, (TimeoutError, ConnectionError)) or bool(
        names & {"APITimeoutError", "OpenAITimeoutError", "APIConnectionError", "ReadTimeout",
                 "RemoteProtocolError", "ReadError", "InternalServerError"}
    )  # fmt: skip
