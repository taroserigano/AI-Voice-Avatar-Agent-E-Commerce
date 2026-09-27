"""Turn signals for the graph: build Jev's state from the conversation, ask, and decide."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage

from assistant.config import get_settings
from assistant.jev.client import DecisionModel, JevClient, JevError
from assistant.jev.decisions import TurnSignals, decide
from assistant.jev.questions import turn_questions
from assistant.jev.simulator import JevSimulator

log = logging.getLogger(__name__)

RECENT_TURNS = 6


@lru_cache
def decision_model() -> DecisionModel | None:
    """Jev when keyed, the labeled simulator otherwise, or None when JEV_ENABLED is off."""
    settings = get_settings()
    if not settings.jev_enabled:
        return None
    if settings.typesafe_api_key:
        return JevClient(
            settings.typesafe_api_key,
            model=settings.jev_model,
            base_url=settings.typesafe_base_url,
            timeout_s=settings.jev_timeout_s,
        )
    return JevSimulator()


def _text(message: BaseMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    return " ".join(b.get("text", "") for b in content if isinstance(b, dict))


def candidate_lines(messages: list[BaseMessage]) -> list[dict[str, Any]]:
    """Order lines the server already showed in this conversation (newest orders first)."""
    from assistant.scripted import read_payload

    lines: dict[str, dict[str, Any]] = {}
    for m in reversed(messages):
        if not isinstance(m, ToolMessage) or m.name not in ("list_my_orders", "get_order_status"):
            continue
        data = read_payload(str(m.content))
        for order in data.get("orders") or ([data] if "order_id" in data else []):
            for item in order.get("items", []):
                lines.setdefault(
                    item["line_id"],
                    {
                        "line_id": item["line_id"],
                        "title": item["title"],
                        "variant": item.get("variant", ""),
                        "order_number": order.get("order_number", ""),
                        "delivered_at": order.get("delivered_at"),
                    },
                )
    return list(lines.values())


def turn_state(messages: list[BaseMessage]) -> dict[str, Any]:
    convo: list[dict[str, str]] = []
    for m in messages:
        if isinstance(m, HumanMessage):
            convo.append({"role": "customer", "text": _text(m)[:1000]})
        elif isinstance(m, AIMessage) and _text(m).strip():
            convo.append({"role": "assistant", "text": _text(m)[:600]})
    return {
        "conversation": convo[-RECENT_TURNS:],
        "candidate_order_lines": candidate_lines(messages),
    }


def turn_signals(messages: list[BaseMessage]) -> TurnSignals:
    model = decision_model()
    if model is None:
        return TurnSignals(source="off")
    state = turn_state(messages)
    try:
        return decide(model.ask(state, turn_questions(state["candidate_order_lines"])))
    except JevError as exc:
        log.warning("Jev unavailable, continuing without it: %s", exc)
        return TurnSignals(source="error")
