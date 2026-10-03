"""What the voice session needs from its three engines: ears, brain, and voice.

The session (session.py) only talks to these protocols, so the real engines (OpenAI streaming
transcription, the LangGraph agent, Cartesia) and the test fakes are interchangeable.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

# --- Ears: streaming speech-to-text with voice activity detection -------------------------


@dataclass(frozen=True)
class SpeechStarted:
    at: float


@dataclass(frozen=True)
class SpeechStopped:
    at: float


@dataclass(frozen=True)
class Partial:
    text: str


@dataclass(frozen=True)
class Draft:
    """The live transcript at the end of speech: good enough to start thinking on."""

    text: str
    item_id: str
    at: float


@dataclass(frozen=True)
class Final:
    text: str
    at: float
    speech_ms: float = 0.0
    item_id: str | None = None


@dataclass(frozen=True)
class SttFailed:
    message: str


HearingEvent = SpeechStarted | SpeechStopped | Partial | Draft | Final | SttFailed


class Ears(Protocol):
    name: str
    model: str

    async def start(self) -> None: ...
    async def send_audio(self, pcm16: bytes) -> None: ...
    def events(self) -> AsyncIterator[HearingEvent]: ...
    async def close(self) -> None: ...


# --- Voice: streaming text-to-speech -------------------------------------------------------


@dataclass(frozen=True)
class Audio:
    pcm16: bytes


@dataclass(frozen=True)
class Words:
    words: list[dict[str, Any]]  # {"w", "start_ms", "end_ms"}, from the start of the segment


@dataclass(frozen=True)
class SpeechDone:
    pass


@dataclass(frozen=True)
class SpeechFailed:
    message: str


SpeechEvent = Audio | Words | SpeechDone | SpeechFailed


class Utterance(Protocol):
    """One continuous spoken answer. Text arrives in chunks; prosody carries across them."""

    async def push(self, text: str) -> None: ...
    async def finish(self) -> None: ...
    async def cancel(self) -> None: ...
    def events(self) -> AsyncIterator[SpeechEvent]: ...


class Mouth(Protocol):
    name: str
    voice: str

    async def start(self) -> None: ...
    def utterance(self) -> Utterance: ...
    async def synthesize(self, text: str) -> tuple[bytes, list[dict[str, Any]]]: ...
    async def close(self) -> None: ...


# --- Brain: the support agent --------------------------------------------------------------


@dataclass(frozen=True)
class TextDelta:
    text: str


@dataclass(frozen=True)
class ToolStarted:
    name: str
    label: str


@dataclass(frozen=True)
class CardOut:
    card: dict[str, Any]


@dataclass(frozen=True)
class QuoteOut:
    """The turn paused on a return quote; only the customer can confirm it."""

    quote: dict[str, Any]


@dataclass(frozen=True)
class TurnEnded:
    citations: list[dict[str, Any]] = field(default_factory=list)
    # Sections the answer cited but the call never retrieved (removed from what's shown).
    invalid_citations: list[str] = field(default_factory=list)
    first_token_ms: float | None = None
    error: str | None = None


AgentEvent = TextDelta | ToolStarted | CardOut | QuoteOut | TurnEnded


class Brain(Protocol):
    model: str
    simulated: bool

    def turn(self, text: str, message_id: str | None = None) -> AsyncIterator[AgentEvent]: ...
    def resume(
        self, outcome: Literal["confirmed", "declined", "superseded"]
    ) -> AsyncIterator[AgentEvent]: ...
    async def pending_quote(self) -> dict[str, Any] | None: ...


class ConfirmRule(Protocol):
    """The app's own check of a spoken yes (never the model)."""

    def __call__(
        self, text: str, *, final: bool, readback_complete: bool, speech_ms: float
    ) -> Literal["yes", "no", "unclear"]: ...
