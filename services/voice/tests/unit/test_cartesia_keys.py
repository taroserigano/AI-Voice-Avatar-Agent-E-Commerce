from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

import ai_commerce_voice.app as app
from ai_commerce_voice.config import VoiceSettings
from ai_commerce_voice.mouth_cartesia import CartesiaMouth
from ai_commerce_voice.mouth_fallback import FallbackMouth
from ai_commerce_voice.ports import Audio, SpeechFailed
from ai_commerce_voice.session import FillerClip
from tests.fakes import FakeMouth
from tests.unit.test_backup_voice import RefusingMouth, backup, drain, run


def test_configured_preference_uses_second_key_first(monkeypatch: pytest.MonkeyPatch) -> None:
    used: list[str] = []

    def fake_mouth(key: str, **_kwargs: Any) -> FakeMouth:
        used.append(key)
        mouth = FakeMouth()
        mouth.name = "cartesia"
        return mouth

    monkeypatch.setattr(app, "CartesiaMouth", fake_mouth)
    settings = VoiceSettings.model_construct(
        cartesia_api_key="first", cartesia_api_key2="second", cartesia_preferred_key="secondary"
    )
    mouth = app.make_mouth(settings)
    assert used == ["second", "first"]
    assert isinstance(mouth, FallbackMouth)


def test_secondary_alone_and_duplicate_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    used: list[str] = []

    def fake_mouth(key: str, **_kwargs: Any) -> FakeMouth:
        used.append(key)
        return FakeMouth()

    monkeypatch.setattr(app, "CartesiaMouth", fake_mouth)
    only_second = VoiceSettings.model_construct(cartesia_api_key2="second")
    assert not isinstance(app.make_mouth(only_second), FallbackMouth)
    duplicate = VoiceSettings.model_construct(cartesia_api_key="same", cartesia_api_key2="same")
    assert not isinstance(app.make_mouth(duplicate), FallbackMouth)
    assert used == ["second", "same"]


def test_first_key_refusal_switches_to_second_without_changing_voice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def t() -> None:
        spare = FakeMouth()
        spare.name = "cartesia"
        monkeypatch.setattr(
            app,
            "CartesiaMouth",
            lambda key, **_kwargs: RefusingMouth(at_start=True) if key == "first" else spare,
        )
        settings = VoiceSettings.model_construct(
            cartesia_api_key="first", cartesia_api_key2="second"
        )
        mouth = app.make_mouth(settings)
        await mouth.start()
        utt = mouth.utterance()
        await utt.push("Your order is on its way.")
        await utt.finish()
        assert any(isinstance(ev, Audio) for ev in await drain(utt.events()))
        assert spare.spoken() == ["Your order is on its way."]
        skylar = {"hello": FillerClip("hello", b"s", [])}
        marin = {"hello": FillerClip("hello", b"m", [])}
        assert app.fillers_for(mouth, skylar, marin)["hello"].pcm16 == b"s"
        await mouth.close()

    run(t)


def test_audio_already_heard_is_not_replayed_on_another_key() -> None:
    async def t() -> None:
        spare = FakeMouth()
        mouth = FallbackMouth(RefusingMouth(after_audio=True), spare)
        await mouth.start()
        utt = mouth.utterance()
        await utt.push("Your order is on its way.")
        await utt.finish()
        events = await drain(utt.events())
        assert any(isinstance(ev, Audio) for ev in events)
        assert isinstance(events[-1], SpeechFailed)
        assert not spare.spoken()
        assert mouth.on_backup
        next_utt = mouth.utterance()
        await next_utt.push("Here is the rest.")
        await next_utt.finish()
        assert any(isinstance(ev, Audio) for ev in await drain(next_utt.events()))
        assert spare.spoken() == ["Here is the rest."]
        await mouth.close()

    run(t)


def test_unavailable_second_key_during_answer_falls_through_to_openai() -> None:
    class CannotStart(RefusingMouth):
        def utterance(self) -> Any:
            raise AssertionError("a failed backup must never be used")

    async def t() -> None:
        spare = backup()
        mouth = FallbackMouth(FallbackMouth(RefusingMouth(), CannotStart(at_start=True)), spare)
        await mouth.start()
        utt = mouth.utterance()
        await utt.push("Your order is on its way.")
        await utt.finish()
        events = await drain(utt.events())
        assert any(isinstance(ev, Audio) for ev in events)
        assert not any(isinstance(ev, SpeechFailed) for ev in events)
        assert spare.spoken() == ["Your order is on its way."]
        await mouth.close()

    run(t)


def test_cartesia_reconnect_failure_is_delivered_as_speech_failure() -> None:
    async def t() -> None:
        mouth = CartesiaMouth("fake", model="fake", version="fake", voice_id="fake")
        mouth._send = AsyncMock(side_effect=RuntimeError("connection refused"))
        utterance = mouth.utterance()
        await utterance.push("Hello.")
        await utterance.finish()
        events = await drain(utterance.events())
        assert len(events) == 1
        assert isinstance(events[0], SpeechFailed)
        await mouth.close()

    run(t)
