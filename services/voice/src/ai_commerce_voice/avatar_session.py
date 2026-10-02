"""One serialized, latest-selection-wins avatar lifecycle per authenticated voice socket."""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from ai_commerce_voice.config import Look
from ai_commerce_voice.face_tavus import AvatarRoom, AvatarUnavailable, SendJson


class Face(Protocol):
    name: str

    async def open(self, conversation_id: str, look: Look | None = None) -> AvatarRoom: ...
    async def close(self, room: AvatarRoom) -> None: ...
    async def close_all(self) -> None: ...
    async def retry_cleanup(self) -> None: ...


class AvatarSession:
    def __init__(
        self,
        faces: dict[str, Face],
        conversation_id: str,
        send_json: SendJson,
        switch_output: Callable[[str, int], Awaitable[None]],
        *,
        output_ready: Callable[[int], Awaitable[None]] | None = None,
        looks: tuple[Look, ...] = (),
        default_look: str | None = None,
    ) -> None:
        self._faces = faces
        self._id = conversation_id
        self._send = send_json
        self._switch_output = switch_output
        self._output_ready = output_ready
        self._looks = {look.key: look for look in looks}
        self._default = self._looks.get(default_look or "")
        self._request = 0
        self._desired: tuple[str | None, Look | None] = (None, None)
        self._current: tuple[Face, AvatarRoom] | None = None
        self._worker: asyncio.Task[None] | None = None
        self._closed = False

    def describe(self) -> dict[str, Any]:
        offers: dict[str, Any] = {}
        for provider in ("tavus", "heygen"):
            offers[provider] = {"available": provider in self._faces}
            if provider in self._faces:
                offers[provider].update(
                    {
                        "provider": provider,
                        "notice": "With video on, Xena's replies are sent to "
                        + ("Tavus" if provider == "tavus" else "HeyGen LiveAvatar")
                        + " to animate her face. Your microphone stays with Xena's voice service.",
                    }
                )
        if "tavus" in self._faces:
            offers["tavus"].update(
                {
                    "looks": [{"key": x.key, "label": x.label} for x in self._looks.values()],
                    "default_look": self._default.key if self._default else None,
                }
            )
        return offers

    async def on_message(self, msg: dict[str, Any]) -> None:
        if (
            not self._closed
            and msg.get("type") == "avatar.playing"
            and msg.get("request_id") == self._request
            and self._current is not None
        ):
            if self._output_ready:
                await self._output_ready(self._request)
            return
        if self._closed or msg.get("type") != "avatar.select":
            return
        request = msg.get("request_id")
        provider = msg.get("provider")
        if (
            type(request) is not int
            or request <= self._request
            or request > 2**31
            or provider not in ("tavus", "heygen", None)
        ):
            return
        self._request = request
        self._desired = (
            provider,
            (self._looks.get(str(msg.get("look") or "")) or self._default)
            if provider == "tavus"
            else None,
        )
        # Invalidate old playback/quote readiness immediately, without waiting for HTTP.
        await self._switch_output(provider or "local", request)
        if self._worker is None or self._worker.done():
            self._worker = asyncio.create_task(self._run())

    async def _run(self) -> None:
        while True:
            request = self._request
            provider, look = self._desired
            try:
                if self._current is not None:
                    face, room = self._current
                    await face.close(room)
                    self._current = None
                if request != self._request:
                    continue
                if provider is None:
                    if not self._closed:
                        await self._send({"type": "avatar.ended", "request_id": request})
                    if request != self._request:
                        continue
                    return
                selected_face = self._faces.get(provider)
                if selected_face is None:
                    raise AvatarUnavailable("not_configured")
                room = await selected_face.open(self._id, look)
                self._current = (selected_face, room)
                if request != self._request:
                    continue
                await self._send(
                    {
                        "type": "avatar",
                        "provider": provider,
                        "request_id": request,
                        "conversation_id": room.conversation_id,
                        "url": room.url,
                        "token": room.token,
                        "ws_url": room.ws_url,
                        "look": look.key if look else None,
                        "greenscreen": bool(look and look.greenscreen),
                    }
                )
                if request != self._request:
                    continue
                return
            except AvatarUnavailable as exc:
                if self._current is None and exc.room is not None and provider in self._faces:
                    self._current = (self._faces[provider], exc.room)
                if not self._closed and request == self._request:
                    if self._output_ready:
                        await self._output_ready(request)
                    await self._send(
                        {
                            "type": "avatar.unavailable",
                            "request_id": request,
                            "reason": exc.reason,
                        }
                    )
                # A failed stop retains _current. A newer selection retries it first.
                if request == self._request:
                    return
            except Exception:
                # A disconnected socket must not strand the newly-created room.
                return

    async def close(self) -> None:
        self._closed = True
        self._request += 1
        self._desired = (None, None)
        if self._worker is not None:
            with contextlib.suppress(Exception):
                await self._worker
        if self._current is not None:
            face, room = self._current
            with contextlib.suppress(AvatarUnavailable):
                await face.close(room)
            # Failed stops remain accounted for by the process adapter, retried at shutdown.
