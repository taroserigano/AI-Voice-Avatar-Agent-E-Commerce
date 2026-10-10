"""In-memory ears, mouth, and brain for testing the voice session without any vendor."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Literal

from ai_commerce_voice.ports import (
    AgentEvent,
    Audio,
    HearingEvent,
    SpeechDone,
    SpeechEvent,
    TurnEnded,
    Words,
)
from ai_commerce_voice.session import FillerClip, VoiceSession


class FakeEars:
    name = "fake"
    model = "fake-stt"

    def __init__(self) -> None:
        self.queue: asyncio.Queue[HearingEvent | None] = asyncio.Queue()
        self.audio: list[bytes] = []

    async def start(self) -> None:
        return None

    async def send_audio(self, pcm16: bytes) -> None:
        self.audio.append(pcm16)

    async def events(self) -> AsyncIterator[HearingEvent]:
        while (ev := await self.queue.get()) is not None:
            yield ev

    async def close(self) -> None:
        await self.queue.put(None)

    def hear(self, ev: HearingEvent) -> None:
        self.queue.put_nowait(ev)


class FakeUtterance:
    def __init__(self, mouth: FakeMouth) -> None:
        self.mouth = mouth
        self.queue: asyncio.Queue[SpeechEvent] = asyncio.Queue()
        self.texts: list[str] = []
        self.canceled = False
        self.at_ms = 0

    async def push(self, text: str) -> None:
        self.texts.append(text)
        await asyncio.sleep(self.mouth.first_audio_s)
        words = []
        for w in text.split():
            words.append({"w": w, "start_ms": self.at_ms, "end_ms": self.at_ms + 200})
            self.at_ms += 250
        await self.queue.put(Words(words))
        await self.queue.put(Audio(b"\x01\x00" * 2400 * max(1, len(words))))

    async def finish(self) -> None:
        await self.queue.put(SpeechDone())

    async def cancel(self) -> None:
        self.canceled = True
        await self.queue.put(SpeechDone())

    async def events(self) -> AsyncIterator[SpeechEvent]:
        while True:
            ev = await self.queue.get()
            yield ev
            if isinstance(ev, SpeechDone):
                return


class FakeMouth:
    name = "fake"
    voice = "Skylar"

    def __init__(self, first_audio_s: float = 0.0) -> None:
        self.first_audio_s = first_audio_s
        self.utterances: list[FakeUtterance] = []

    async def start(self) -> None:
        return None

    def utterance(self) -> FakeUtterance:
        u = FakeUtterance(self)
        self.utterances.append(u)
        return u

    async def synthesize(self, text: str) -> tuple[bytes, list[dict[str, Any]]]:
        return b"\x02\x00" * 4800, [{"w": w, "start_ms": 0, "end_ms": 100} for w in text.split()]

    async def close(self) -> None:
        return None

    def spoken(self) -> list[str]:
        return [" ".join(u.texts) for u in self.utterances]


@dataclass
class Step:
    event: AgentEvent
    delay_s: float = 0.0


@dataclass
class FakeBrain:
    model: str = "fake-llm"
    simulated: bool = True
    scripts: list[list[Step]] = field(default_factory=list)
    resumes: list[list[Step]] = field(default_factory=list)
    heard: list[str] = field(default_factory=list)
    resumed: list[str] = field(default_factory=list)
    message_ids: list[str | None] = field(default_factory=list)

    async def _play(self, steps: list[Step]) -> AsyncIterator[AgentEvent]:
        for step in steps:
            if step.delay_s:
                await asyncio.sleep(step.delay_s)
            yield step.event
        if not any(isinstance(s.event, TurnEnded) for s in steps):
            yield TurnEnded()

    async def turn(self, text: str, message_id: str | None = None) -> AsyncIterator[AgentEvent]:
        self.heard.append(text)
        self.message_ids.append(message_id)
        steps = self.scripts.pop(0) if self.scripts else []
        async for ev in self._play(steps):
            yield ev

    async def resume(
        self, outcome: Literal["confirmed", "declined", "superseded"]
    ) -> AsyncIterator[AgentEvent]:
        self.resumed.append(outcome)
        steps = self.resumes.pop(0) if self.resumes else []
        async for ev in self._play(steps):
            yield ev

    async def pending_quote(self) -> dict[str, Any] | None:
        return None


def strict_yes(text: str, *, final: bool, readback_complete: bool, speech_ms: float) -> str:
    t = text.lower().strip(" .!")
    if not (final and readback_complete):
        return "unclear"
    if t in ("yes", "yes confirm", "yes, confirm"):
        return "yes"
    if t in ("no", "no thanks"):
        return "no"
    return "unclear"


@dataclass
class Harness:
    session: VoiceSession
    ears: FakeEars
    mouth: FakeMouth
    brain: FakeBrain
    sent: list[dict[str, Any]] = field(default_factory=list)
    audio: list[bytes] = field(default_factory=list)

    def of(self, kind: str) -> list[dict[str, Any]]:
        return [m for m in self.sent if m["type"] == kind]

    def kinds(self) -> list[str]:
        return [m["type"] for m in self.sent]

    def audio_segments(self) -> list[int]:
        return [int.from_bytes(a[:4], "little") for a in self.audio]


def harness(
    brain: FakeBrain | None = None,
    *,
    filler_after_ms: int = 900,
    first_audio_s: float = 0.0,
    mouth: Any = None,
) -> Harness:
    ears, mouth = FakeEars(), mouth or FakeMouth(first_audio_s)
    brain = brain or FakeBrain()
    sent: list[dict[str, Any]] = []
    audio: list[bytes] = []

    async def send_json(msg: dict[str, Any]) -> None:
        sent.append(msg)

    async def send_bytes(b: bytes) -> None:
        audio.append(b)

    from ai_commerce_voice.fillers import all_phrases

    fillers = {p: FillerClip(p, b"\x03\x00" * 9600, []) for p in all_phrases()}
    session = VoiceSession(
        send_json=send_json,
        send_bytes=send_bytes,
        ears=ears,
        mouth=mouth,
        brain=brain,
        confirm=strict_yes,  # type: ignore[arg-type]
        fillers=fillers,
        filler_after_ms=filler_after_ms,
    )
    return Harness(session, ears, mouth, brain, sent, audio)
