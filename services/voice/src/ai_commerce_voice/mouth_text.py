"""A mouth that can't speak: the call goes on with Xena's answers as text.

Used when the speech engine won't connect (no credit, an outage). Every utterance fails at
once, so the session shows its words on screen (``segment.unspoken``) and tells the customer
once that her voice is unavailable. Listening, thinking, quotes, and cards all work as usual.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from ai_commerce_voice.ports import SpeechEvent, SpeechFailed


class _SilentUtterance:
    def __init__(self, reason: str) -> None:
        self._reason = reason
        self._ended = asyncio.Event()

    async def push(self, text: str) -> None:
        return None

    async def finish(self) -> None:
        self._ended.set()

    async def cancel(self) -> None:
        self._ended.set()

    async def events(self) -> AsyncIterator[SpeechEvent]:
        yield SpeechFailed(self._reason)


class TextOnlyMouth:
    name = "text-only"

    def __init__(self, reason: str, voice: str = "Skylar") -> None:
        self.reason = reason
        self.voice = voice

    async def start(self) -> None:
        return None

    def utterance(self) -> _SilentUtterance:
        return _SilentUtterance(self.reason)

    async def synthesize(self, text: str) -> tuple[bytes, list[dict[str, Any]]]:
        raise RuntimeError(self.reason)

    async def close(self) -> None:
        return None
