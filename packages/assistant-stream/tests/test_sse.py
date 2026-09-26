from __future__ import annotations

import json

from ai_commerce_stream.events import (
    AgentHandoff,
    Card,
    Citations,
    Done,
    Error,
    Plan,
    Signals,
    TextDelta,
    Todo,
    ToolStart,
    event_json_schema,
    parse_event,
)
from ai_commerce_stream.sse import HEARTBEAT, encode, encode_v1, parse_stream, to_v1


def v1_turns_sse(event: str, data: object) -> str:
    """Byte-for-byte copy of services/assistant/turns.py:sse(), today's v1 encoder."""
    return f"event: {event}\ndata: {json.dumps(data, default=str, ensure_ascii=False)}\n\n"


def test_v1_translation_is_byte_identical_to_todays_stream() -> None:
    cases = [
        ToolStart(call_id="c1", tool="search_products", label="Searching the catalog…"),
        TextDelta(delta="Here are two sugar-free yogurts: «Skyr»"),
        Card(card={"kind": "product", "title": "Skyr", "price_minor": 199}),
        Citations(valid=[{"cite": "returns#rr-2-1"}], invalid=["returns#rr-9"]),
        Signals(signals={"intent": "product_search", "simulated": True}),
        Error(
            code="turn_failed", message="Sorry, something went wrong on our side. Please try again."
        ),
        Done(model="gpt-5.5", simulated=False, prompt_version="steph.v1"),
    ]
    expected = [
        ("status", {"tool": "search_products", "label": "Searching the catalog…"}),
        ("text", {"delta": "Here are two sugar-free yogurts: «Skyr»"}),
        ("card", {"kind": "product", "title": "Skyr", "price_minor": 199}),
        ("citations", {"valid": [{"cite": "returns#rr-2-1"}], "invalid": ["returns#rr-9"]}),
        ("signals", {"intent": "product_search", "simulated": True}),
        ("error", {"message": "Sorry, something went wrong on our side. Please try again."}),
        ("done", {"model": "gpt-5.5", "simulated": False, "prompt_version": "steph.v1"}),
    ]
    for event, (name, data) in zip(cases, expected, strict=True):
        v1 = to_v1(event)
        assert v1 == (name, data)
        assert encode_v1(*v1) == v1_turns_sse(name, data)


def test_v2_only_events_have_no_v1_form() -> None:
    plan = Plan(
        plan_id="p", revision=1, todos=[Todo(id="0", content="Pick dinners", status="pending")]
    )
    handoff = AgentHandoff(
        from_agent="steph", to_agent="xana", reason_code="start_return", shared=["order LK-1"]
    )
    assert to_v1(plan) is None
    assert to_v1(handoff) is None


def test_v2_events_carry_an_id_and_round_trip() -> None:
    event = TextDelta(turn_id="t1", agent="steph", delta="hi")
    text = encode(7, event) + HEARTBEAT

    (parsed,) = parse_stream(text)  # the heartbeat is a comment, not an event

    assert parsed["id"] == "7" and parsed["event"] == "text.delta"
    assert parsed["data"]["v"] == 2
    assert parse_event(parsed["data"]) == event


def test_every_event_type_is_in_the_published_schema() -> None:
    schema = json.dumps(event_json_schema())
    for name in (
        "turn.start",
        "agent.handoff",
        "plan",
        "tool.start",
        "text.delta",
        "card",
        "quote",
        "ask",
        "done",
        "error",
        "resumed",
    ):
        assert f'"{name}"' in schema
