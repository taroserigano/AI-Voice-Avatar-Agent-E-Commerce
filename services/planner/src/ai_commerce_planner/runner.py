"""Run one planning task and report it as :mod:`ai_commerce_planner.events`.

This is the in-process planner (``PLANNER_TRANSPORT=inproc``, decision v2-1). The A2A
server wraps the same runner, so both transports emit identical events.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from collections.abc import Iterator
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from pydantic import BaseModel, Field

from ai_commerce_planner.agent import PROMPT_VERSION, build_planner
from ai_commerce_planner.basket import Basket
from ai_commerce_planner.catalog import CatalogPort
from ai_commerce_planner.config import PlannerSettings, get_settings
from ai_commerce_planner.constraints import Constraints, parse_constraints
from ai_commerce_planner.events import (
    BasketEvent,
    DoneEvent,
    ErrorEvent,
    PlanEvent,
    PlannerEvent,
    TextEvent,
    Todo,
    ToolEndEvent,
    ToolStartEvent,
)
from ai_commerce_planner.models import planner_models

MAX_GOAL_CHARS = 600
log = logging.getLogger(__name__)


class PlannerRequest(BaseModel):
    """What the gateway sends: the shopper's goal and any rules it already knows.

    No conversation history and no personal data beyond the goal itself."""

    goal: str = Field(min_length=3, max_length=MAX_GOAL_CHARS)
    constraints: Constraints = Field(default_factory=Constraints)


def _label(tool: str, args: dict[str, Any]) -> str:
    if tool == "search_products":
        what = args.get("text") or ", ".join(
            t.replace("-", " ") for t in args.get("product_types") or []
        )
        return f"Looking for {what}" if what else "Searching the catalog"
    return {
        "check_basket": "Checking prices, stock, and your rules",
        "propose_basket": "Building your basket",
        "task": "Asking a helper to research products",
    }.get(tool, "Working")


def _updates(chunk: Any) -> list[tuple[str, dict[str, Any]]]:
    """(node, update) pairs from one v2 ``updates`` chunk; tool nodes may yield lists."""
    out: list[tuple[str, dict[str, Any]]] = []
    for node, update in (chunk.get("data") or {}).items():
        for part in update if isinstance(update, list) else [update]:
            if isinstance(part, dict):
                out.append((node, part))
    return out


def run_planner(
    request: PlannerRequest,
    catalog: CatalogPort,
    settings: PlannerSettings | None = None,
    stop: threading.Event | None = None,
) -> Iterator[PlannerEvent]:
    """``stop``: set it to end the run at the next step (A2A cancel, the shopper's Stop)."""
    settings = settings or get_settings()
    # The request's rules plus anything code finds in the goal. Never looser than either.
    constraints = request.constraints.tightened(parse_constraints(request.goal))
    models = planner_models(settings, servings=constraints.servings)
    graph = build_planner(
        model=models.main,
        helper_model=models.helper,
        catalog=catalog,
        constraints=constraints,
        max_model_calls=settings.planner_max_model_calls,
        max_tool_calls=settings.planner_max_tool_calls,
    )
    started = time.monotonic()
    revision = 0
    model_calls = tool_calls = 0
    open_calls: dict[str, str] = {}
    basket: Basket | None = None
    summary = ""
    final_text = ""
    status: str = "completed"
    try:
        stream = graph.stream(
            {"messages": [HumanMessage(request.goal)]},
            {"recursion_limit": 4 * settings.planner_max_tool_calls},
            stream_mode=["updates"],
            subgraphs=True,
            version="v2",
        )
        for chunk in stream:
            if stop is not None and stop.is_set():
                status = "canceled"
                break
            if time.monotonic() - started > settings.planner_timeout_s:
                status = "timeout"
                break
            helper = bool(chunk.get("ns"))  # a helper agent's own steps stay internal
            for _node, update in _updates(chunk):
                if "run_model_call_count" in update and not helper:
                    model_calls = int(update["run_model_call_count"])
                if update.get("todos") is not None and not helper:
                    revision += 1
                    yield PlanEvent(
                        revision=revision,
                        todos=[
                            Todo(id=str(i), content=t["content"], status=t["status"])
                            for i, t in enumerate(update["todos"])
                        ],
                    )
                for msg in update.get("messages") or []:
                    if helper:
                        continue
                    if isinstance(msg, AIMessage):
                        for tc in msg.tool_calls:
                            if tc["name"] == "write_todos":
                                continue
                            tool_calls += 1
                            call_id = tc["id"] or f"call-{tool_calls}"
                            open_calls[call_id] = tc["name"]
                            yield ToolStartEvent(
                                call_id=call_id,
                                tool=tc["name"],
                                label=_label(tc["name"], tc["args"]),
                            )
                        if not msg.tool_calls and msg.text:
                            final_text = msg.text
                    elif isinstance(msg, ToolMessage) and msg.tool_call_id in open_calls:
                        yield ToolEndEvent(
                            call_id=msg.tool_call_id,
                            tool=open_calls.pop(msg.tool_call_id),
                            ok=msg.status != "error",
                        )
                if update.get("basket") is not None and not helper:
                    basket = Basket.model_validate(update["basket"])
                    summary = str(update.get("basket_summary") or "")
    except Exception as exc:  # noqa: BLE001 - the gateway shows a retryable error card
        log.error("planner run failed: %s", type(exc).__name__, exc_info=exc)
        yield ErrorEvent(
            code="planner_failed",
            message="The planner couldn't finish this request.",
            retryable=True,
        )
        yield DoneEvent(
            status="no_basket",
            simulated=models.simulated,
            model=models.name,
            prompt_version=PROMPT_VERSION,
            model_calls=model_calls,
            tool_calls=tool_calls,
        )
        return

    if (
        basket is None
        and status == "completed"
        and (
            model_calls >= settings.planner_max_model_calls
            or tool_calls >= settings.planner_max_tool_calls
        )
    ):
        status = "limit_reached"
    if basket is not None:
        yield BasketEvent(basket=basket, summary=summary, simulated=models.simulated)
    if final_text:
        yield TextEvent(text=final_text)
    yield DoneEvent(
        status="no_basket" if basket is None and status == "completed" else status,
        simulated=models.simulated,
        model=models.name,
        prompt_version=PROMPT_VERSION,
        model_calls=model_calls,
        tool_calls=tool_calls,
    )


def new_task_id() -> str:
    return uuid.uuid4().hex
