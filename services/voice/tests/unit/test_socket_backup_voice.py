"""The WebSocket does not report a successful voice fallback as an error."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import ai_commerce_voice.app as voice_app
from ai_commerce_voice.config import VoiceSettings
from tests.fakes import FakeEars
from tests.unit.test_backup_voice import RefusingMouth, backup, drain


@pytest.mark.parametrize("at_start", [True, False])
def test_fallback_does_not_send_a_customer_error(
    monkeypatch: pytest.MonkeyPatch, at_start: bool
) -> None:
    primary = RefusingMouth(at_start=at_start)
    spare = backup()
    settings = VoiceSettings.model_construct(cartesia_api_key="test", openai_api_key="test")
    pick = SimpleNamespace(simulated=True, model=None, strong=None, strong_name="", name="fixture")
    customer = SimpleNamespace(id=uuid4(), name="Alice")
    conversation = SimpleNamespace(id=uuid4())

    class Brain:
        model = "fixture"
        simulated = True

        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            pass

        async def pending_quote(self) -> None:
            return None

    class Session:
        def __init__(self, **kwargs: Any) -> None:
            self.send_json = kwargs["send_json"]
            self.mouth = kwargs["mouth"]
            self.state = "listening"

        async def start(self) -> None:
            await self.send_json({"type": "state", "state": "listening"})

        async def on_message(self, _message: dict[str, Any]) -> None:
            utterance = self.mouth.utterance()
            await utterance.push("The return window is thirty days.")
            await utterance.finish()
            await drain(utterance.events())
            await self.send_json({"type": "test.finished"})

        async def close(self) -> None:
            pass

        async def switch_output(self, *_args: Any) -> None:
            pass

        async def output_ready(self, *_args: Any) -> None:
            pass

    async def no_fillers(*_args: Any) -> None:
        pass

    monkeypatch.setattr(voice_app, "get_settings", lambda: settings)
    monkeypatch.setattr(
        voice_app,
        "assistant_settings",
        lambda: SimpleNamespace(session_cookie_name="session", max_turns_per_conversation=10),
    )
    monkeypatch.setattr(voice_app, "build_voice_graph", lambda _saver: None)
    monkeypatch.setattr(voice_app, "load_fillers", no_fillers)
    monkeypatch.setattr(voice_app, "make_face", lambda *_args: None)
    monkeypatch.setattr(voice_app, "resolve_customer", lambda *_args: customer)
    monkeypatch.setattr(voice_app, "CommerceClient", lambda *_args: MagicMock())
    monkeypatch.setattr(
        voice_app, "make_mouth", lambda _settings, provider=None: spare if provider else primary
    )
    monkeypatch.setattr(voice_app, "OpenAILiveEars", lambda *_args, **_kwargs: FakeEars())
    monkeypatch.setattr(voice_app, "pick_model", lambda *_args: pick)
    monkeypatch.setattr(voice_app, "_warm_policy_search", lambda *_args: None)
    monkeypatch.setattr(voice_app, "_own_or_new", lambda *_args: conversation)
    monkeypatch.setattr(voice_app, "_recent_orders", lambda *_args: [])
    monkeypatch.setattr(voice_app, "catalog_vocabulary", lambda *_args: {})
    monkeypatch.setattr(voice_app, "XanaBrain", Brain)
    monkeypatch.setattr(voice_app, "make_context", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(voice_app, "VoiceSession", Session)

    with (
        TestClient(voice_app.create_app(checkpointer=object())) as client,
        client.websocket_connect(
            "/v1/voice/xana", headers={"origin": "http://localhost:3000"}
        ) as socket,
    ):
        socket.send_json({"type": "hello"})
        ready = socket.receive_json()
        assert ready["type"] == "ready"
        assert ready["voice"]["provider"] == ("openai" if at_start else "cartesia")
        assert socket.receive_json() == {"type": "state", "state": "listening"}
        socket.send_json({"type": "test.switch"})
        assert socket.receive_json() == {"type": "test.finished"}
        assert spare.spoken() == ["The return window is thirty days."]
