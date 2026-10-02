"""Xena's face: a Tavus video avatar in echo mode (docs/features/10-xana-avatar).

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
from dataclasses import dataclass, field
from typing import Any, Literal

import httpx

from ai_commerce_voice.config import Look

log = logging.getLogger(__name__)

TAVUS_API = "https://tavusapi.com"
NOTICE = "With video on, Xena's replies (not your voice) are sent to Tavus to animate her face."

Reason = Literal["not_configured", "busy", "error", "cleanup_pending"]


class AvatarUnavailable(Exception):
    def __init__(self, reason: Reason, room: AvatarRoom | None = None) -> None:
        super().__init__(reason)
        self.reason: Reason = reason
        self.room = room


@dataclass(frozen=True)
class AvatarRoom:
    conversation_id: str
    url: str
    token: str | None = field(repr=False)
    opened_at: float
    look: Look | None = None
    ws_url: str | None = field(default=None, repr=False)


def conversation_request(
    *,
    pal_id: str,
    face_id: str,
    conversation_id: str,
    max_call_s: int,
    test_mode: bool,
    greenscreen: bool = False,
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
    if greenscreen:
        # Solid green behind her; the browser swaps in the background the customer picked.
        body["properties"]["apply_greenscreen"] = True
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
        self._live: dict[str, AvatarRoom] = {}
        self._reserved = 0
        self._lock = asyncio.Lock()
        self._closing: dict[str, AvatarRoom] = {}

    @property
    def live(self) -> int:
        return len(self._live) + self._reserved

    async def open(self, conversation_id: str, look: Look | None = None) -> AvatarRoom:
        async with self._lock:
            self._live = {
                k: r
                for k, r in self._live.items()
                if self._clock() - r.opened_at < self._max_call_s + 30
            }
            if self.live >= self._max_live:
                raise AvatarUnavailable("busy")
            self._reserved += 1
        try:
            resp = await self._http.post(
                f"{self._base}/v2/conversations",
                headers=self._headers,
                json=conversation_request(
                    pal_id=self._pal_id,
                    face_id=look.face_id if look else self.face_id,
                    conversation_id=conversation_id,
                    max_call_s=self._max_call_s,
                    test_mode=self._test_mode,
                    greenscreen=bool(look and look.greenscreen),
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
                look=look,
            )
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            log.warning("tavus: couldn't start the avatar: %s", _describe(exc))
            async with self._lock:
                self._reserved -= 1
            raise AvatarUnavailable("error") from exc
        async with self._lock:
            self._reserved -= 1
            self._live[room.conversation_id] = room
        log.info("tavus: avatar %s started", room.conversation_id)
        return room

    async def close(self, room: AvatarRoom) -> None:
        """Release capacity only after a confirmed stop or the provider duration limit."""
        if room.conversation_id not in self._live:
            self._closing.pop(room.conversation_id, None)
            return
        if self._clock() - room.opened_at >= self._max_call_s + 30:
            self._live.pop(room.conversation_id, None)
            self._closing.pop(room.conversation_id, None)
            return
        minutes = (self._clock() - room.opened_at) / 60
        for attempt in (1, 2):
            try:
                resp = await self._http.post(
                    f"{self._base}/v2/conversations/{room.conversation_id}/end",
                    headers=self._headers,
                    timeout=httpx.Timeout(8, connect=5),
                )
                # Already ended (Tavus timed it out): nothing left to stop.
                if resp.status_code != 404:
                    resp.raise_for_status()
                self._live.pop(room.conversation_id, None)
                self._closing.pop(room.conversation_id, None)
                log.info("tavus: avatar %s ended after %.1f min", room.conversation_id, minutes)
                return
            except httpx.HTTPError as exc:
                log.warning(
                    "tavus: ending %s failed (attempt %d): %s",
                    room.conversation_id,
                    attempt,
                    _describe(exc),
                )
        self._closing[room.conversation_id] = room
        raise AvatarUnavailable("cleanup_pending", room)

    async def retry_cleanup(self) -> None:
        for room in list(self._closing.values()):
            with contextlib.suppress(AvatarUnavailable):
                await self.close(room)

    async def close_all(self) -> None:
        for room in list(self._live.values()):
            with contextlib.suppress(AvatarUnavailable):
                await self.close(room)


def _describe(exc: BaseException) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        return f"HTTP {exc.response.status_code}"
    return type(exc).__name__


SendJson = Callable[[dict[str, Any]], Awaitable[None]]


class AvatarLink:
    """One call's avatar: handles ``avatar.start`` / ``avatar.stop`` from the browser.

    ``avatar.start`` may name a look; only looks on the server's list are used (an unknown
    one gets the default), so the browser can't ask for an arbitrary face. Starting with a
    different look while a room is open ends that room and opens a new one."""

    def __init__(
        self,
        face: TavusFace | None,
        conversation_id: str,
        send_json: SendJson,
        looks: tuple[Look, ...] = (),
        default_look: str | None = None,
    ) -> None:
        self._face = face
        self._conversation_id = conversation_id
        self._send = send_json
        self._looks = {look.key: look for look in looks}
        self._default = self._looks.get(default_look or "") or (looks[0] if looks else None)
        self._room: AvatarRoom | None = None
        self._lock = asyncio.Lock()

    @property
    def available(self) -> bool:
        return self._face is not None

    def describe(self) -> dict[str, Any]:
        """What the ``ready`` message says about video."""
        if self._face is None:
            return {"available": False}
        return {
            "available": True,
            "provider": self._face.name,
            "notice": NOTICE,
            "looks": [{"key": look.key, "label": look.label} for look in self._looks.values()],
            "default_look": self._default.key if self._default else None,
        }

    async def on_message(self, msg: dict[str, Any]) -> None:
        kind = msg.get("type")
        if kind == "avatar.start":
            await self._start(self._looks.get(str(msg.get("look") or "")) or self._default)
        elif kind == "avatar.stop":
            await self._stop(tell=True)

    async def _start(self, look: Look | None) -> None:
        async with self._lock:
            if self._face is None:
                await self._send({"type": "avatar.unavailable", "reason": "not_configured"})
                return
            if self._room is not None and self._room.look != look:
                # A new look: end this room (billing stops) before opening the next.
                await self._face.close(self._room)
                self._room = None
            if self._room is None:
                try:
                    self._room = await self._face.open(self._conversation_id, look)
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
                    "look": look.key if look else None,
                    "greenscreen": bool(look and look.greenscreen),
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
