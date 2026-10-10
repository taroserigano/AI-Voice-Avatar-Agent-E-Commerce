"""Two voices, one call: Cartesia first, the backup when Cartesia won't speak.

``start()`` falls back when Cartesia refuses the connection (no credit: HTTP 402, an outage).
During the call, an utterance Cartesia fails before any audio is replayed, word for word, on the
backup, and the call stays on the backup from then on. A failure after audio has played is
passed on as it is (half an answer can't be re-said in another voice); the session shows it as
text. Only when both voices fail does the call go to text.
"""

from __future__ import annotations

import contextlib
import logging
from collections.abc import AsyncIterator, Callable
from typing import Any

from ai_commerce_voice.ports import Audio, Mouth, SpeechEvent, SpeechFailed, Utterance

log = logging.getLogger(__name__)


class _FallbackUtterance:
    def __init__(self, owner: FallbackMouth, first: Utterance, can_switch: bool) -> None:
        self.owner = owner
        self.current = first
        self.can_switch = can_switch
        self.texts: list[str] = []
        self.finished = False
        self.canceled = False

    async def push(self, text: str) -> None:
        self.texts.append(text)
        await self.current.push(text)

    async def finish(self) -> None:
        self.finished = True
        await self.current.finish()

    async def cancel(self) -> None:
        self.canceled = True
        await self.current.cancel()

    async def events(self) -> AsyncIterator[SpeechEvent]:
        heard = False
        while True:
            switched = False
            async for ev in self.current.events():
                if isinstance(ev, Audio):
                    heard = True
                if (
                    isinstance(ev, SpeechFailed)
                    and not heard
                    and self.can_switch
                    and not self.canceled
                ):
                    self.can_switch = False
                    self.owner._switch(ev.message)
                    self.current = self.owner.backup.utterance()
                    for text in self.texts:
                        await self.current.push(text)
                    if self.finished:
                        await self.current.finish()
                    switched = True
                    break
                yield ev
            if not switched:
                return


class FallbackMouth:
    """Speaks with ``primary`` until it fails, then with ``backup``."""

    def __init__(
        self, primary: Mouth, backup: Mouth, on_switch: Callable[[str], None] | None = None
    ) -> None:
        self.primary = primary
        self.backup = backup
        self.using = primary
        self.reason: str | None = None
        self._on_switch = on_switch
        # Who's speaking now (the Mouth protocol's attributes), updated on a switch.
        self.name = primary.name
        self.voice = primary.voice

    @property
    def on_backup(self) -> bool:
        return self.using is self.backup

    async def start(self) -> None:
        try:
            await self.primary.start()
        except Exception as exc:  # noqa: BLE001 - any refusal: use the backup
            log.warning("%s unavailable, using %s: %s", self.primary.name, self.backup.name, exc)
            self._switch(str(exc))
            await self.backup.start()

    def _switch(self, reason: str) -> None:
        if self.using is self.backup:
            return
        log.warning("voice switched from %s to %s: %s", self.primary.name, self.backup.name, reason)
        self.using = self.backup
        self.name = self.backup.name
        self.voice = self.backup.voice
        self.reason = reason
        if self._on_switch is not None:
            self._on_switch(reason)

    def utterance(self) -> Utterance:
        if self.using is self.backup:
            return self.backup.utterance()
        return _FallbackUtterance(self, self.primary.utterance(), can_switch=True)

    async def synthesize(self, text: str) -> tuple[bytes, list[dict[str, Any]]]:
        if self.using is self.primary:
            try:
                return await self.primary.synthesize(text)
            except Exception as exc:  # noqa: BLE001 - try the backup voice
                self._switch(str(exc))
        return await self.backup.synthesize(text)

    async def close(self) -> None:
        for m in (self.primary, self.backup):
            with contextlib.suppress(Exception):  # closing is best effort
                await m.close()
