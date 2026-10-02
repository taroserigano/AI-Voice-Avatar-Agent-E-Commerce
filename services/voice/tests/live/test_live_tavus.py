"""The real Tavus API: create and end a private avatar conversation in test mode.

Test mode means Tavus doesn't join the room or bill. Opt in with ``TAVUS_LIVE=1`` (needs
``TAVUS_APIKEY`` and ``TAVUS_PAL_ID``; run ``pnpm tavus:setup`` first).
"""

from __future__ import annotations

import asyncio
import os

import httpx
import pytest

from ai_commerce_voice.config import VoiceSettings
from ai_commerce_voice.face_tavus import TavusFace

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(os.environ.get("TAVUS_LIVE") != "1", reason="set TAVUS_LIVE=1"),
]


def test_a_private_test_mode_conversation_starts_and_ends() -> None:
    s = VoiceSettings()
    assert s.tavus_api_key and s.tavus_pal_id

    async def go() -> None:
        async with httpx.AsyncClient() as http:
            face = TavusFace(
                s.tavus_api_key,  # type: ignore[arg-type]
                pal_id=s.tavus_pal_id,  # type: ignore[arg-type]
                face_id=s.tavus_face_id,
                http=http,
                max_call_s=60,
                test_mode=True,
            )
            room = await face.open("live-test")
            assert room.url.startswith("https://")
            assert room.token, "a private room comes with a meeting token"
            await face.close(room)
            got = await http.get(
                f"https://tavusapi.com/v2/conversations/{room.conversation_id}",
                headers={"x-api-key": s.tavus_api_key},  # type: ignore[dict-item]
            )
            assert got.json().get("status") == "ended"

    asyncio.run(go())
