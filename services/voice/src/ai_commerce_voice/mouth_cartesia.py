"""Xana's voice: Cartesia Sonic ("Skylar"), streamed over one WebSocket per session.

Measured (2026-09-26): first audio ~125-165 ms after text is sent on an open socket, versus
~365-454 ms on a fresh connection, so the socket is opened when the session starts and kept
warm (Cartesia closes idle sockets after 5 minutes; we reconnect before that).

One answer is one Cartesia *context*: its clauses are sent as they come from the model with
``continue: true``, so Skylar's intonation carries across them. We chunk the text ourselves
(speech_text.py), so ``max_buffer_delay_ms`` is 0: Cartesia speaks each chunk at once. (That
also avoids a Cartesia bug where cancelling a buffering context with timestamps errors.)

Word timestamps come back with the audio and drive the on-screen captions.
"""

from __future__ import annotations

import asyncio
import base64
import contextlib
import json
import logging
import time
import uuid
from collections.abc import AsyncIterator
from typing import Any

import websockets

from ai_commerce_voice.ports import Audio, SpeechDone, SpeechEvent, SpeechFailed, Words

log = logging.getLogger(__name__)

IDLE_RECONNECT_S = 240.0


class CartesiaUtterance:
    def __init__(self, mouth: CartesiaMouth) -> None:
        self.mouth = mouth
        self.context_id = str(uuid.uuid4())
        self.queue: asyncio.Queue[SpeechEvent] = asyncio.Queue()
        self.canceled = False
        self.finished = False
        self.sent_any = False

    async def push(self, text: str) -> None:
        if self.canceled or self.finished or not text.strip():
            return
        # Cartesia joins pieces exactly as sent: keep a space between clauses.
        await self.mouth._send(self, f"{text.strip()} ", more=True)
        self.sent_any = True

    async def finish(self) -> None:
        if self.canceled or self.finished:
            return
        self.finished = True
        if not self.sent_any:
            await self.queue.put(SpeechDone())
            self.mouth._forget(self)
            return
        await self.mouth._send(self, "", more=False)

    async def cancel(self) -> None:
        if self.canceled:
            return
        self.canceled = True
        if self.sent_any:
            await self.mouth._cancel(self)
        await self.queue.put(SpeechDone())
        self.mouth._forget(self)

    async def events(self) -> AsyncIterator[SpeechEvent]:
        while True:
            ev = await self.queue.get()
            yield ev
            if isinstance(ev, SpeechDone | SpeechFailed):
                return

    def _on(self, m: dict[str, Any]) -> bool:
        """Handle one server message; True when the context is finished."""
        kind = m.get("type")
        if self.canceled:
            return kind in ("done", "error")
        if kind == "chunk" and m.get("data"):
            self.queue.put_nowait(Audio(base64.b64decode(m["data"])))
        elif kind == "timestamps":
            ts = m.get("word_timestamps") or {}
            words = [
                {"w": w, "start_ms": round(s * 1000), "end_ms": round(e * 1000)}
                for w, s, e in zip(
                    ts.get("words", []), ts.get("start", []), ts.get("end", []), strict=False
                )
            ]
            if words:
                self.queue.put_nowait(Words(words))
        elif kind == "done":
            self.queue.put_nowait(SpeechDone())
            return True
        elif kind == "error":
            self.queue.put_nowait(SpeechFailed(str(m.get("title") or m.get("message") or m)))
            return True
        return False


class CartesiaMouth:
    name = "cartesia"

    def __init__(
        self,
        api_key: str,
        *,
        model: str,
        version: str,
        voice_id: str,
        voice_name: str = "Skylar",
        sample_rate: int = 24_000,
    ) -> None:
        self.voice = voice_name
        self.model = model
        self._key = api_key
        self._url = f"wss://api.cartesia.ai/tts/websocket?cartesia_version={version}"
        self._base: dict[str, Any] = {
            "model_id": model,
            "voice": {"mode": "id", "id": voice_id},
            "output_format": {
                "container": "raw",
                "encoding": "pcm_s16le",
                "sample_rate": sample_rate,
            },
            "language": "en",
            "add_timestamps": True,
            "max_buffer_delay_ms": 0,
        }
        self._ws: websockets.ClientConnection | None = None
        self._reader: asyncio.Task[None] | None = None
        self._keeper: asyncio.Task[None] | None = None
        self._contexts: dict[str, CartesiaUtterance] = {}
        self._lock = asyncio.Lock()
        self._used_at = time.monotonic()
        self._closed = False

    async def start(self) -> None:
        await self._connect()
        self._keeper = asyncio.create_task(self._keep_warm())

    async def _connect(self) -> None:
        self._ws = await websockets.connect(
            self._url,
            additional_headers={"X-API-Key": self._key},
            max_size=2**23,
            open_timeout=10,
            ping_interval=20,
        )
        self._reader = asyncio.create_task(self._read(self._ws))
        self._used_at = time.monotonic()

    async def _ensure(self) -> websockets.ClientConnection:
        async with self._lock:
            if self._ws is None or self._ws.state is not websockets.State.OPEN:
                await self._connect()
            assert self._ws is not None
            return self._ws

    async def _keep_warm(self) -> None:
        """Reconnect an idle socket before Cartesia's 5-minute idle timeout closes it."""
        while not self._closed:
            await asyncio.sleep(30)
            if self._contexts or time.monotonic() - self._used_at < IDLE_RECONNECT_S:
                continue
            async with self._lock:
                old = self._ws
                with contextlib.suppress(Exception):
                    await self._connect()
                if old is not None:
                    with contextlib.suppress(Exception):
                        await old.close()

    async def _read(self, ws: websockets.ClientConnection) -> None:
        try:
            async for raw in ws:
                m = json.loads(raw)
                utt = self._contexts.get(str(m.get("context_id")))
                if utt is None:
                    if m.get("type") == "error" and not m.get("context_id"):
                        log.warning("cartesia error: %s", m.get("title"))
                    continue
                if utt._on(m):
                    self._forget(utt)
        except websockets.ConnectionClosed:
            pass
        finally:
            # The live socket died: whatever was speaking on it won't finish. (A socket the
            # keeper replaced had nothing in flight.)
            if ws is self._ws:
                for utt in list(self._contexts.values()):
                    if not utt.canceled:
                        utt.queue.put_nowait(SpeechFailed("voice connection closed"))
                    self._forget(utt)

    def _forget(self, utt: CartesiaUtterance) -> None:
        self._contexts.pop(utt.context_id, None)

    async def _send(self, utt: CartesiaUtterance, transcript: str, *, more: bool) -> None:
        ws = await self._ensure()
        self._contexts[utt.context_id] = utt
        self._used_at = time.monotonic()
        await ws.send(
            json.dumps(
                {
                    **self._base,
                    "context_id": utt.context_id,
                    "transcript": transcript,
                    "continue": more,
                }
            )
        )

    async def _cancel(self, utt: CartesiaUtterance) -> None:
        if self._ws is not None and self._ws.state is websockets.State.OPEN:
            with contextlib.suppress(Exception):
                await self._ws.send(json.dumps({"context_id": utt.context_id, "cancel": True}))

    def utterance(self) -> CartesiaUtterance:
        return CartesiaUtterance(self)

    async def synthesize(self, text: str) -> tuple[bytes, list[dict[str, Any]]]:
        utt = self.utterance()
        await utt.push(text)
        await utt.finish()
        audio: list[bytes] = []
        words: list[dict[str, Any]] = []
        async for ev in utt.events():
            if isinstance(ev, Audio):
                audio.append(ev.pcm16)
            elif isinstance(ev, Words):
                words += ev.words
            elif isinstance(ev, SpeechFailed):
                raise RuntimeError(ev.message)
        return b"".join(audio), words

    async def close(self) -> None:
        self._closed = True
        for task in (self._keeper, self._reader):
            if task:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    await task
        if self._ws is not None:
            with contextlib.suppress(Exception):
                await self._ws.close()
