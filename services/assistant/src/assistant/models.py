"""Which chat model answers: Claude when its key works, otherwise the labeled scripted model."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache

import httpx
from langchain_core.language_models import BaseChatModel

from assistant.config import get_settings
from assistant.scripted import SCRIPTED_MODEL_NAME, ScriptedChatModel

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelChoice:
    model: BaseChatModel
    name: str
    simulated: bool
    reason: str | None = None


def _anthropic_key_works(key: str) -> tuple[bool, str | None]:
    try:
        resp = httpx.get(
            "https://api.anthropic.com/v1/models",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
            timeout=5,
        )
    except httpx.HTTPError as exc:
        return False, f"couldn't reach Anthropic ({type(exc).__name__})"
    if resp.status_code == 200:
        return True, None
    if resp.status_code in (401, 403):
        return False, "ANTHROPIC_API_KEY was rejected"
    return False, f"Anthropic answered {resp.status_code}"


@lru_cache
def choose_model() -> ModelChoice:
    settings = get_settings()
    scripted = ModelChoice(ScriptedChatModel(), SCRIPTED_MODEL_NAME, simulated=True)
    if settings.assistant_model_mode == "scripted":
        return ModelChoice(scripted.model, scripted.name, True, "ASSISTANT_MODEL_MODE=scripted")
    if not settings.anthropic_api_key:
        return ModelChoice(scripted.model, scripted.name, True, "ANTHROPIC_API_KEY is not set")
    if settings.assistant_model_mode == "auto":
        ok, reason = _anthropic_key_works(settings.anthropic_api_key)
        if not ok:
            log.warning("using the scripted assistant model: %s", reason)
            return ModelChoice(scripted.model, scripted.name, True, reason)

    from langchain_anthropic import ChatAnthropic

    claude = ChatAnthropic(
        model=settings.assistant_model,
        api_key=settings.anthropic_api_key,
        max_tokens=settings.assistant_max_tokens,
        streaming=True,
        timeout=60,
        max_retries=2,
    )
    return ModelChoice(claude, settings.assistant_model, simulated=False)
