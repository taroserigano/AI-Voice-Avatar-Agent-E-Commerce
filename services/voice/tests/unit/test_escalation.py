"""Luna answers; code moves a turn to Sol (decision 26), never the model's own judgment."""

from __future__ import annotations

import asyncio
from datetime import date
from typing import Any

import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from ai_commerce_voice.brain import XanaBrain, build_voice_graph, make_context, system_prompt
from ai_commerce_voice.escalation import escalation_reason
from assistant.tools import ToolContext

from .test_brain import FakeStore, ScriptModel, collect


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("My earbuds arrived broken", "dispute"),
        ("I was charged twice for my order", "dispute"),
        ("That's not right, the tablet was delivered last month", "repeat"),
        ("How long do I have to return a blender?", None),
        ("Do you have organic whole milk?", None),
        ("Where's my order?", None),
    ],
)
def test_which_turns_go_to_the_stronger_model(text: str, reason: str | None) -> None:
    assert escalation_reason(text, []) == reason


def test_asking_the_same_thing_again_escalates() -> None:
    history = [HumanMessage("do you have the arc headphones in sand")]
    assert escalation_reason("Do you have the Arc headphones in Sand?", history)


def brain(weak: ScriptModel, strong: ScriptModel | None) -> XanaBrain:
    ctx = ToolContext(client=FakeStore(), agent="xana", first_name="Alice", voice=True)  # type: ignore[arg-type]
    return XanaBrain(
        build_voice_graph(InMemorySaver()),
        conversation_id="conv-esc",
        ctx=ctx,
        voice=make_context(
            weak,
            system=system_prompt("Alice", date(2026, 9, 26), None),
            max_tool_calls=6,
            strong=strong,
            strong_name="sol",
        ),
        model="luna",
        simulated=True,
    )


def test_a_product_question_stays_on_the_fast_model() -> None:
    weak = ScriptModel(replies=["Yes, it's $3.99."], seen=[])
    strong = ScriptModel(replies=[], seen=[])
    asyncio.run(collect(brain(weak, strong).turn("Do you have oat milk?")))
    assert len(weak.seen) == 1 and strong.seen == []


def test_a_dispute_is_answered_by_the_stronger_model() -> None:
    weak = ScriptModel(replies=[], seen=[])
    strong = ScriptModel(replies=["I'm sorry. Which item was it?"], seen=[])
    asyncio.run(collect(brain(weak, strong).turn("I was charged twice for my order")))
    assert weak.seen == [] and len(strong.seen) == 1


def test_two_failed_tools_move_the_rest_of_the_turn_up() -> None:
    bad: Any = ("get_order_status", {"order_id": "not-an-id"})
    weak = ScriptModel(replies=[bad, bad], seen=[])
    strong = ScriptModel(replies=["Let me get a person to check that order."], seen=[])
    asyncio.run(collect(brain(weak, strong).turn("Where's my order?")))
    assert len(weak.seen) == 2 and len(strong.seen) == 1


def test_without_a_stronger_model_every_turn_stays_on_the_fast_one() -> None:
    weak = ScriptModel(replies=["Sorry about that. Which item?"], seen=[])
    asyncio.run(collect(brain(weak, None).turn("I was charged twice")))
    assert len(weak.seen) == 1
