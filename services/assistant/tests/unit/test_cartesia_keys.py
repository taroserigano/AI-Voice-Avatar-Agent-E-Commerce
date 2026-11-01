from __future__ import annotations

from typing import Any

import httpx
import pytest

from assistant import voice
from assistant.config import Settings


def test_sonic_alias_takes_precedence_when_both_primary_aliases_are_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CARTESIA_SONIC_API_KEY", "sonic")
    monkeypatch.setenv("CARTESIA_API_KEY", "legacy")
    assert Settings(_env_file=None).cartesia_api_key == "sonic"


@pytest.mark.parametrize(
    ("preferred", "first_status", "expected_keys"),
    [
        ("secondary", 200, ["second"]),
        ("primary", 402, ["first", "second"]),
    ],
)
def test_speech_uses_preferred_key_and_retries_other_key(
    monkeypatch: pytest.MonkeyPatch,
    preferred: str,
    first_status: int,
    expected_keys: list[str],
) -> None:
    used: list[str] = []

    def post(_url: str, **kwargs: Any) -> httpx.Response:
        used.append(kwargs["headers"]["X-API-Key"])
        status = first_status if len(used) == 1 else 200
        return httpx.Response(status, content=b"audio" if status == 200 else b"")

    monkeypatch.setattr(voice.httpx, "post", post)
    settings = Settings.model_construct(
        cartesia_api_key="first",
        cartesia_api_key2="second",
        cartesia_preferred_key=preferred,
    )
    assert voice.speak(settings, "Hello.", "xana") == b"audio"
    assert used == expected_keys


def test_speech_uses_secondary_when_it_is_the_only_key(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings.model_construct(cartesia_api_key=None, cartesia_api_key2="second")
    monkeypatch.setattr(
        voice.httpx, "post", lambda *_args, **_kwargs: httpx.Response(200, content=b"audio")
    )
    assert voice.tts_provider(settings) == "cartesia"
    assert voice.speak(settings, "Hello.", "xana") == b"audio"


def test_all_speech_keys_failing_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings.model_construct(cartesia_api_key="first", cartesia_api_key2="second")
    monkeypatch.setattr(voice.httpx, "post", lambda *_args, **_kwargs: httpx.Response(402))
    with pytest.raises(voice.VoiceError, match="text-to-speech answered 402"):
        voice.speak(settings, "Hello.", "xana")


def test_connection_error_falls_back_to_other_key(monkeypatch: pytest.MonkeyPatch) -> None:
    used: list[str] = []

    def post(_url: str, **kwargs: Any) -> httpx.Response:
        used.append(kwargs["headers"]["X-API-Key"])
        if len(used) == 1:
            raise httpx.ConnectError("unavailable")
        return httpx.Response(200, content=b"audio")

    monkeypatch.setattr(voice.httpx, "post", post)
    settings = Settings.model_construct(cartesia_api_key="first", cartesia_api_key2="second")
    assert voice.speak(settings, "Hello.", "xana") == b"audio"
    assert used == ["first", "second"]
