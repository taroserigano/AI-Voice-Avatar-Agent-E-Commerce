import asyncio
import json

import httpx
import pytest

from ai_commerce_voice.face_heygen import SANDBOX_AVATAR, HeygenFace
from ai_commerce_voice.face_tavus import AvatarUnavailable


def test_lite_contract_sanitized_credentials_capacity_and_stop():
    async def run():
        requests = []

        def handle(request):
            requests.append(request)
            if request.url.path.endswith("/token"):
                body = json.loads(request.content)
                assert body["mode"] == "LITE"
                assert body["avatar_id"] == SANDBOX_AVATAR
                assert body["is_sandbox"] is True and body["max_session_duration"] == 60
                assert request.headers["x-api-key"] == "private-key"
                return httpx.Response(
                    200, json={"data": {"session_id": "s1", "session_token": "server-bearer"}}
                )
            if request.url.path.endswith("/start"):
                assert request.headers["authorization"] == "Bearer server-bearer"
                return httpx.Response(
                    201,
                    json={
                        "data": {
                            "livekit_url": "wss://room.test",
                            "livekit_client_token": "client-token",
                            "livekit_agent_token": "private-agent-token",
                            "ws_url": "wss://control.test",
                        }
                    },
                )
            assert json.loads(request.content) == {"session_id": "s1", "reason": "USER_CLOSED"}
            return httpx.Response(200, json={})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
            face = HeygenFace("private-key", avatar_id=SANDBOX_AVATAR, http=http, max_live=1)
            room = await face.open("customer-conversation")
            assert room.token == "client-token" and room.ws_url == "wss://control.test"
            assert "private" not in repr(room) and "server-bearer" not in repr(room)
            with pytest.raises(AvatarUnavailable, match="busy"):
                await face.open("second")
            await face.close(room)
            await face.close(room)
            assert face.live == 0 and len(requests) == 3

    asyncio.run(run())


def test_partial_start_cleanup_failure_retains_slot_and_can_be_retried():
    async def run():
        allow_stop = False

        def handle(request):
            if request.url.path.endswith("/token"):
                return httpx.Response(
                    200, json={"data": {"session_id": "partial", "session_token": "secret"}}
                )
            if request.url.path.endswith("/start"):
                return httpx.Response(201, json={"data": {"livekit_url": "wss://room.test"}})
            return httpx.Response(200 if allow_stop else 503, json={})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
            face = HeygenFace("private-key", avatar_id=SANDBOX_AVATAR, http=http)
            with pytest.raises(AvatarUnavailable, match="cleanup_pending") as exc:
                await face.open("conversation")
            assert exc.value.room.conversation_id == "partial"
            assert face.live == 1
            allow_stop = True
            await face.retry_cleanup()
            assert face.live == 0

    asyncio.run(run())


def test_provider_errors_do_not_leak_keys_or_release_uncertain_stop(caplog):
    async def run():
        stop_code = 503
        now = [0.0]

        def handle(request):
            if request.url.path.endswith("/token"):
                return httpx.Response(
                    200, json={"data": {"session_id": "s1", "session_token": "secret"}}
                )
            if request.url.path.endswith("/start"):
                return httpx.Response(
                    201,
                    json={
                        "data": {
                            "livekit_url": "wss://room",
                            "livekit_client_token": "t",
                            "ws_url": "wss://control",
                        }
                    },
                )
            return httpx.Response(stop_code, json={"message": "private-key"})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
            face = HeygenFace(
                "private-key", avatar_id=SANDBOX_AVATAR, http=http, clock=lambda: now[0]
            )
            room = await face.open("c")
            with pytest.raises(AvatarUnavailable, match="cleanup_pending"):
                await face.close(room)
            assert face.live == 1
            now[0] = 91
            await face.retry_cleanup()
            assert face.live == 0
            assert "private-key" not in caplog.text

    asyncio.run(run())
