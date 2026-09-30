"""Xana's face: a Tavus video avatar in echo mode (docs/features/10-xana-avatar).

Tavus only animates the face. Our pipeline still decides every word and makes the audio; the
browser forwards that audio to the Tavus room as ``conversation.echo`` messages and shows the
video that comes back. This module is the server's half:

- it creates a private Tavus conversation (``require_auth``) when the customer turns Video on,
  and hands the room URL and meeting token to that customer only, over their signed-in socket;
- the Tavus key never leaves the server, and the request carries no personal data: the name
  is the conversation id, and recording, transcription and captions are off;
- it ends the conversation when Video goes off or the call ends, so billing stops;
- at most ``max_live`` avatars run at once across the process (the account's limits);
- any failure means "no video" (``avatar.unavailable``), never a failed call.

Measured in the spike (2026-09-30): the face joins ~1.3 s after the browser, and Tavus adds
~0.8 s between the audio we send and the audio the customer hears.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Literal

import httpx

log = logging.getLogger(__name__)

TAVUS_API = "https://tavusapi.com"
NOTICE = "With video on, Xana's replies (not your voice) are sent to Tavus to animate her face."

Reason = Literal["not_configured", "busy", "error"]


class AvatarUnavailable(Exception):
    def __init__(self, reason: Reason) -> None:
        super().__init__(reason)
        self.reason: Reason = reason


@dataclass(frozen=True)
class AvatarRoom:
    conversation_id: str
    url: str
    token: str | None
    opened_at: float


def conversation_request(
    *, pal_id: str, face_id: str, conversation_id: str, max_call_s: int, test_mode: bool
) -> dict[str, Any]:
    """The create-conversation body. Nothing about the customer goes in it."""
    body: dict[str, Any] = {
        "pal_id": pal_id,
        "face_id": face_id,
        "conversation_name": f"xana-{conversation_id}",
        "require_auth": True,
        "properties": {
            "max_call_duration": max_call_s,
            # The meeting token expires with this join window (Tavus private rooms).
            "participant_absent_timeout": 30,
            "participant_left_timeout": 10,
            "enable_recording": False,
            "enable_closed_captions": False,
        },
    }
    if test_mode:
        body["test_mode"] = True
    return body


class TavusFace:
    """One per process: creates and ends avatar conversations, and counts the live ones."""

    name = "tavus"

    def __init__(
        self,
        api_key: str,
        *,
        pal_id: str,
        face_id: str,
        http: httpx.AsyncClient,
        max_live: int = 2,
        max_call_s: int = 20 * 60,
        test_mode: bool = False,
        base_url: str = TAVUS_API,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._headers = {"x-api-key": api_key}
        self._pal_id = pal_id
        self.face_id = face_id
        self._http = http
        self._max_live = max_live
        self._max_call_s = max_call_s
        self._test_mode = test_mode
        self._base = base_url.rstrip("/")
        self._clock = clock
        self._live: set[str] = set()
        self._reserved = 0
        self._lock = asyncio.Lock()

    @property
    def live(self) -> int:
        return len(self._live) + self._reserved

    async def open(self, conversation_id: str) -> AvatarRoom:
        async with self._lock:
            if self.live >= self._max_live:
                raise AvatarUnavailable("busy")
            self._reserved += 1
        try:
            resp = await self._http.post(
                f"{self._base}/v2/conversations",
                headers=self._headers,
                json=conversation_request(
                    pal_id=self._pal_id,
                    face_id=self.face_id,
                    conversation_id=conversation_id,
                    max_call_s=self._max_call_s,
                    test_mode=self._test_mode,
                ),
                timeout=httpx.Timeout(10, connect=5),
            )
            resp.raise_for_status()
            data = resp.json()
            room = AvatarRoom(
                conversation_id=str(data["conversation_id"]),
                url=str(data["conversation_url"]),
                token=data.get("meeting_token"),
                opened_at=self._clock(),
            )
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            log.warning("tavus: couldn't start the avatar: %s", _describe(exc))
            async with self._lock:
                self._reserved -= 1
            raise AvatarUnavailable("error") from exc
        async with self._lock:
            self._reserved -= 1
            self._live.add(room.conversation_id)
        log.info("tavus: avatar %s started", room.conversation_id)
        return room

    async def close(self, room: AvatarRoom) -> None:
        """End the conversation (billing stops). Tried twice; the slot is freed either way,
        and Tavus's own timeouts end a conversation we couldn't."""
        if room.conversation_id not in self._live:
            return
        self._live.discard(room.conversation_id)
        minutes = (self._clock() - room.opened_at) / 60
        for attempt in (1, 2):
            try:
                resp = await self._http.post(
                    f"{self._base}/v2/conversations/{room.conversation_id}/end",
                    headers=self._headers,
                    timeout=httpx.Timeout(8, connect=5),
                )
                # Already ended (Tavus timed it out): nothing left to stop.
                if resp.status_code not in (400, 404):
                    resp.raise_for_status()
                log.info("tavus: avatar %s ended after %.1f min", room.conversation_id, minutes)
                return
            except httpx.HTTPError as exc:
                log.warning(
                    "tavus: ending %s failed (attempt %d): %s",
                    room.conversation_id,
                    attempt,
                    _describe(exc),
                )


def _describe(exc: BaseException) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        return f"HTTP {exc.response.status_code}"
    return type(exc).__name__


SendJson = Callable[[dict[str, Any]], Awaitable[None]]


class AvatarLink:
    """One call's avatar: handles ``avatar.start`` / ``avatar.stop`` from the browser."""

    def __init__(self, face: TavusFace | None, conversation_id: str, send_json: SendJson) -> None:
        self._face = face
        self._conversation_id = conversation_id
        self._send = send_json
        self._room: AvatarRoom | None = None
        self._lock = asyncio.Lock()

    @property
    def available(self) -> bool:
        return self._face is not None

    def describe(self) -> dict[str, Any]:
        """What the ``ready`` message says about video."""
        if self._face is None:
            return {"available": False}
        return {"available": True, "provider": self._face.name, "notice": NOTICE}

    async def on_message(self, msg: dict[str, Any]) -> None:
        kind = msg.get("type")
        if kind == "avatar.start":
            await self._start()
        elif kind == "avatar.stop":
            await self._stop(tell=True)

    async def _start(self) -> None:
        async with self._lock:
            if self._face is None:
                await self._send({"type": "avatar.unavailable", "reason": "not_configured"})
                return
            if self._room is None:
                try:
                    self._room = await self._face.open(self._conversation_id)
                except AvatarUnavailable as exc:
                    await self._send({"type": "avatar.unavailable", "reason": exc.reason})
                    return
            await self._send(
                {
                    "type": "avatar",
                    "provider": self._face.name,
                    "conversation_id": self._room.conversation_id,
                    "url": self._room.url,
                    "token": self._room.token,
                }
            )

    async def _stop(self, *, tell: bool) -> None:
        async with self._lock:
            room, self._room = self._room, None
            if room is not None and self._face is not None:
                await self._face.close(room)
            if tell:
                with contextlib.suppress(Exception):
                    await self._send({"type": "avatar.ended"})

    async def close(self) -> None:
        """The call is over: end the avatar without telling a socket that's gone."""
        await self._stop(tell=False)
