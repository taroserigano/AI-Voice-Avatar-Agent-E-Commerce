"""A rejected Claude key must not leave a working OpenAI assistant in scripted mode."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from assistant import models


def test_auto_uses_openai_after_claude_key_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = SimpleNamespace(
        assistant_model_mode="auto",
        anthropic_api_key="bad-claude-key",
        openai_api_key="working-openai-key",
        assistant_openai_model="gpt-6-sol",
        assistant_openai_reasoning="medium",
        assistant_max_tokens=1024,
    )
    monkeypatch.setattr(models, "get_settings", lambda: settings)
    monkeypatch.setattr(
        models, "_anthropic_key_works", lambda key: (False, "ANTHROPIC_API_KEY was rejected")
    )
    monkeypatch.setattr(models, "_openai_model_works", lambda key, model: (True, None))
    models.choose_model.cache_clear()
    try:
        selected = models.choose_model()
        assert selected.name == "gpt-6-sol"
        assert selected.simulated is False
    finally:
        models.choose_model.cache_clear()


def test_a_network_blip_at_startup_doesnt_pin_the_scripted_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = SimpleNamespace(
        assistant_model_mode="auto",
        anthropic_api_key=None,
        openai_api_key="working-openai-key",
        assistant_openai_model="gpt-6-sol",
        assistant_openai_reasoning="medium",
        assistant_max_tokens=1024,
    )
    reachable = False
    clock = [1000.0]
    monkeypatch.setattr(models, "get_settings", lambda: settings)
    monkeypatch.setattr(
        models,
        "_openai_model_works",
        lambda key, model: (True, None) if reachable else (False, "couldn't reach OpenAI"),
    )
    monkeypatch.setattr(models.time, "monotonic", lambda: clock[0])
    models.choose_model.cache_clear()
    monkeypatch.setattr(models, "_fallback_since", None)
    try:
        assert models.current_model().simulated is True
        reachable = True
        clock[0] += 10
        assert models.current_model().simulated is True  # not re-probed on every turn
        clock[0] += models.RECHECK_UNREACHABLE_S
        assert models.current_model().name == "gpt-6-sol"
    finally:
        models.choose_model.cache_clear()


def test_auto_uses_labeled_script_when_both_providers_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = SimpleNamespace(
        assistant_model_mode="auto",
        anthropic_api_key="bad-claude-key",
        openai_api_key="bad-openai-key",
        assistant_openai_model="gpt-6-sol",
    )
    monkeypatch.setattr(models, "get_settings", lambda: settings)
    monkeypatch.setattr(models, "_anthropic_key_works", lambda key: (False, "rejected"))
    monkeypatch.setattr(models, "_openai_model_works", lambda key, model: (False, "rejected"))
    models.choose_model.cache_clear()
    try:
        selected = models.choose_model()
        assert selected.name == "scripted"
        assert selected.simulated is True
    finally:
        models.choose_model.cache_clear()
