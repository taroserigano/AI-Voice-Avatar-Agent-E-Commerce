"""What a planner run reports as it goes. The assistant gateway re-emits these as SSE v2
events (``plan``, ``tool.start``, ``tool.end``, ``card`` basket, ``text.delta``, ``done``)."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from ai_commerce_planner.basket import Basket


class Todo(BaseModel):
    id: str
    content: str
    status: Literal["pending", "in_progress", "completed"]


class PlanEvent(BaseModel):
    type: Literal["plan"] = "plan"
    revision: int
    todos: list[Todo]


class ToolStartEvent(BaseModel):
    type: Literal["tool.start"] = "tool.start"
    call_id: str
    tool: str
    label: str


class ToolEndEvent(BaseModel):
    type: Literal["tool.end"] = "tool.end"
    call_id: str
    tool: str
    ok: bool


class BasketEvent(BaseModel):
    type: Literal["basket"] = "basket"
    basket: Basket
    summary: str
    simulated: bool


class TextEvent(BaseModel):
    type: Literal["text"] = "text"
    text: str


class DoneEvent(BaseModel):
    type: Literal["done"] = "done"
    status: Literal["completed", "no_basket", "limit_reached", "timeout", "canceled"]
    simulated: bool
    model: str
    prompt_version: str
    model_calls: int
    tool_calls: int


class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    code: str
    message: str
    retryable: bool


PlannerEvent = Annotated[
    PlanEvent | ToolStartEvent | ToolEndEvent | BasketEvent | TextEvent | DoneEvent | ErrorEvent,
    Field(discriminator="type"),
]
