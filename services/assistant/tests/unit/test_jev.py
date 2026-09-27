"""Jev: the request we send, how answers become decisions, and failing safe."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import httpx
import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from assistant.jev import signals as signals_mod
from assistant.jev.client import JevClient, JevError
from assistant.jev.decisions import TurnSignals, decide, voice_yes_passes
from assistant.jev.questions import INTENTS, turn_questions, voice_yes_question
from assistant.jev.simulator import JevSimulator
from assistant.jev.types import ChoiceAnswer, JevResult, NoulAnswer
from assistant.tools import untrusted

ROOT = Path(__file__).resolve().parents[4]


def _jev(handler) -> JevClient:  # type: ignore[no-untyped-def]
    return JevClient("test-key", transport=httpx.MockTransport(handler), max_attempts=2)


def test_request_matches_the_system_one_api() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers["authorization"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "model": "jev-1.13.0",
                "answers": {
                    "intent": {
                        "type": "choice",
                        "choice": "start_return",
                        "probabilities": {"start_return": 0.9, "other": 0.1},
                        "confidence": 0.84,
                    },
                    "wants_person": {"type": "noul", "noul": 0.02},
                },
                "usage": {"input_tokens": 312, "output_tokens": 20},
            },
        )

    result = _jev(handler).ask({"conversation": []}, turn_questions([]))
    assert seen["url"] == "https://api.typesafe.ai/v1/systemone"
    assert seen["auth"] == "Bearer test-key"
    body = seen["body"]
    assert body["model"] == "jev-latest" and body["state"] == {"conversation": []}
    assert body["questions"]["intent"]["type"] == "choice"
    assert set(body["questions"]["intent"]["criteria"]) == set(INTENTS)
    assert body["questions"]["frustration"]["criteria"][0] == "Calm"
    assert "target_line" not in body["questions"]  # no order lines shown yet
    assert result.model == "jev-1.13.0" and result.usage.input_tokens == 312
    assert isinstance(result.answers["intent"], ChoiceAnswer)


def test_rate_limits_are_retried_then_errors_fail_safe() -> None:
    calls = {"n": 0}

    def flaky(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, headers={"retry-after": "0"})
        return httpx.Response(200, json={"model": "jev-1.13.0", "answers": {}})

    assert _jev(flaky).ask("x", {}).model == "jev-1.13.0"
    assert calls["n"] == 2
    with pytest.raises(JevError):
        _jev(lambda r: httpx.Response(401)).ask("x", {})


def test_target_line_options_are_the_servers_order_lines() -> None:
    q = turn_questions(
        [{"line_id": "L1", "title": "Arc Headphones", "variant": "Black", "order_number": "AB12"}]
    )
    options = q["target_line"].criteria  # type: ignore[union-attr]
    assert set(options) == {"L1", "unclear"}
    assert "Arc Headphones" in (options["L1"] or "")


def _result(**answers: Any) -> JevResult:
    return JevResult(model="jev-1.13.0", answers=answers)


def test_decisions_act_only_above_their_threshold() -> None:
    confident = decide(
        _result(intent=ChoiceAnswer(choice="start_return", probabilities={}, confidence=0.81))
    )
    assert confident.acted_intent == "start_return"
    unsure = decide(
        _result(intent=ChoiceAnswer(choice="start_return", probabilities={}, confidence=0.55))
    )
    assert unsure.acted_intent is None
    line = decide(_result(target_line=ChoiceAnswer(choice="L1", probabilities={}, confidence=0.79)))
    assert line.target_line is not None and not line.target_line.act  # the line needs 0.80
    unclear = decide(
        _result(target_line=ChoiceAnswer(choice="unclear", probabilities={}, confidence=0.99))
    )
    assert not unclear.target_line.act and "show the candidates and ask" in unclear.prompt_hint()  # type: ignore[union-attr]


def test_signals_are_hints_for_the_model() -> None:
    s = decide(
        _result(
            intent=ChoiceAnswer(choice="start_return", probabilities={}, confidence=0.9),
            policy_bypass=NoulAnswer(noul=0.95),
            wants_person=NoulAnswer(noul=0.9),
        )
    )
    hint = s.prompt_hint()
    assert "start return" in hint and "decline" in hint and "handoff_to_person" in hint
    assert TurnSignals(source="off").prompt_hint() == ""


@pytest.mark.parametrize(
    ("answer", "passes"),
    [
        ("yes", True),
        ("Yes, confirm the return.", True),
        ("yeah go ahead", True),
        ("mm-hmm", False),
        ("uh-huh", False),
        ("yeah maybe", False),
        ("yes but only the blue one", False),
        ("I guess", False),
        ("yes?", False),
        ("wait", False),
        ("no", False),
    ],
)
def test_the_simulator_only_votes_yes_on_a_clear_yes(answer: str, passes: bool) -> None:
    result = JevSimulator().ask({"answer": answer}, voice_yes_question())
    assert voice_yes_passes(result) is passes


def test_no_decision_model_answer_never_passes_a_spoken_yes() -> None:
    assert voice_yes_passes(None) is False
    assert voice_yes_passes(_result(voice_yes=NoulAnswer(noul=0.89))) is False


def test_candidate_lines_come_from_order_tools_in_the_conversation() -> None:
    orders = untrusted(
        "list_my_orders",
        {
            "orders": [
                {
                    "order_id": "o1",
                    "order_number": "AB12CD34",
                    "delivered_at": "2026-09-20T00:00:00Z",
                    "items": [{"line_id": "L1", "title": "Arc Headphones", "variant": "Black"}],
                }
            ]
        },
    )
    messages = [
        HumanMessage("where is my order"),
        AIMessage("", tool_calls=[{"name": "list_my_orders", "args": {}, "id": "c1"}]),
        ToolMessage(content=orders, tool_call_id="c1", name="list_my_orders"),
        AIMessage("Order AB12CD34 was delivered."),
        HumanMessage("return the headphones"),
    ]
    state = signals_mod.turn_state(messages)
    assert state["candidate_order_lines"] == [
        {
            "line_id": "L1",
            "title": "Arc Headphones",
            "variant": "Black",
            "order_number": "AB12CD34",
            "delivered_at": "2026-09-20T00:00:00Z",
        }
    ]
    assert [t["role"] for t in state["conversation"]] == ["customer", "assistant", "customer"]


def test_jev_off_or_failing_leaves_the_turn_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(signals_mod, "decision_model", lambda: None)
    assert signals_mod.turn_signals([HumanMessage("hi")]).source == "off"

    class Broken:
        simulated = False

        def ask(self, state: Any, questions: Any) -> JevResult:
            raise JevError("timeout")

    monkeypatch.setattr(signals_mod, "decision_model", lambda: Broken())
    s = signals_mod.turn_signals([HumanMessage("return my kettle")])
    assert s.source == "error" and s.acted_intent is None


def test_simulator_baseline_on_the_labeled_set() -> None:
    """The labeled set stays valid and the baseline doesn't silently regress."""
    sys.path.insert(0, str(ROOT / "evals"))
    import jev_eval

    report = jev_eval.run(JevSimulator())
    q = report["questions"]
    assert report["cases"] >= 40
    assert q["intent"]["accuracy"] >= 0.9
    assert q["return_reason"]["acted_accuracy"] == 1.0
    assert q["target_line"]["acted_accuracy"] == 1.0
    assert q["policy_bypass"]["accuracy"] == 1.0
