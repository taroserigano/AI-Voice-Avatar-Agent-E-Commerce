"""The spoken-confirmation gate: only a clear, final yes after the full read-back confirms."""

from __future__ import annotations

import pytest

from assistant import voice
from assistant.jev.simulator import JevSimulator


@pytest.fixture(autouse=True)
def _simulated_jev(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(voice, "decision_model", lambda: JevSimulator())


def decide(text: str, **kw: object) -> str:
    args = {"final": True, "readback_complete": True, "speech_ms": 900, **kw}
    return voice.confirm_decision(text, **args).decision  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("yes", "yes"),
        ("Yes, confirm the return.", "yes"),
        ("yeah, go ahead", "yes"),
        ("confirm", "yes"),
        ("mm-hmm", "unclear"),
        ("uh-huh", "unclear"),
        ("yeah maybe", "unclear"),
        ("yes but only one of them", "unclear"),
        ("I guess", "unclear"),
        ("yes?", "unclear"),
        ("wait", "unclear"),
        ("what's the refund again", "unclear"),
        ("honey can you grab the door", "unclear"),
        ("no", "no"),
        ("cancel", "no"),
        ("no, don't", "no"),
    ],
)
def test_only_a_clear_yes_confirms(text: str, expected: str) -> None:
    assert decide(text) == expected


def test_an_interrupted_read_back_or_partial_transcript_never_confirms() -> None:
    assert decide("yes", readback_complete=False) == "unclear"
    assert decide("yes", final=False) == "unclear"
    assert decide("yes", speech_ms=120) == "unclear"


def test_jev_can_block_but_never_cause_a_confirmation(monkeypatch: pytest.MonkeyPatch) -> None:
    from assistant.jev.types import JevResult, NoulAnswer

    class Doubtful:
        simulated = True

        def ask(self, state: object, questions: object) -> JevResult:
            return JevResult(model="x", answers={"voice_yes": NoulAnswer(noul=0.5)})

    class Eager:
        simulated = True

        def ask(self, state: object, questions: object) -> JevResult:
            return JevResult(model="x", answers={"voice_yes": NoulAnswer(noul=0.99)})

    monkeypatch.setattr(voice, "decision_model", lambda: Doubtful())
    assert decide("yes") == "unclear"  # the rule said yes, Jev wasn't sure: ask again
    monkeypatch.setattr(voice, "decision_model", lambda: Eager())
    assert decide("mm-hmm") == "unclear"  # Jev said yes, the rule didn't: still no


def test_answers_are_spoken_without_markup() -> None:
    assert voice.speakable(
        "You have 30 days. [[cite:returns-and-refunds#rr-2-1]]\n- **Free** returns"
    ) == ("You have 30 days. Free returns")
