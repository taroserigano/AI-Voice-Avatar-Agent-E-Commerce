"""The real engines, end to end: Skylar speaks a question, the live transcriber hears it.

Costs a few cents. Opt in with ``VOICE_LIVE=1``. Prints the measured latencies.
"""

from __future__ import annotations

import asyncio
import os
import time

import pytest

from ai_commerce_voice.config import VoiceSettings
from ai_commerce_voice.ears_openai import OpenAILiveEars
from ai_commerce_voice.mouth_cartesia import CartesiaMouth
from ai_commerce_voice.ports import (
    Audio,
    Draft,
    Final,
    Partial,
    SpeechStarted,
    SpeechStopped,
    Words,
)

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(os.environ.get("VOICE_LIVE") != "1", reason="set VOICE_LIVE=1"),
]

QUESTION = "Hi, where is my order from last week? It still hasn't arrived."


def mouth(s: VoiceSettings) -> CartesiaMouth:
    assert s.cartesia_api_key
    return CartesiaMouth(
        s.cartesia_api_key,
        model=s.cartesia_model,
        version=s.cartesia_version,
        voice_id=s.cartesia_voice_id,
    )


def test_skylar_streams_first_audio_fast_with_word_timings() -> None:
    async def t() -> None:
        m = mouth(VoiceSettings())
        await m.start()
        try:
            firsts = []
            for text in (
                "Let me check on that order.",
                "Your refund of twelve dollars is on its way.",
            ):
                utt = m.utterance()
                started = time.perf_counter()
                await utt.push(text)
                await utt.finish()
                first = None
                words: list[dict[str, object]] = []
                audio = 0
                async for ev in utt.events():
                    if isinstance(ev, Audio):
                        first = first or time.perf_counter()
                        audio += len(ev.pcm16)
                    elif isinstance(ev, Words):
                        words += ev.words
                assert first is not None and audio > 24_000
                firsts.append((first - started) * 1000)
                assert [w["w"] for w in words][:2] == text.split()[:2]
            print(f"\nfirst audio ms: {[round(f) for f in firsts]}")
            assert min(firsts) < 600

            # Barge-in: cancelling mid-answer stops it.
            utt = m.utterance()
            await utt.push(
                "This is a long answer that the customer is going to interrupt before it ends."
            )
            await utt.cancel()
            assert utt.canceled
        finally:
            await m.close()

    asyncio.run(t())


def test_the_live_transcriber_hears_skylar_and_ends_the_turn_quickly() -> None:
    async def t() -> None:
        s = VoiceSettings()
        m = mouth(s)
        await m.start()
        pcm, _ = await m.synthesize(QUESTION)
        await m.close()
        assert s.openai_api_key
        ears = OpenAILiveEars(s.openai_api_key, model=s.voice_stt_model)
        await ears.start()
        got: list[tuple[float, object]] = []

        async def listen() -> None:
            async for ev in ears.events():
                got.append((time.perf_counter(), ev))
                if isinstance(ev, Final):
                    return

        listener = asyncio.create_task(listen())
        frame = 960  # 20 ms
        silence = b"\x00\x00" * 480
        started = time.perf_counter()
        for _ in range(15):
            await ears.send_audio(silence)
            await asyncio.sleep(0.02)
        for i in range(0, len(pcm), frame):
            await ears.send_audio(pcm[i : i + frame])
            await asyncio.sleep(0.02)
        spoken_end = time.perf_counter()
        for _ in range(100):
            await ears.send_audio(silence)
            await asyncio.sleep(0.02)
            if listener.done():
                break
        await asyncio.wait_for(listener, 10)
        await ears.close()

        def at(kind: type) -> float | None:
            return next(((ts - spoken_end) * 1000 for ts, ev in got if isinstance(ev, kind)), None)

        partials = [ev for _, ev in got if isinstance(ev, Partial)]
        final = next(ev for _, ev in got if isinstance(ev, Final))
        draft = next((ev for _, ev in got if isinstance(ev, Draft)), None)
        first_partial = next(
            ((ts - started) * 1000 for ts, ev in got if isinstance(ev, Partial)), None
        )
        print(
            f"\nspeech {len(pcm) / 48:.0f} ms; first words at {first_partial:.0f} ms from start; "
            f"after end of speech: stopped {at(SpeechStopped):.0f} ms, draft {at(Draft):.0f} ms, "
            f"final {at(Final):.0f} ms"
        )
        print(f"draft: {draft.text if draft else None!r}\nfinal: {final.text!r}")
        assert at(SpeechStarted) is not None
        assert len(partials) >= 3  # words arrived while "the customer" was still talking
        assert "order" in final.text.lower() and "last week" in final.text.lower()
        assert at(Draft) is not None and at(Draft) < 1500

    asyncio.run(t())
