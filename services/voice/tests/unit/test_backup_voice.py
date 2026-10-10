"""The backup voice: when Cartesia refuses (out of credit, 2026-10-09), Xena keeps talking."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

from ai_commerce_voice.app import VoiceFillers
from ai_commerce_voice.mouth_fallback import FallbackMouth
from ai_commerce_voice.mouth_openai import OpenAIMouth, spread_words
from ai_commerce_voice.ports import (
    Audio,
    Final,
    SpeechDone,
    SpeechEvent,
    SpeechFailed,
    TextDelta,
    Words,
)
from ai_commerce_voice.session import FillerClip
from tests.fakes import FakeBrain, FakeMouth, Step, harness


def run(test: Callable[[], Awaitable[None]]) -> None:
    asyncio.run(asyncio.wait_for(test(), 5))


class RefusingUtterance:
    def __init__(self, after_audio: bool) -> None:
        self.after_audio = after_audio
        self.texts: list[str] = []
        self.done = asyncio.Event()

    async def push(self, text: str) -> None:
        self.texts.append(text)
        self.done.set()

    async def finish(self) -> None:
        self.done.set()

    async def cancel(self) -> None:
        self.done.set()

    async def events(self) -> AsyncIterator[SpeechEvent]:
        await self.done.wait()
        if self.after_audio:
            yield Audio(b"\x01\x00" * 100)
        yield SpeechFailed("Model credits limit reached")


class RefusingMouth:
    """Cartesia out of credit: refuses to connect, or fails each utterance."""

    name = "cartesia"
    voice = "Skylar"

    def __init__(self, *, at_start: bool = False, after_audio: bool = False) -> None:
        self.at_start = at_start
        self.after_audio = after_audio
        self.utterances: list[RefusingUtterance] = []

    async def start(self) -> None:
        if self.at_start:
            raise RuntimeError("server rejected WebSocket connection: HTTP 402")

    def utterance(self) -> RefusingUtterance:
        u = RefusingUtterance(self.after_audio)
        self.utterances.append(u)
        return u

    async def synthesize(self, text: str) -> tuple[bytes, list[dict[str, Any]]]:
        raise RuntimeError("HTTP 402")

    async def close(self) -> None:
        return None


def backup() -> FakeMouth:
    m = FakeMouth()
    m.name = "openai"
    m.voice = "Marin"
    return m


async def drain(events: AsyncIterator[SpeechEvent]) -> list[SpeechEvent]:
    return [ev async for ev in events]


def test_cartesia_refusing_the_call_starts_it_on_the_backup_voice() -> None:
    async def t() -> None:
        switched: list[str] = []
        mouth = FallbackMouth(RefusingMouth(at_start=True), backup(), on_switch=switched.append)
        await mouth.start()
        assert mouth.on_backup
        assert (mouth.name, mouth.voice) == ("openai", "Marin")
        assert switched and "402" in switched[0]

    run(t)


def test_an_answer_cartesia_refuses_mid_call_is_said_word_for_word_by_the_backup() -> None:
    async def t() -> None:
        primary, spare = RefusingMouth(), backup()
        mouth = FallbackMouth(primary, spare)
        await mouth.start()
        utt = mouth.utterance()
        await utt.push("Your mat arrives")
        await utt.push("on Tuesday.")
        await utt.finish()
        events = await drain(utt.events())

        assert not any(isinstance(e, SpeechFailed) for e in events)
        assert any(isinstance(e, Audio) for e in events)
        assert isinstance(events[-1], SpeechDone)
        assert spare.spoken() == ["Your mat arrives on Tuesday."]
        # The rest of the call goes straight to the backup.
        assert mouth.on_backup
        mouth.utterance()
        assert len(primary.utterances) == 1
        assert len(spare.utterances) == 2

    run(t)


def test_a_voice_that_fails_after_speaking_is_not_said_again_in_another_voice() -> None:
    async def t() -> None:
        spare = backup()
        mouth = FallbackMouth(RefusingMouth(after_audio=True), spare)
        utt = mouth.utterance()
        await utt.push("Half an answer")
        await utt.finish()
        events = await drain(utt.events())

        assert isinstance(events[-1], SpeechFailed)
        assert spare.spoken() == []

    run(t)


def test_in_a_call_cartesia_refusing_still_gets_her_answer_spoken() -> None:
    """End to end: the answer is heard (audio sent), not shown as unspoken text."""

    async def t() -> None:
        brain = FakeBrain(scripts=[[Step(TextDelta("We have six oat milks."))]])
        spare = backup()
        h = harness(brain, filler_after_ms=5000, mouth=FallbackMouth(RefusingMouth(), spare))
        await h.session.start()
        h.ears.hear(Final("Do you have oat milk?", at=1.0))
        await asyncio.sleep(0.3)

        assert h.audio_segments()
        assert not h.of("segment.unspoken")
        assert not [e for e in h.of("error") if "text" in e["message"]]
        assert "".join(spare.spoken()).strip() == "We have six oat milks."
        await h.session.close()

    run(t)


def test_fillers_follow_the_voice_in_use() -> None:
    mouth = FallbackMouth(RefusingMouth(), backup())
    skylar = {"Let me check!": FillerClip("Let me check!", b"s", [])}
    marin = {"Let me check!": FillerClip("Let me check!", b"m", [])}
    fillers = VoiceFillers(mouth, skylar, marin)
    assert fillers["Let me check!"].pcm16 == b"s"
    mouth._switch("HTTP 402")
    assert fillers["Let me check!"].pcm16 == b"m"


class FakeOpenAI(OpenAIMouth):
    """OpenAI speech with canned audio: later clauses come back first."""

    def __init__(self) -> None:
        super().__init__("key")
        self.delays = {"One.": 0.08, "Two.": 0.0}

    async def _stream(self, text: str) -> AsyncIterator[bytes]:
        await asyncio.sleep(self.delays.get(text, 0))
        tag = b"\x01" if text == "One." else b"\x02"
        # 9600 bytes = 200 ms, in an odd-sized split that cuts a sample in two.
        yield tag * 4801
        yield tag * 4799


def test_openai_clauses_play_in_order_with_words_timed_across_them() -> None:
    async def t() -> None:
        mouth = FakeOpenAI()
        utt = mouth.utterance()
        await utt.push("One.")
        await utt.push("Two.")
        await utt.finish()
        events = await drain(utt.events())

        audio = b"".join(e.pcm16 for e in events if isinstance(e, Audio))
        assert audio == b"\x01" * 9600 + b"\x02" * 9600
        assert all(len(e.pcm16) % 2 == 0 for e in events if isinstance(e, Audio))
        words = [w for e in events if isinstance(e, Words) for w in e.words]
        assert [w["w"] for w in words] == ["One.", "Two."]
        assert words[1]["start_ms"] == 200
        assert isinstance(events[-1], SpeechDone)

    run(t)


def test_spread_words_covers_the_clause_in_order() -> None:
    words = spread_words("Your mat arrives Tuesday", 1000, 500)
    assert words[0]["start_ms"] == 500
    assert words[-1]["end_ms"] == 1500
    assert all(a["end_ms"] <= b["start_ms"] for a, b in zip(words, words[1:], strict=False))
    assert spread_words("", 1000, 0) == []
