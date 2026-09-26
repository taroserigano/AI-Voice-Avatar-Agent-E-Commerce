"""Chat models for the planner: OpenAI (decision 22) or the labeled scripted stand-in."""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.language_models.chat_models import BaseChatModel

from ai_commerce_planner.config import PlannerSettings
from ai_commerce_planner.scripted import ScriptedPlannerModel


@dataclass(frozen=True)
class PlannerModels:
    main: BaseChatModel
    helper: BaseChatModel
    name: str
    simulated: bool
    reason: str | None = None  # why it's simulated, for the "Simulated planner" badge


def planner_models(settings: PlannerSettings, servings: int | None = None) -> PlannerModels:
    provider = settings.planner_provider
    if provider == "auto":
        provider = "openai" if settings.openai_api_key else "scripted"
    if provider == "scripted":
        scripted = ScriptedPlannerModel(servings=servings or 4)
        reason = None if settings.planner_provider == "scripted" else "no OpenAI key"
        return PlannerModels(
            scripted, scripted, "scripted-planner", True, reason or "scripted mode"
        )
    if not settings.openai_api_key:
        raise RuntimeError("PLANNER_PROVIDER=openai needs OPEN_AI_API (or OPENAI_API_KEY)")

    from langchain_openai import ChatOpenAI

    def chat(model: str) -> BaseChatModel:
        return ChatOpenAI(
            model=model,
            api_key=settings.openai_api_key,
            use_responses_api=True,
            timeout=30,
            max_retries=2,
        )

    return PlannerModels(
        chat(settings.planner_model),
        chat(settings.planner_subagent_model),
        settings.planner_model,
        simulated=False,
    )
