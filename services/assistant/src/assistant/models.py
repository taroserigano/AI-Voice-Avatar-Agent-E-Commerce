"""Which chat model answers: Claude, OpenAI, or the labeled scripted fallback."""

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


def _openai_model_works(key: str, model: str) -> tuple[bool, str | None]:
    try:
        resp = httpx.get(
            f"https://api.openai.com/v1/models/{model}",
            headers={"Authorization": f"Bearer {key}"},
            timeout=5,
        )
    except httpx.HTTPError as exc:
        return False, f"couldn't reach OpenAI ({type(exc).__name__})"
    if resp.status_code == 200:
        return True, None
    if resp.status_code in (401, 403):
        return False, "OPEN_AI_API was rejected"
    if resp.status_code == 404:
        return False, f"OpenAI model {model} is not available"
    return False, f"OpenAI answered {resp.status_code}"


@lru_cache
def choose_model() -> ModelChoice:
    settings = get_settings()
    scripted = ModelChoice(ScriptedChatModel(), SCRIPTED_MODEL_NAME, simulated=True)
    if settings.assistant_model_mode == "scripted":
        return ModelChoice(scripted.model, scripted.name, True, "ASSISTANT_MODEL_MODE=scripted")
    reason: str | None = "No working assistant model key is configured"
    if settings.assistant_model_mode in ("auto", "claude") and settings.anthropic_api_key:
        ok, reason = (
            _anthropic_key_works(settings.anthropic_api_key)
            if settings.assistant_model_mode == "auto"
            else (True, None)
        )
        if ok:
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
    if settings.assistant_model_mode in ("auto", "openai") and settings.openai_api_key:
        ok, reason = (
            _openai_model_works(settings.openai_api_key, settings.assistant_openai_model)
            if settings.assistant_model_mode == "auto"
            else (True, None)
        )
        if ok:
            from langchain_openai import ChatOpenAI

            openai = ChatOpenAI(
                model=settings.assistant_openai_model,
                api_key=settings.openai_api_key,
                use_responses_api=True,
                reasoning={"effort": settings.assistant_openai_reasoning},
                max_tokens=settings.assistant_max_tokens,
                streaming=True,
                timeout=60,
                max_retries=2,
            )
            return ModelChoice(openai, settings.assistant_openai_model, simulated=False)
    log.warning("using the scripted assistant model: %s", reason)
    return ModelChoice(scripted.model, scripted.name, True, reason)
