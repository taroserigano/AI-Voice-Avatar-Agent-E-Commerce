"""Xana's avatar (Tavus): private rooms, no personal data, billing stops, video never breaks
a call."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx
import pytest

from ai_commerce_voice.config import LOOKS, Look
from ai_commerce_voice.face_tavus import AvatarLink, AvatarUnavailable, TavusFace

KEY = "tavus-secret-key"


class FakeTavus:
    """A stand-in for tavusapi.com: records every request, fails on demand."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.created = 0
        self.fail_create: int | None = None
        self.fail_end: list[int] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if request.url.path == "/v2/conversations":
            if self.fail_create:
                return httpx.Response(self.fail_create)
            self.created += 1
            cid = f"c{self.created}"
            return httpx.Response(
                200,
                json={
                    "conversation_id": cid,
                    "conversation_url": f"https://tavus.daily.co/{cid}",
                    "meeting_token": f"token-{cid}",
                    "status": "active",
                },
            )
        if request.url.path.endswith("/end"):
            if self.fail_end:
                return httpx.Response(self.fail_end.pop(0))
            return httpx.Response(200)
        return httpx.Response(404)

    def ends(self) -> list[str]:
        return [r.url.path for r in self.requests if r.url.path.endswith("/end")]

    def bodies(self) -> list[dict[str, Any]]:
        return [json.loads(r.content) for r in self.requests if r.url.path == "/v2/conversations"]


def face(fake: FakeTavus, **kw: Any) -> TavusFace:
    http = httpx.AsyncClient(transport=httpx.MockTransport(fake))
    return TavusFace(KEY, pal_id="p-xana", face_id="rc9cff32ceba", http=http, **kw)


class Browser:
    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []

    async def __call__(self, msg: dict[str, Any]) -> None:
        self.sent.append(msg)


def run(coro: Any) -> Any:
    return asyncio.run(coro)


def test_the_room_is_private_and_carries_nothing_about_the_customer() -> None:
    fake = FakeTavus()

    async def go() -> None:
        room = await face(fake, max_call_s=1200).open("3f1c-conv")
        assert room.token == "token-c1"

    run(go())
    (body,) = fake.bodies()
    assert body["require_auth"] is True
    assert body["conversation_name"] == "xana-3f1c-conv"
    assert body["pal_id"] == "p-xana" and body["face_id"] == "rc9cff32ceba"
    props = body["properties"]
    assert props["enable_recording"] is False and props["enable_closed_captions"] is False
    assert props["max_call_duration"] == 1200
    # Only these fields, so nothing personal can ride along.
    assert set(body) == {"pal_id", "face_id", "conversation_name", "require_auth", "properties"}
    assert fake.requests[0].headers["x-api-key"] == KEY


def test_the_key_never_reaches_the_browser() -> None:
    fake = FakeTavus()
    browser = Browser()

    async def go() -> None:
        link = AvatarLink(face(fake), "conv-1", browser)
        await link.on_message({"type": "avatar.start"})
        await link.on_message({"type": "avatar.stop"})

    run(go())
    assert browser.sent[0] == {
        "type": "avatar",
        "provider": "tavus",
        "conversation_id": "c1",
        "url": "https://tavus.daily.co/c1",
        "token": "token-c1",
        "look": None,
        "greenscreen": False,
    }
    assert KEY not in json.dumps(browser.sent)


def test_hanging_up_ends_the_avatar_once() -> None:
    fake = FakeTavus()
    browser = Browser()

    async def go() -> None:
        link = AvatarLink(face(fake), "conv-1", browser)
        await link.on_message({"type": "avatar.start"})
        await link.on_message({"type": "avatar.start"})  # a second tap reuses the room
        await link.close()
        await link.close()

    run(go())
    assert fake.created == 1
    assert fake.ends() == ["/v2/conversations/c1/end"]


def test_video_off_then_hang_up_ends_it_once() -> None:
    fake = FakeTavus()
    browser = Browser()

    async def go() -> None:
        link = AvatarLink(face(fake), "conv-1", browser)
        await link.on_message({"type": "avatar.start"})
        await link.on_message({"type": "avatar.stop"})
        await link.close()

    run(go())
    assert fake.ends() == ["/v2/conversations/c1/end"]
    assert browser.sent[-1] == {"type": "avatar.ended"}


def test_a_failed_end_is_tried_again() -> None:
    fake = FakeTavus()
    fake.fail_end = [503]

    async def go() -> TavusFace:
        f = face(fake)
        await f.close(await f.open("conv-1"))
        return f

    f = run(go())
    assert len(fake.ends()) == 2
    assert f.live == 0


def test_an_already_ended_conversation_isnt_retried() -> None:
    fake = FakeTavus()
    fake.fail_end = [404]

    async def go() -> None:
        f = face(fake)
        await f.close(await f.open("conv-1"))

    run(go())
    assert len(fake.ends()) == 1


def test_only_so_many_avatars_at_once() -> None:
    fake = FakeTavus()

    async def go() -> None:
        f = face(fake, max_live=2)
        a = await f.open("conv-a")
        await f.open("conv-b")
        with pytest.raises(AvatarUnavailable) as exc:
            await f.open("conv-c")
        assert exc.value.reason == "busy"
        await f.close(a)
        await f.open("conv-c")  # the freed slot is usable again

    run(go())
    assert fake.created == 3


def test_parallel_starts_cant_overshoot_the_limit() -> None:
    fake = FakeTavus()

    async def go() -> list[Any]:
        f = face(fake, max_live=1)
        return await asyncio.gather(f.open("a"), f.open("b"), f.open("c"), return_exceptions=True)

    results = run(go())
    assert sum(not isinstance(r, Exception) for r in results) == 1
    assert fake.created == 1


@pytest.mark.parametrize("status", [401, 429, 500])
def test_a_tavus_failure_means_no_video_not_a_failed_call(status: int) -> None:
    fake = FakeTavus()
    fake.fail_create = status
    browser = Browser()

    async def go() -> AvatarLink:
        link = AvatarLink(face(fake), "conv-1", browser)
        await link.on_message({"type": "avatar.start"})
        return link

    run(go())
    assert browser.sent == [{"type": "avatar.unavailable", "reason": "error"}]


def test_a_failed_start_frees_its_slot() -> None:
    fake = FakeTavus()
    fake.fail_create = 500

    async def go() -> TavusFace:
        f = face(fake, max_live=1)
        with pytest.raises(AvatarUnavailable):
            await f.open("conv-1")
        return f

    assert run(go()).live == 0


def test_a_server_without_video_says_so() -> None:
    browser = Browser()

    async def go() -> AvatarLink:
        link = AvatarLink(None, "conv-1", browser)
        await link.on_message({"type": "avatar.start"})
        await link.close()
        return link

    link = run(go())
    assert link.describe() == {"available": False}
    assert browser.sent == [{"type": "avatar.unavailable", "reason": "not_configured"}]


ROSE = Look("rose", "Rose", "face-rose")
MARGO = Look("margo", "Margo", "face-margo")


def looked(fake: FakeTavus, browser: Browser) -> AvatarLink:
    return AvatarLink(face(fake), "conv-1", browser, looks=(ROSE, MARGO), default_look="rose")


def test_a_look_picks_its_face_and_the_green_screen() -> None:
    fake = FakeTavus()
    browser = Browser()

    async def go() -> None:
        await looked(fake, browser).on_message({"type": "avatar.start", "look": "margo"})

    run(go())
    (body,) = fake.bodies()
    assert body["face_id"] == "face-margo"
    assert body["properties"]["apply_greenscreen"] is True
    assert browser.sent[0]["look"] == "margo" and browser.sent[0]["greenscreen"] is True


def test_the_browser_cant_ask_for_an_arbitrary_face() -> None:
    fake = FakeTavus()
    browser = Browser()

    async def go() -> None:
        link = looked(fake, browser)
        await link.on_message({"type": "avatar.start", "look": "r-someone-elses-face"})
        await link.on_message({"type": "avatar.start", "face_id": "r-someone-elses-face"})

    run(go())
    assert [b["face_id"] for b in fake.bodies()] == ["face-rose"]  # the default, once


def test_switching_looks_ends_the_old_room_first() -> None:
    fake = FakeTavus()
    browser = Browser()

    async def go() -> None:
        link = looked(fake, browser)
        await link.on_message({"type": "avatar.start", "look": "rose"})
        await link.on_message({"type": "avatar.start", "look": "margo"})
        await link.close()

    run(go())
    assert [b["face_id"] for b in fake.bodies()] == ["face-rose", "face-margo"]
    assert fake.ends() == ["/v2/conversations/c1/end", "/v2/conversations/c2/end"]
    assert [m["look"] for m in browser.sent if m["type"] == "avatar"] == ["rose", "margo"]


def test_the_ready_message_lists_the_looks() -> None:
    link = looked(FakeTavus(), Browser())
    offer = link.describe()
    assert offer["looks"] == [{"key": "rose", "label": "Rose"}, {"key": "margo", "label": "Margo"}]
    assert offer["default_look"] == "rose"
    assert "face-rose" not in str(offer) and "face-margo" not in str(offer)  # ids stay server-side


def test_every_look_can_take_a_background() -> None:
    # Tavus's green screen doesn't work on Phoenix-4.5 faces; every listed look must allow it.
    assert LOOKS and all(look.greenscreen for look in LOOKS)
    assert len({look.key for look in LOOKS}) == len(LOOKS)
