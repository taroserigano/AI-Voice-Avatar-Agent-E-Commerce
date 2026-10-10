"""Xena's backup voice: OpenAI speech (gpt-4o-mini-tts), used when Cartesia refuses.

Cartesia ran out of credit on 2026-10-09 and every call went to text. This voice keeps her
talking (a different voice, said on screen). It has no streaming context like Cartesia's, so
each clause the model sends is its own request: they're fetched up to ``AHEAD`` at a time and
played strictly in order. Measured (2026-10-10): first audio ~0.5 s on a warm connection,
~1.1-1.4 s cold, versus ~0.13 s for Cartesia.

OpenAI returns no word timings, so each clause's words are spread over its audio by length
once the clause has arrived; captions run a clause behind at most.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from typing import Any

import httpx

from ai_commerce_voice.ports import Audio, SpeechDone, SpeechEvent, SpeechFailed, Words

log = logging.getLogger(__name__)

URL = "https://api.openai.com/v1/audio/speech"
BYTES_PER_MS = 48  # 24 kHz, 16-bit mono PCM
AHEAD = 2
INSTRUCTIONS = (
    "A warm, upbeat, friendly store assistant on a phone call. Natural conversational pace, "
    "clear and relaxed; never theatrical."
)


def spread_words(text: str, duration_ms: int, offset_ms: int) -> list[dict[str, Any]]:
    """Word timings for ``text`` spoken over ``duration_ms``, by each word's share of the
    letters (a long word takes longer to say)."""
    words = text.split()
    if not words or duration_ms <= 0:
        return []
    weights = [len(w) + 1 for w in words]
    total = sum(weights)
    out: list[dict[str, Any]] = []
    at = 0.0
    for w, weight in zip(words, weights, strict=True):
        span = duration_ms * weight / total
        out.append(
            {"w": w, "start_ms": round(offset_ms + at), "end_ms": round(offset_ms + at + span)}
        )
        at += span
    return out


class OpenAIUtterance:
    def __init__(self, mouth: OpenAIMouth) -> None:
        self.mouth = mouth
        self.queue: asyncio.Queue[SpeechEvent] = asyncio.Queue()
        self.pieces: asyncio.Queue[str | None] = asyncio.Queue()
        self.canceled = False
        self.finished = False
        self._runner: asyncio.Task[None] | None = None

    def _run(self) -> None:
        if self._runner is None:
            self._runner = asyncio.create_task(self._speak())

    async def push(self, text: str) -> None:
        if self.canceled or self.finished or not text.strip():
            return
        self._run()
        await self.pieces.put(text.strip())

    async def finish(self) -> None:
        if self.canceled or self.finished:
            return
        self.finished = True
        self._run()
        await self.pieces.put(None)

    async def cancel(self) -> None:
        if self.canceled:
            return
        self.canceled = True
        if self._runner is not None:
            self._runner.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await self._runner
        await self.queue.put(SpeechDone())

    async def events(self) -> AsyncIterator[SpeechEvent]:
        while True:
            ev = await self.queue.get()
            yield ev
            if isinstance(ev, SpeechDone | SpeechFailed):
                return

    async def _speak(self) -> None:
        """Fetch clauses a little ahead, play them in order."""
        gate = asyncio.Semaphore(AHEAD)
        order: asyncio.Queue[tuple[str, asyncio.Queue[bytes | None | Exception]] | None]
        order = asyncio.Queue()

        async def fetch(text: str, out: asyncio.Queue[bytes | None | Exception]) -> None:
            async with gate:
                try:
                    async for chunk in self.mouth._stream(text):
                        await out.put(chunk)
                    await out.put(None)
                except Exception as exc:  # noqa: BLE001 - reported as a failed utterance
                    await out.put(exc)

        async def feed() -> None:
            while (text := await self.pieces.get()) is not None:
                out: asyncio.Queue[bytes | None | Exception] = asyncio.Queue()
                fetches.append(asyncio.create_task(fetch(text, out)))
                await order.put((text, out))
            await order.put(None)

        fetches: list[asyncio.Task[None]] = []
        feeder = asyncio.create_task(feed())
        offset_ms = 0
        try:
            while (item := await order.get()) is not None:
                text, out = item
                size = 0
                carry = b""
                while (chunk := await out.get()) is not None:
                    if isinstance(chunk, Exception):
                        raise chunk
                    # Keep whole 16-bit samples: a split sample would click.
                    chunk = carry + chunk
                    cut = len(chunk) - len(chunk) % 2
                    carry = chunk[cut:]
                    if cut:
                        size += cut
                        await self.queue.put(Audio(chunk[:cut]))
                duration = size // BYTES_PER_MS
                words = spread_words(text, duration, offset_ms)
                if words:
                    await self.queue.put(Words(words))
                offset_ms += duration
            await self.queue.put(SpeechDone())
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 - any engine failure ends the utterance
            await self.queue.put(SpeechFailed(f"openai speech: {exc}"))
        finally:
            feeder.cancel()
            for t in fetches:
                t.cancel()


class OpenAIMouth:
    name = "openai"

    def __init__(
        self,
        api_key: str,
        *,
        model: str = "gpt-4o-mini-tts",
        voice: str = "marin",
        voice_name: str = "Marin",
        http: httpx.AsyncClient | None = None,
    ) -> None:
        self.voice = voice_name
        self.model = model
        self._voice_id = voice
        self._key = api_key
        self._http = http
        self._own_http = http is None

    async def start(self) -> None:
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=httpx.Timeout(20, connect=4))

    async def _stream(self, text: str) -> AsyncIterator[bytes]:
        if self._http is None:
            await self.start()
        assert self._http is not None
        async with self._http.stream(
            "POST",
            URL,
            headers={"Authorization": f"Bearer {self._key}"},
            json={
                "model": self.model,
                "voice": self._voice_id,
                "input": text,
                "response_format": "pcm",
                "instructions": INSTRUCTIONS,
            },
        ) as r:
            if r.status_code != 200:
                body = (await r.aread())[:200].decode("utf-8", "replace")
                raise RuntimeError(f"HTTP {r.status_code}: {body}")
            async for chunk in r.aiter_bytes():
                yield chunk

    def utterance(self) -> OpenAIUtterance:
        return OpenAIUtterance(self)

    async def synthesize(self, text: str) -> tuple[bytes, list[dict[str, Any]]]:
        audio = b"".join([c async for c in self._stream(text)])
        audio = audio[: len(audio) - len(audio) % 2]
        return audio, spread_words(text, len(audio) // BYTES_PER_MS, 0)

    async def close(self) -> None:
        if self._own_http and self._http is not None:
            with contextlib.suppress(Exception):
                await self._http.aclose()
            self._http = None
