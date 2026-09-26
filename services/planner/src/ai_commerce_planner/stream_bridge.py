"""From planner events to the assistant's SSE v2 stream, as one detached, resumable turn.

The gateway uses :func:`planner_producer` with ``ai_commerce_stream.TurnRunner``. Planner
output is untrusted when it crosses the A2A boundary, so the basket is re-checked with the
gateway's own catalog view (:func:`reverify_basket`) before its card is sent.
"""

from __future__ import annotations

import threading
import uuid
from collections.abc import Callable

from ai_commerce_planner.agent import PROMPT_VERSION
from ai_commerce_planner.basket import Basket, ProposedLine, check_basket
from ai_commerce_planner.catalog import CatalogPort
from ai_commerce_planner.constraints import Constraints, parse_constraints
from ai_commerce_planner.events import (
    BasketEvent,
    DoneEvent,
    ErrorEvent,
    PlanEvent,
    TextEvent,
    ToolEndEvent,
    ToolStartEvent,
)
from ai_commerce_planner.port import PlannerPort
from ai_commerce_planner.runner import PlannerRequest
from ai_commerce_stream.events import Card, Done, Error, Plan, TextDelta, ToolEnd, ToolStart
from ai_commerce_stream.events import Todo as StreamTodo
from ai_commerce_stream.runner import Emit, Producer


def reverify_basket(basket: Basket, catalog: CatalogPort, constraints: Constraints) -> Basket:
    """The basket as the gateway's own catalog and rules see it: only IDs and quantities
    are taken from the planner; prices, stock, and allergens are read again."""
    lines = [
        ProposedLine(
            product_id=ln.product_id,
            variant_id=ln.variant_id,
            quantity=ln.quantity,
            reason=ln.reason,
        )
        for ln in basket.lines
    ]
    checked = check_basket(lines, catalog, constraints)
    return checked.model_copy(update={"excluded": [*basket.excluded, *checked.excluded]})


def planner_producer(
    port: PlannerPort,
    request: PlannerRequest,
    *,
    customer_id: uuid.UUID,
    conversation_id: str,
    gateway_catalog: Callable[[], CatalogPort],
) -> Producer:
    constraints = request.constraints.tightened(parse_constraints(request.goal))
    plan_id = uuid.uuid4().hex

    def produce(emit: Emit, stop: threading.Event) -> None:
        done: DoneEvent | None = None
        failed = False
        for event in port.run(
            request, customer_id=customer_id, conversation_id=conversation_id, stop=stop
        ):
            match event:
                case PlanEvent():
                    emit(
                        Plan(
                            agent="planner",
                            plan_id=plan_id,
                            revision=event.revision,
                            constraints=constraints.labels(),
                            todos=[StreamTodo(**t.model_dump()) for t in event.todos],
                        )
                    )
                case ToolStartEvent():
                    emit(
                        ToolStart(
                            agent="planner",
                            call_id=event.call_id,
                            tool=event.tool,
                            label=event.label,
                        )
                    )
                case ToolEndEvent():
                    emit(
                        ToolEnd(
                            agent="planner", call_id=event.call_id, tool=event.tool, ok=event.ok
                        )
                    )
                case BasketEvent():
                    catalog = gateway_catalog()
                    try:
                        basket = reverify_basket(event.basket, catalog, constraints)
                    finally:
                        close = getattr(catalog, "close", None)
                        if callable(close):
                            close()
                    emit(
                        Card(
                            agent="planner",
                            card={
                                "kind": "basket",
                                **basket.model_dump(mode="json"),
                                "summary": event.summary,
                                "simulated": event.simulated,
                            },
                        )
                    )
                case TextEvent():
                    emit(TextDelta(agent="planner", delta=event.text))
                case ErrorEvent():
                    failed = True
                case DoneEvent():
                    done = event
        if failed or done is None:
            emit(
                Error(
                    code="planner_failed",
                    message="The planner couldn't finish this request. Please try again.",
                )
            )
            return
        emit(
            Done(
                agent="planner",
                status="canceled" if done.status == "canceled" else "completed",
                model=done.model,
                simulated=done.simulated,
                prompt_version=PROMPT_VERSION,
                usage={"model_calls": done.model_calls, "tool_calls": done.tool_calls},
            )
        )

    return produce
