"""SSE v2 events: what the assistant streams to the browser, one typed model per event.

Every event carries ``v`` (2), ``turn_id``, ``agent``, and ``ts``. The runner fills those
in; producers only set the payload. On the wire each is ``id: <seq>`` / ``event: <type>`` /
``data: <json>`` (see :mod:`ai_commerce_stream.sse`). Browsers opt in with the header
``X-Assistant-Stream: 2``; without it they get today's v1 events.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

AgentName = Literal["steph", "xana", "planner", "person"]


def _now() -> datetime:
    return datetime.now(UTC)


class _Event(BaseModel):
    model_config = ConfigDict(frozen=True)

    v: Literal[2] = 2
    turn_id: str = ""
    agent: str = ""
    ts: datetime = Field(default_factory=_now)

    @property
    def terminal(self) -> bool:
        return False


class TurnStart(_Event):
    type: Literal["turn.start"] = "turn.start"
    conversation_id: str
    resume_url: str


class Signals(_Event):
    """Jev's typed read of the turn (development builds only)."""

    type: Literal["signals"] = "signals"
    signals: dict[str, Any]


class AgentHandoff(_Event):
    type: Literal["agent.handoff"] = "agent.handoff"
    from_agent: AgentName
    to_agent: AgentName
    reason_code: str  # a fixed code, never model text
    shared: list[str] = Field(description='What the next agent sees, e.g. ["order LK-1042"]')
    via: Literal["in_process", "a2a"] = "in_process"


class Todo(BaseModel):
    id: str
    content: str
    status: Literal["pending", "in_progress", "completed"]


class Plan(_Event):
    type: Literal["plan"] = "plan"
    plan_id: str
    revision: int
    constraints: list[str] = Field(default_factory=list)
    todos: list[Todo]
    simulated: bool = False


class ToolStart(_Event):
    type: Literal["tool.start"] = "tool.start"
    call_id: str
    tool: str
    label: str


class ToolProgress(_Event):
    type: Literal["tool.progress"] = "tool.progress"
    call_id: str
    label: str
    done: int | None = None
    total: int | None = None


class ToolEnd(_Event):
    type: Literal["tool.end"] = "tool.end"
    call_id: str
    tool: str
    ok: bool
    error_code: str | None = None


class TextDelta(_Event):
    type: Literal["text.delta"] = "text.delta"
    message_id: str = ""
    delta: str


class Card(_Event):
    """A product, order, store, cart, return, handoff, or basket card (``card["kind"]``)."""

    type: Literal["card"] = "card"
    card: dict[str, Any]


class Quote(_Event):
    """A return quote waiting for the customer's own confirmation; the turn pauses."""

    type: Literal["quote"] = "quote"
    quote: dict[str, Any]


class Ask(_Event):
    type: Literal["ask"] = "ask"
    question: str
    options: list[dict[str, str]] = Field(default_factory=list)


class Citations(_Event):
    type: Literal["citations"] = "citations"
    valid: list[dict[str, Any]]
    invalid: list[str]


class Done(_Event):
    type: Literal["done"] = "done"
    status: Literal["completed", "interrupted", "input_required", "canceled"] = "completed"
    model: str
    simulated: bool
    prompt_version: str
    usage: dict[str, float] | None = None

    @property
    def terminal(self) -> bool:
        return True


class Error(_Event):
    type: Literal["error"] = "error"
    code: str
    message: str
    retryable: bool = True

    @property
    def terminal(self) -> bool:
        return True


class Resumed(_Event):
    """Sent first on a resumed stream: events after ``from_seq`` follow."""

    type: Literal["resumed"] = "resumed"
    from_seq: int


StreamEvent = Annotated[
    TurnStart
    | Signals
    | AgentHandoff
    | Plan
    | ToolStart
    | ToolProgress
    | ToolEnd
    | TextDelta
    | Card
    | Quote
    | Ask
    | Citations
    | Done
    | Error
    | Resumed,
    Field(discriminator="type"),
]
EVENT_ADAPTER: TypeAdapter[Any] = TypeAdapter(StreamEvent)


def parse_event(data: dict[str, Any]) -> StreamEvent:
    return EVENT_ADAPTER.validate_python(data)  # type: ignore[no-any-return]


def event_json_schema() -> dict[str, Any]:
    """For ``packages/contracts``: the web client's types are generated from this."""
    return EVENT_ADAPTER.json_schema()
