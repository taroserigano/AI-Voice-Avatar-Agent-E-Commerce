"""Xana's brain for voice: a LangGraph agent ⇄ tools loop over Xana's own support tools.

The same narrow tools, server-side identity, and PostgreSQL checkpoint as Xana in the chat
(services/assistant), so a voice call is saved as a normal Xana conversation. What's
different is tuned for speaking in real time:

- the model is ``gpt-6-luna`` on the Responses API at low reasoning effort with priority
  processing (measured first token ~450-590 ms with this prompt and tools, against ~600-950
  ms on the default tier), streaming; its text goes straight to the speech engine;
- a tool call is announced the moment its name streams in, not when the call is complete, so
  the "Let me check that order" filler starts ~a second sooner;
- a snapshot of the customer's recent orders is read when the call starts and given to the
  model (as untrusted data), so "where's my order?" needs no tool round trip;
- the prompt is short and fixed per session (the dynamic part last) so OpenAI's prompt cache
  hits from the second turn on.

No planning agent here: a deep agent's plan-and-delegate loop costs seconds, which is right
for building a basket (services/planner) and wrong for a phone call.
"""

from __future__ import annotations

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
)
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Command

from ai_commerce_voice.ports import AgentEvent, CardOut, QuoteOut, TextDelta, ToolStarted, TurnEnded
from assistant.graph import _superseded_proposal, recent_history
from assistant.tools import ToolContext, _order_for_model, untrusted
from assistant.toolsets import XANA_TOOLS
from assistant.turns import TOOL_LABELS, message_text, split_citations

log = logging.getLogger(__name__)

PROMPT_VERSION = "xana.voice.v1"
PROMPT_DIR = Path(__file__).resolve().parent / "prompts"
SNAPSHOT_ORDERS = 8


@lru_cache
def _template() -> str:
    return (PROMPT_DIR / f"{PROMPT_VERSION}.md").read_text(encoding="utf-8")


def orders_snapshot(details: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The recent orders the model may read at once: the chat tool's own whitelist, shortened."""
    out = []
    for d in details[:SNAPSHOT_ORDERS]:
        o = _order_for_model(d)
        out.append(
            {
                "order_id": o["order_id"],
                "order_number": o["order_number"],
                "status": o["status"],
                "placed_on": o["placed_on"],
                "arriving_by": o["arriving_by"],
                "delivered_on": o["delivered_on"],
                "total": o["total"],
                "items": [f"{i['quantity']} × {i['title']}" for i in o["items"]][:6],
            }
        )
    return out


def system_prompt(first_name: str, today: date, snapshot: list[dict[str, Any]] | None) -> str:
    # Fixed instructions first (cacheable), then this call's facts.
    orders = (
        untrusted("orders_snapshot", {"orders": snapshot})
        if snapshot is not None
        else "(not loaded: use list_my_orders)"
    )
    return (
        f"{_template()}\n\n## This call\n\nYou're talking with {first_name or 'the customer'}, "
        f"who is signed in. Today is {today.strftime('%A, %B %d, %Y')}.\n\n"
        f"## Your orders right now\n\n{orders}\n"
    )


@dataclass
class VoiceContext:
    """Per-session model setup. Lives in the run config, never in checkpointed state."""

    system: str
    model: Runnable[Any, Any]
    bound: Runnable[Any, Any]
    max_tool_calls: int


class VoiceState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    agent: str
    tool_calls_this_turn: int


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
    model = vc.bound if used < vc.max_tool_calls else vc.model
    messages: list[AnyMessage] = [
        SystemMessage(content=vc.system),
        *recent_history(state["messages"]),
    ]
    response = await model.ainvoke(messages, config)
    calls = len(response.tool_calls) if isinstance(response, AIMessage) else 0
    return {"messages": [response], "tool_calls_this_turn": used + calls}


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
) -> VoiceContext:
    bound = model.bind_tools(XANA_TOOLS, **(bind_extra or {}))
    return VoiceContext(system=system, model=model, bound=bound, max_tool_calls=max_tool_calls)


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

    def turn(self, text: str, message_id: str | None = None) -> AsyncIterator[AgentEvent]:
        # A fixed id: a turn restarted on a corrected transcript replaces its draft message.
        message = HumanMessage(content=text, id=message_id or str(uuid.uuid4()))
        return self._stream({"messages": [message], "agent": "xana", "tool_calls_this_turn": 0})

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

    async def _stream(self, graph_input: Any) -> AsyncIterator[AgentEvent]:
        started = time.perf_counter()
        first_token_ms: float | None = None
        answer: list[str] = []
        citable: dict[str, dict[str, Any]] = {}
        # Text streamed during the current agent step: its final message repeats it (the
        # Responses API gives the chunks and the final message different ids).
        streamed_this_step = False
        announced: set[str] = set()
        # Calls already announced from their streamed name, not yet seen complete.
        early: list[str] = []
        try:
            stream = self.graph.astream(
                graph_input, self._config(), stream_mode=["messages", "updates"]
            )
            async for mode, chunk in cast(AsyncIterator[tuple[str, Any]], stream):
                if mode == "messages":
                    message, meta = chunk
                    if meta.get("langgraph_node") != "agent" or not isinstance(
                        message, AIMessageChunk
                    ):
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
                        if first_token_ms is None:
                            first_token_ms = (time.perf_counter() - started) * 1000
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
                            for card in message.artifact or []:
                                if card.get("kind") == "citation":
                                    citable[card["cite"]] = card
                                else:
                                    yield CardOut(card)
        except Exception:
            log.exception("voice turn failed")
            yield TurnEnded(
                first_token_ms=first_token_ms,
                error="Sorry, something went wrong on our side. Please try again.",
            )
            return
        valid, invalid = split_citations("".join(answer), citable)
        if invalid:
            log.warning("voice answer cited sections it didn't retrieve: %s", invalid)
        yield TurnEnded(citations=valid, first_token_ms=first_token_ms)
