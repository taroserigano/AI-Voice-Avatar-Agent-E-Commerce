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
