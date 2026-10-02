"""LiveAvatar LITE: render our Cartesia audio, without another conversational agent."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from collections.abc import Callable

import httpx

from ai_commerce_voice.config import Look
from ai_commerce_voice.face_tavus import AvatarRoom, AvatarUnavailable

log = logging.getLogger(__name__)
SANDBOX_AVATAR = "dd73ea75-1218-4ef3-92ce-606d5f7fbc0a"


class HeygenFace:
    name = "heygen"

    def __init__(
        self,
        api_key: str,
        *,
        avatar_id: str,
        http: httpx.AsyncClient,
        sandbox: bool = True,
        max_live: int = 2,
        max_call_s: int = 60,
        base_url: str = "https://api.liveavatar.com",
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._headers = {"X-API-KEY": api_key}
        self._avatar_id = avatar_id
        self._http = http
        self._sandbox = sandbox
        self._max_live = max_live
        self._max_call_s = min(max_call_s, 60) if sandbox else max_call_s
        self._base = base_url.rstrip("/")
        self._clock = clock
        self._live: dict[str, AvatarRoom] = {}
        self._lock = asyncio.Lock()
        self._closing: dict[str, AvatarRoom] = {}

    @property
    def live(self) -> int:
        return len(self._live)

    async def open(self, conversation_id: str, look: Look | None = None) -> AvatarRoom:
        # Serializing creates also ensures a failed partial start is cleaned up before retry.
        async with self._lock:
            for old_room in list(self._live.values()):
                if not old_room.url or self._expired(old_room):
                    await self.close(old_room)
            if self.live >= self._max_live:
                raise AvatarUnavailable("busy")
            room: AvatarRoom | None = None
            try:
                response = await self._http.post(
                    f"{self._base}/v1/sessions/token",
                    headers=self._headers,
                    json={
                        "mode": "LITE",
                        "avatar_id": self._avatar_id,
                        "is_sandbox": self._sandbox,
                        "video_settings": {"quality": "high", "encoding": "H264"},
                        "max_session_duration": self._max_call_s,
                    },
                    timeout=15,
                )
                response.raise_for_status()
                data = response.json()["data"]
                session_token = data["session_token"]
                # Keep the ID before starting, so partial failures can always be stopped.
                room = AvatarRoom(str(data["session_id"]), "", None, self._clock())
                self._live[room.conversation_id] = room
                response = await self._http.post(
                    f"{self._base}/v1/sessions/start",
                    headers={"Authorization": f"Bearer {session_token}"},
                    timeout=20,
                )
                response.raise_for_status()
                data = response.json()["data"]
                url, token, ws_url = (
                    data["livekit_url"],
                    data["livekit_client_token"],
                    data["ws_url"],
                )
                if not all(isinstance(v, str) and v for v in (url, token, ws_url)):
                    raise ValueError("missing LITE credentials")
                room = AvatarRoom(room.conversation_id, url, token, room.opened_at, ws_url=ws_url)
                self._live[room.conversation_id] = room
                return room
            except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
                # Never log response bodies, bearer tokens, signed URLs, or API keys.
                log.warning("liveavatar: start failed (%s)", type(exc).__name__)
                if room is not None:
                    await self.close(room)
                raise AvatarUnavailable("error") from exc

    def _expired(self, room: AvatarRoom) -> bool:
        return self._clock() - room.opened_at >= self._max_call_s + 30

    async def close(self, room: AvatarRoom) -> None:
        if room.conversation_id not in self._live:
            self._closing.pop(room.conversation_id, None)
            return
        if self._expired(room):
            self._live.pop(room.conversation_id, None)
            self._closing.pop(room.conversation_id, None)
            return
        for _ in range(2):
            try:
                response = await self._http.post(
                    f"{self._base}/v1/sessions/stop",
                    headers=self._headers,
                    json={"session_id": room.conversation_id, "reason": "USER_CLOSED"},
                    timeout=8,
                )
                if response.status_code != 404:
                    response.raise_for_status()
                self._live.pop(room.conversation_id, None)
                self._closing.pop(room.conversation_id, None)
                return
            except httpx.HTTPError:
                pass
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
