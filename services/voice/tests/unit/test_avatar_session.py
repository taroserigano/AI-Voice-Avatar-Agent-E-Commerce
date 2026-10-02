"""Lifecycle tests use gates, not network sleeps, to exercise overlapping selections."""

import asyncio

from ai_commerce_voice.avatar_session import AvatarSession
from ai_commerce_voice.face_tavus import AvatarRoom, AvatarUnavailable


class Face:
    def __init__(self, name, events):
        self.name, self.events = name, events
        self.entered = asyncio.Event()
        self.release = asyncio.Event()
        self.release.set()
        self.fail_close = False

    async def open(self, conversation_id, look=None):
        self.events.append(("open", self.name, conversation_id))
        self.entered.set()
        await self.release.wait()
        return AvatarRoom(self.name + "-room", "https://room.test", "ephemeral", 0)

    async def close(self, room):
        self.events.append(("close", self.name))
        if self.fail_close:
            raise AvatarUnavailable("cleanup_pending", room)


def setup():
    events, sent, switches = [], [], []
    faces = {name: Face(name, events) for name in ("tavus", "heygen")}

    async def send(msg):
        sent.append(msg)

    async def switch(provider, generation):
        switches.append((provider, generation))

    manager = AvatarSession(faces, "same-conversation", send, switch)
    return manager, faces, events, sent, switches


async def select(manager, provider, request):
    await manager.on_message({"type": "avatar.select", "provider": provider, "request_id": request})


def test_latest_switch_wins_and_stale_room_is_stopped_before_next_start():
    async def run():
        manager, faces, events, sent, switches = setup()
        faces["tavus"].release.clear()
        await select(manager, "tavus", 1)
        await faces["tavus"].entered.wait()
        await select(manager, "heygen", 2)
        await select(manager, "tavus", 3)
        await select(manager, "heygen", 4)
        faces["tavus"].release.set()
        await manager._worker
        assert events == [
            ("open", "tavus", "same-conversation"),
            ("close", "tavus"),
            ("open", "heygen", "same-conversation"),
        ]
        assert len(sent) == 1 and sent[0]["request_id"] == 4
        assert switches[-1] == ("heygen", 4)
        await manager.close()
        assert events[-1] == ("close", "heygen")

    asyncio.run(run())


def test_failed_stop_blocks_new_provider_and_retry_keeps_correct_owner():
    async def run():
        manager, faces, events, sent, _ = setup()
        await select(manager, "tavus", 1)
        await manager._worker
        faces["tavus"].fail_close = True
        await select(manager, "heygen", 2)
        await manager._worker
        assert sent[-1]["reason"] == "cleanup_pending"
        assert not faces["heygen"].entered.is_set()
        faces["tavus"].fail_close = False
        await select(manager, "heygen", 3)
        await manager._worker
        assert events[-2:] == [("close", "tavus"), ("open", "heygen", "same-conversation")]
        await manager.close()

    asyncio.run(run())


def test_disconnect_during_create_cleans_late_room_and_sends_no_credentials():
    async def run():
        manager, faces, events, sent, _ = setup()
        faces["heygen"].release.clear()
        await select(manager, "heygen", 1)
        await faces["heygen"].entered.wait()
        closing = asyncio.create_task(manager.close())
        await asyncio.sleep(0)
        faces["heygen"].release.set()
        await closing
        assert events[-1] == ("close", "heygen")
        assert sent == []

    asyncio.run(run())


def test_missing_provider_and_old_or_invalid_selection_never_open_rooms():
    async def run():
        manager, faces, events, sent, switches = setup()
        del faces["heygen"]
        assert manager.describe()["heygen"] == {"available": False}
        assert events == []  # describing/pre-call tabs are free
        await select(manager, "heygen", 2)
        await manager._worker
        assert sent[-1]["reason"] == "not_configured"
        await select(manager, "tavus", 1)
        await select(manager, "untrusted-provider", 3)
        assert events == [] and switches == [("heygen", 2)]
        await manager.close()

    asyncio.run(run())


def test_selection_arriving_while_credentials_are_sent_is_processed():
    async def run():
        manager, _, events, sent, _ = setup()
        original = manager._send

        async def send(msg):
            await original(msg)
            if msg["type"] == "avatar" and msg["request_id"] == 1:
                await select(manager, "heygen", 2)

        manager._send = send
        await select(manager, "tavus", 1)
        await manager._worker
        assert sent[-1]["provider"] == "heygen"
        assert events[-2:] == [("close", "tavus"), ("open", "heygen", "same-conversation")]
        await manager.close()

    asyncio.run(run())
