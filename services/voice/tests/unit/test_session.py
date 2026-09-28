"""The voice session's turn-taking: streaming, fillers, barge-in, and the confirmation guard."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from ai_commerce_voice.ports import (
    Draft,
    Final,
    QuoteOut,
    SpeechStarted,
    SpeechStopped,
    TextDelta,
    ToolStarted,
)
from ai_commerce_voice.speech_text import speakable
from tests.fakes import FakeBrain, Harness, Step, harness

QUOTE = {
    "kind": "return_quote",
    "quote_id": "q-1",
    "total_refund_minor": 1263,
    "readback": "Here's your return: 1 × Oat milk. You'll get $12.63 back. Do you want me to "
    "confirm this return?",
}


def run(test: Callable[[], Awaitable[None]]) -> None:
    asyncio.run(asyncio.wait_for(test(), 5))


async def settle(h: Harness, s: float = 0.05) -> None:
    await asyncio.sleep(s)
    if h.session._turn:
        await asyncio.wait_for(asyncio.shield(h.session._turn), 3)
    await asyncio.sleep(0.01)


async def play_all(h: Harness) -> None:
    """The browser reports every segment played in full."""
    for m in h.of("segment.end"):
        await h.session.on_message({"type": "played", "segment": m["segment"], "complete": True})


def test_an_answer_streams_as_audio_with_word_timed_captions() -> None:
    async def t() -> None:
        brain = FakeBrain(
            scripts=[
                [
                    Step(TextDelta("Your order shipped yesterday, and it")),
                    Step(TextDelta(" arrives Friday.")),
                ]
            ]
        )
        h = harness(brain)
        await h.session.start()
        h.ears.hear(SpeechStarted(at=1.0))
        h.ears.hear(SpeechStopped(at=2.0))
        h.ears.hear(Final("Where's my order?", at=2.2))
        await settle(h)

        assert brain.heard == ["Where's my order?"]
        states = [m["state"] for m in h.of("state")]
        assert states[:4] == ["listening", "hearing", "thinking", "speaking"]
        # The first clause went to the speech engine before the sentence was finished.
        assert h.mouth.utterances[0].texts == [
            "Your order shipped yesterday,",
            "and it arrives Friday.",
        ]
        assert len(h.mouth.utterances) == 1  # one voice context: prosody carries across chunks
        (start,) = h.of("segment.start")
        assert start["kind"] == "answer"
        assert set(h.audio_segments()) == {start["segment"]}
        assert sum(len(m["words"]) for m in h.of("segment.words")) == 8
        (done,) = h.of("turn.done")
        assert done["metrics"]["filler"] is False and done["metrics"]["stt_ms"] == 200.0
        assert "first_audio_ms" in done["metrics"]

        await play_all(h)
        assert h.of("state")[-1]["state"] == "listening"
        await h.session.close()

    run(t)


def test_a_slow_answer_gets_one_filler_first_and_never_twice() -> None:
    async def t() -> None:
        brain = FakeBrain(scripts=[[Step(TextDelta("Here's what I found."), delay_s=0.25)]])
        h = harness(brain, filler_after_ms=60)
        await h.session.start()
        h.ears.hear(Final("What's your return policy for opened electronics?", at=1.0))
        await settle(h, 0.4)

        starts = h.of("segment.start")
        assert [s["kind"] for s in starts] == ["filler", "answer"]
        filler, answer = starts[0]["segment"], starts[1]["segment"]
        order = h.audio_segments()
        # All filler audio is queued before any answer audio, so they never interleave.
        assert order.index(answer) > max(i for i, s in enumerate(order) if s == filler)
        (text,) = [m["text"] for m in h.of("segment.text") if m["segment"] == filler]
        assert text in h.session.fillers
        assert h.of("turn.done")[0]["metrics"]["filler"] is True
        await h.session.close()

    run(t)


def test_a_fast_answer_gets_no_filler() -> None:
    async def t() -> None:
        h = harness(
            FakeBrain(scripts=[[Step(TextDelta("It arrives Friday."))]]), filler_after_ms=300
        )
        await h.session.start()
        h.ears.hear(Final("When does it arrive?", at=1.0))
        await settle(h, 0.4)
        assert [s["kind"] for s in h.of("segment.start")] == ["answer"]
        await h.session.close()

    run(t)


def test_a_tool_call_before_any_words_says_what_xana_is_doing() -> None:
    async def t() -> None:
        brain = FakeBrain(
            scripts=[
                [
                    Step(ToolStarted("get_order_status", "Checking your order…")),
                    Step(TextDelta("It's out for delivery."), delay_s=0.05),
                ]
            ]
        )
        h = harness(brain, filler_after_ms=5000)
        await h.session.start()
        h.ears.hear(Final("Where is order E2EA6BC6?", at=1.0))
        await settle(h, 0.2)

        assert h.of("tool") == [
            {"type": "tool", "name": "get_order_status", "label": "Checking your order…"}
        ]
        filler_text = h.of("segment.text")[0]["text"]
        assert filler_text in (
            "Let me check on that order.",
            "Let me look that order up.",
            "One sec, checking that order.",
        )
        await h.session.close()

    run(t)


def test_talking_over_xana_stops_her_at_once() -> None:
    async def t() -> None:
        brain = FakeBrain(
            scripts=[
                [
                    Step(TextDelta("Your refund is on its way. ")),
                    Step(TextDelta("It usually takes five days."), delay_s=1.0),
                ]
            ]
        )
        h = harness(brain)
        await h.session.start()
        h.ears.hear(Final("Where's my refund?", at=1.0))
        await asyncio.sleep(0.1)
        assert h.session.state == "speaking"

        h.ears.hear(SpeechStarted(at=2.0))
        await asyncio.sleep(0.4)  # longer than the barge-in threshold

        (drop,) = h.of("drop")
        assert drop["segments"] == [h.of("segment.start")[0]["segment"]]
        assert h.mouth.utterances[0].canceled
        assert h.session.state == "hearing"
        assert h.of("turn.done") == []  # the rest of the answer was never said
        await h.session.close()

    run(t)


def test_a_cough_while_xana_talks_doesnt_stop_her() -> None:
    async def t() -> None:
        brain = FakeBrain(
            scripts=[
                [
                    Step(TextDelta("Your refund is on its way.")),
                    Step(TextDelta(" Anything else?"), delay_s=0.4),
                ]
            ]
        )
        h = harness(brain)
        await h.session.start()
        h.ears.hear(Final("Where's my refund?", at=1.0))
        await asyncio.sleep(0.1)
        h.ears.hear(SpeechStarted(at=2.0))
        await asyncio.sleep(0.05)
        h.ears.hear(SpeechStopped(at=2.05))
        await settle(h, 0.5)
        assert h.of("drop") == []
        assert h.mouth.spoken() == ["Your refund is on its way. Anything else?"]
        await h.session.close()

    run(t)


def test_noise_is_not_a_turn() -> None:
    async def t() -> None:
        h = harness()
        await h.session.start()
        h.ears.hear(Final("Um...", at=1.0))
        await asyncio.sleep(0.05)
        assert h.brain.heard == [] and h.of("user.final") == []
        await h.session.close()

    run(t)


async def _quoted(h: Harness) -> None:
    await h.session.start()
    h.ears.hear(Final("Return the oat milk, it was spoiled.", at=1.0))
    await settle(h)


def test_the_quote_read_back_is_spoken_word_for_word_from_code() -> None:
    async def t() -> None:
        brain = FakeBrain(scripts=[[Step(TextDelta("I can do that.")), Step(QuoteOut(QUOTE))]])
        h = harness(brain)
        await _quoted(h)
        assert h.of("quote")[0]["quote"]["quote_id"] == "q-1"
        confirm = [s for s in h.of("segment.start") if s["kind"] == "confirm"]
        assert len(confirm) == 1
        assert h.mouth.spoken()[-1] == speakable(
            QUOTE["readback"]
        )  # "1 × Oat milk" -> "1 Oat milk"
        await h.session.close()

    run(t)


def test_a_yes_before_the_read_back_finished_playing_does_not_confirm() -> None:
    async def t() -> None:
        h = harness(FakeBrain(scripts=[[Step(QuoteOut(QUOTE))]]))
        await _quoted(h)
        h.ears.hear(Final("Yes", at=5.0))
        await settle(h)
        assert h.of("confirm.result")[-1]["decision"] == "unclear"
        assert h.brain.heard == [
            "Return the oat milk, it was spoiled."
        ]  # the model never saw "yes"
        await h.session.close()

    run(t)


def test_a_clear_yes_after_the_read_back_lets_the_browser_confirm() -> None:
    async def t() -> None:
        h = harness(
            FakeBrain(
                scripts=[[Step(QuoteOut(QUOTE))]],
                resumes=[[Step(TextDelta("Done. Your refund is on its way."))]],
            )
        )
        await _quoted(h)
        await play_all(h)
        h.ears.hear(Final("Yes, confirm.", at=5.0))
        await settle(h)
        assert h.of("confirm.result")[-1] == {
            "type": "confirm.result",
            "decision": "yes",
            "quote_id": "q-1",
        }
        assert h.mouth.spoken()[-1] == "Thanks, confirming your return now."
        assert h.brain.resumed == []  # nothing happens until the store says it's confirmed

        # The browser confirmed with the store and says so; the agent picks up from there.
        await h.session.on_message(
            {"type": "quote.outcome", "quote_id": "q-1", "outcome": "confirmed"}
        )
        await settle(h)
        assert h.brain.resumed == ["confirmed"]
        assert h.session.quote is None
        await h.session.close()

    run(t)


def test_a_new_request_instead_of_an_answer_closes_the_quote_quietly() -> None:
    async def t() -> None:
        h = harness(
            FakeBrain(
                scripts=[
                    [Step(QuoteOut(QUOTE))],
                    [Step(TextDelta("Your headphones arrive Friday."))],
                ]
            )
        )
        await _quoted(h)
        await play_all(h)
        h.ears.hear(Final("Actually, where are my headphones from last week?", at=5.0))
        await settle(h)
        assert h.brain.resumed == ["superseded"]
        assert h.brain.heard[-1] == "Actually, where are my headphones from last week?"
        assert h.session.quote is None
        await h.session.close()

    run(t)


def test_a_quote_outcome_for_another_quote_is_ignored() -> None:
    async def t() -> None:
        h = harness(FakeBrain(scripts=[[Step(QuoteOut(QUOTE))]]))
        await _quoted(h)
        await h.session.on_message(
            {"type": "quote.outcome", "quote_id": "someone-elses", "outcome": "confirmed"}
        )
        await asyncio.sleep(0.05)
        assert h.brain.resumed == [] and h.session.quote is not None
        await h.session.close()

    run(t)


def test_muting_closes_open_speech_and_stops_sending_audio() -> None:
    async def t() -> None:
        h = harness()
        await h.session.start()
        await h.session.on_audio(b"\x05\x00" * 480)
        await h.session.on_message({"type": "mute", "muted": True})
        sent = len(h.ears.audio)
        await h.session.on_audio(b"\x05\x00" * 480)
        assert len(h.ears.audio) == sent  # nothing more after the silence that closes speech
        assert h.ears.audio[-1] == b"\x00\x00" * 24_000
        await h.session.close()

    run(t)


def test_xana_starts_thinking_on_the_live_transcript_and_keeps_it_when_confirmed() -> None:
    async def t() -> None:
        brain = FakeBrain(scripts=[[Step(TextDelta("It arrives Friday."), delay_s=0.1)]])
        h = harness(brain)
        await h.session.start()
        h.ears.hear(SpeechStopped(at=1.0))
        h.ears.hear(Draft("When does my order arrive", item_id="item-1", at=1.0))
        await asyncio.sleep(0.02)
        h.ears.hear(Final("When does my order arrive?", at=1.3, item_id="item-1"))
        await settle(h, 0.3)
        assert brain.heard == ["When does my order arrive"]  # no second run for a full stop
        assert brain.message_ids == ["item-1"]
        await h.session.close()

    run(t)


def test_a_corrected_final_transcript_replaces_the_draft_turn() -> None:
    async def t() -> None:
        brain = FakeBrain(
            scripts=[
                [Step(TextDelta("wrong"), delay_s=0.3)],
                [Step(TextDelta("Your refund posted."))],
            ]
        )
        h = harness(brain, filler_after_ms=5000)
        await h.session.start()
        h.ears.hear(Draft("Where's my refill", item_id="item-2", at=1.0))
        await asyncio.sleep(0.02)
        h.ears.hear(Final("Where's my refund?", at=1.3, item_id="item-2"))
        await settle(h, 0.3)
        assert brain.heard == ["Where's my refill", "Where's my refund?"]
        assert brain.message_ids == ["item-2", "item-2"]  # replaces the draft in history
        assert h.mouth.spoken() == ["Your refund posted."]
        assert h.of("user.final")[-1]["text"] == "Where's my refund?"
        await h.session.close()

    run(t)


def test_a_reply_to_a_quote_waits_for_the_final_transcript() -> None:
    async def t() -> None:
        h = harness(FakeBrain(scripts=[[Step(QuoteOut(QUOTE))]]))
        await _quoted(h)
        await play_all(h)
        h.ears.hear(Draft("yes", item_id="item-3", at=5.0))
        await asyncio.sleep(0.05)
        assert h.of("confirm.result") == []
        h.ears.hear(Final("Yes, confirm.", at=5.3, item_id="item-3"))
        await settle(h)
        assert h.of("confirm.result")[-1]["decision"] == "yes"
        await h.session.close()

    run(t)


def test_the_store_answering_doesnt_cut_off_the_confirming_line_or_add_a_filler() -> None:
    async def t() -> None:
        brain = FakeBrain(
            scripts=[[Step(QuoteOut(QUOTE))]],
            resumes=[[Step(TextDelta("It's confirmed; your refund is on its way."), delay_s=1.2)]],
        )
        h = harness(brain, filler_after_ms=60, first_audio_s=0.05)
        await _quoted(h)
        await play_all(h)
        h.ears.hear(Final("Yes, confirm.", at=5.0))
        while not h.of("confirm.result"):
            await asyncio.sleep(0.005)
        # The browser confirmed with the store almost at once.
        await h.session.on_message(
            {"type": "quote.outcome", "quote_id": "q-1", "outcome": "confirmed"}
        )
        await settle(h, 1.5)
        spoken = h.mouth.spoken()
        assert "Thanks, confirming your return now." in spoken
        assert spoken[-1] == "It's confirmed; your refund is on its way."
        assert h.of("drop") == []
        kinds = [s["kind"] for s in h.of("segment.start")]
        assert "filler" not in kinds[kinds.index("confirm") :]
        await h.session.close()

    run(t)


def test_the_read_back_caption_is_exact_but_the_voice_skips_the_times_sign() -> None:
    async def t() -> None:
        quote = {**QUOTE, "readback": "Here's your return: 1 × Oat milk. Confirm?"}
        h = harness(FakeBrain(scripts=[[Step(QuoteOut(quote))]]))
        await _quoted(h)
        confirm = next(s["segment"] for s in h.of("segment.start") if s["kind"] == "confirm")
        caption = [m["text"] for m in h.of("segment.text") if m["segment"] == confirm]
        assert caption == ["Here's your return: 1 × Oat milk. Confirm?"]
        assert h.mouth.spoken()[-1] == "Here's your return: 1 Oat milk. Confirm?"
        await h.session.close()

    run(t)
