"""The assistant graph: route → agent ⇄ tools, checkpointed in PostgreSQL per conversation.

``route`` asks Jev about the customer's turn (intent, return reason, which order line, whether
they want a person) and resets the per-turn counters. For Xana, a message about policy also
gets its policy search here, alongside Jev and before the model, recorded as a
``search_policies`` call (assistant.policy_prefetch): the model answers in one call instead of
calling the tool and then answering. ``agent`` is the chat model with the
tools allowed for this assistant, plus Jev's confident signals as hints. ``tools`` runs the
requested tool calls against the commerce API. The server-side ToolContext (who the
customer is) travels in the run config, not in the checkpointed state.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Annotated, Any, TypedDict

from langchain_core.messages import (
    AIMessage,
    AnyMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

from assistant.commerce import catalog_vocabulary
from assistant.config import get_settings
from assistant.jev.decisions import TurnSignals
from assistant.jev.signals import turn_signals
from assistant.models import choose_model
from assistant.policy_prefetch import (
    PREFETCH_TIMEOUT_S,
    prefetched_messages,
    start_policy_search,
)
from assistant.prompts import render_prompt
from assistant.tools import ctx_from
from assistant.toolsets import ALL_TOOLS, tools_for

log = logging.getLogger(__name__)

HISTORY_MESSAGES = 40


class AssistantState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    agent: str
    tool_calls_this_turn: int
    # Jev's signals about the latest customer turn (TurnSignals as a dict).
    signals: dict[str, Any]


def recent_history(messages: list[AnyMessage], limit: int = HISTORY_MESSAGES) -> list[AnyMessage]:
    """The last ``limit`` messages, starting at a customer message so no tool result is cut off
    from the call that asked for it."""
    if len(messages) <= limit:
        return messages
    tail = messages[-limit:]
    for i, m in enumerate(tail):
        if isinstance(m, HumanMessage):
            return tail[i:]
    return tail


def route(state: AssistantState, config: RunnableConfig) -> dict[str, Any]:
    ctx = ctx_from(config)
    search = None
    last = state["messages"][-1] if state["messages"] else None
    if (
        get_settings().assistant_policy_prefetch
        and isinstance(last, HumanMessage)
        and isinstance(last.content, str)
        and state.get("agent") == "xana"
    ):
        search = start_policy_search(ctx.client, last.content)
    signals = turn_signals(list(state["messages"]))
    # Tools read the signals from the server-side context (e.g. the return reason for a quote).
    ctx.signals = signals.model_dump()
    update: dict[str, Any] = {"tool_calls_this_turn": 0, "signals": signals.model_dump()}
    # A turn trying to talk its way past the rules is declined without tools.
    if search is not None and not signals.bypass_attempt:
        question, pending = search
        try:
            result = pending.result(timeout=PREFETCH_TIMEOUT_S)
        except Exception as exc:  # noqa: BLE001 - the model can still call the tool
            log.warning("policy prefetch skipped: %s", type(exc).__name__)
        else:
            # Not counted in tool_calls_this_turn: the model's own budget is for its own calls.
            update["messages"] = prefetched_messages(question, result)
    return update


def _superseded_proposal(messages: list[AnyMessage]) -> bool:
    """The customer moved on while a quote was waiting: close it quietly, with no reply."""
    last = messages[-1] if messages else None
    return (
        isinstance(last, ToolMessage)
        and last.name == "propose_return"
        and any(c.get("outcome") == "superseded" for c in (last.artifact or []))
    )


def agent(state: AssistantState, config: RunnableConfig) -> dict[str, Any]:
    if _superseded_proposal(state["messages"]):
        return {}
    ctx = ctx_from(config)
    settings = get_settings()
    choice = choose_model()
    name = state.get("agent", "steph")
    vocabulary = catalog_vocabulary(ctx.client)
    system = render_prompt(
        name, first_name=ctx.first_name, vocabulary=vocabulary, today=date.today(), voice=ctx.voice
    )
    used = state.get("tool_calls_this_turn", 0)
    tools = tools_for(name) if used < settings.max_tool_calls_per_turn else []
    signals = TurnSignals.model_validate(state.get("signals") or {"source": "off"})
    hint = signals.prompt_hint()
    if hint:
        system = f"{system}\n\n{hint}"
    extra: dict[str, Any] = (
        {"vocabulary": vocabulary, "signals": signals.model_dump(), "agent": name}
        if choice.simulated
        else {}
    )
    model = choice.model.bind_tools(tools, **extra) if tools else choice.model
    messages: list[AnyMessage] = [
        # The system prompt is the same for every turn of a conversation: cache it.
        SystemMessage(
            content=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
        ),
        *recent_history(state["messages"]),
    ]
    response = model.invoke(messages, config)
    calls = len(response.tool_calls) if isinstance(response, AIMessage) else 0
    return {"messages": [response], "tool_calls_this_turn": used + calls}


def after_agent(state: AssistantState) -> str:
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    return END


def build_graph(checkpointer: BaseCheckpointSaver | None) -> CompiledStateGraph:  # type: ignore[type-arg]
    builder = StateGraph(AssistantState)
    builder.add_node("route", route)
    builder.add_node("agent", agent)
    builder.add_node("tools", ToolNode(ALL_TOOLS, handle_tool_errors=True))
    builder.add_edge(START, "route")
    builder.add_edge("route", "agent")
    builder.add_conditional_edges("agent", after_agent, ["tools", END])
    builder.add_edge("tools", "agent")
    return builder.compile(checkpointer=checkpointer)
