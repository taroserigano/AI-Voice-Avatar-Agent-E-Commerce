"""Xana's ears: OpenAI streaming transcription (``gpt-live-transcribe``) with our own VAD.

``gpt-live-transcribe`` at ``delay: minimal`` streams words while the customer is still
talking (about 150-400 ms behind the audio, measured), so captions are live and the text is
essentially complete when they stop. It has no turn detection of its own, so :class:`Vad`
decides when speech starts and ends and we commit the buffer.

Two things make the end of a turn fast:

- only speech is sent (plus 300 ms of pre-roll so the first syllable isn't clipped), so each
  commit transcribes one utterance, not minutes of silence;
- at the commit we emit a :class:`Draft` with the live text, so the agent can start thinking
  right away. The :class:`Final` transcript follows ~300-450 ms later with the same
  ``item_id``; the session restarts the turn only if the words changed.

Audio goes to OpenAI to be transcribed and is not stored by us (returns regulations §5.1).
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

from ai_commerce_voice.ports import (
    Draft,
    Final,
    HearingEvent,
    Partial,
    SpeechStarted,
    SpeechStopped,
    SttFailed,
)
from ai_commerce_voice.vad import FRAME_MS, Vad

log = logging.getLogger(__name__)

URL = "wss://api.openai.com/v1/realtime?intent=transcription"
RATE = 24_000
FRAME_BYTES = RATE * 2 * FRAME_MS // 1000

# Words customers say to Xana that a general model may not expect.
KEYWORDS = [
    "Xana",
    "Serigan Mart",
    "RMA",
    "refund",
    "return label",
    "order number",
    "tracking number",
    "drop-off",
]


class OpenAILiveEars:
    name = "openai"

    def __init__(
        self,
        api_key: str,
        *,
        model: str = "gpt-live-transcribe",
        vad: Vad | None = None,
        keywords: list[str] | None = None,
        talking: Any = None,
    ) -> None:
        self.model = model
        self._key = api_key
        self._vad = vad or Vad()
        self._keywords = keywords or KEYWORDS
        # A callable telling us whether Xana is speaking right now (raises the VAD threshold).
        self._talking = talking or (lambda: False)
        self._ws: websockets.ClientConnection | None = None
        self._events: asyncio.Queue[HearingEvent | None] = asyncio.Queue()
        self._reader: asyncio.Task[None] | None = None
        self._buf = b""
        self._live = ""
        self._pending: list[dict[str, Any]] = []  # utterances committed, awaiting their item_id
        self._started_at = 0.0

    async def start(self) -> None:
        self._ws = await websockets.connect(
            URL,
            additional_headers={"Authorization": f"Bearer {self._key}"},
            max_size=2**22,
            open_timeout=10,
        )
        first = json.loads(await self._ws.recv())
        if first.get("type") != "session.created":
            raise RuntimeError(f"unexpected first event {first.get('type')}")
        transcription: dict[str, Any] = {"model": self.model, "languages": ["en"]}
        if self.model == "gpt-live-transcribe":
            transcription["delay"] = "minimal"
            transcription["keywords"] = self._keywords
        else:
            transcription["prompt"] = ", ".join(self._keywords)
        await self._send(
            {
                "type": "session.update",
                "session": {
                    "type": "transcription",
                    "audio": {
                        "input": {
                            "format": {"type": "audio/pcm", "rate": RATE},
                            "transcription": transcription,
                            "turn_detection": None,
                        }
                    },
                },
            }
        )
        self._reader = asyncio.create_task(self._read())

    async def _send(self, msg: dict[str, Any]) -> None:
        assert self._ws is not None
        await self._ws.send(json.dumps(msg))

    async def send_audio(self, pcm16: bytes) -> None:
        if self._ws is None:
            return
        self._buf += pcm16
        while len(self._buf) >= FRAME_BYTES:
            frame, self._buf = self._buf[:FRAME_BYTES], self._buf[FRAME_BYTES:]
            await self._frame(frame)

    async def _frame(self, frame: bytes) -> None:
        was_speaking = self._vad.speaking
        event = self._vad.feed(frame, transcript=self._live, talking=bool(self._talking()))
        if event == "start":
            self._started_at = time.monotonic()
            self._live = ""
            await self._events.put(SpeechStarted(at=self._started_at))
            await self._append(self._vad.take_pre_roll())
        elif was_speaking:
            await self._append(frame)
        if event == "end":
            now = time.monotonic()
            spoken = self._vad.spoken_ms
            await self._events.put(SpeechStopped(at=now))
            if spoken < self._vad.min_speech_ms:
                await self._send({"type": "input_audio_buffer.clear"})
                return
            self._pending.append({"draft": self._live, "at": now, "speech_ms": float(spoken)})
            await self._send({"type": "input_audio_buffer.commit"})

    async def _append(self, audio: bytes) -> None:
        if audio:
            await self._send(
                {"type": "input_audio_buffer.append", "audio": base64.b64encode(audio).decode()}
            )

    async def _read(self) -> None:
        assert self._ws is not None
        items: dict[str, dict[str, Any]] = {}
        try:
            async for raw in self._ws:
                m = json.loads(raw)
                kind = m.get("type")
                if kind == "input_audio_buffer.committed":
                    item = m.get("item_id") or str(uuid.uuid4())
                    info = (
                        self._pending.pop(0)
                        if self._pending
                        else {"draft": "", "at": time.monotonic(), "speech_ms": 0.0}
                    )
                    items[item] = info
                    # Words that arrived between the end of speech and the commit count too,
                    # unless the customer has already started a new utterance.
                    draft = (
                        info["draft"] if self._vad.speaking else self._live or info["draft"]
                    ).strip()
                    if draft:
                        await self._events.put(Draft(text=draft, item_id=item, at=info["at"]))
                elif kind == "conversation.item.input_audio_transcription.delta":
                    self._live += m.get("delta", "")
                    await self._events.put(Partial(text=self._live.strip()))
                elif kind == "conversation.item.input_audio_transcription.completed":
                    item = m.get("item_id") or ""
                    info = items.pop(item, {"at": time.monotonic(), "speech_ms": 0.0})
                    await self._events.put(
                        Final(
                            text=str(m.get("transcript") or "").strip(),
                            at=time.monotonic(),
                            speech_ms=info["speech_ms"],
                            item_id=item,
                        )
                    )
                elif kind == "error":
                    err = m.get("error") or {}
                    # Clearing or committing an empty buffer is harmless.
                    if err.get("code") in ("input_audio_buffer_commit_empty",):
                        continue
                    log.warning("transcription error: %s", err.get("message"))
                    await self._events.put(SttFailed(message=str(err.get("message"))))
        except websockets.ConnectionClosed as exc:
            log.info("transcription socket closed: %s", exc.code)
        finally:
            await self._events.put(None)

    async def events(self) -> AsyncIterator[HearingEvent]:
        while (ev := await self._events.get()) is not None:
            yield ev

    async def close(self) -> None:
        if self._reader:
            self._reader.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await self._reader
        if self._ws is not None:
            with contextlib.suppress(Exception):
                await self._ws.close()
        await self._events.put(None)
