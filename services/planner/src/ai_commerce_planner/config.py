"""Planner settings, read from the environment and the repo-root ``.env``."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[4]


class PlannerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_env: Literal["dev", "test", "ci", "staging", "prod"] = "dev"

    # Model provider (decision 22: OpenAI). "auto" uses OpenAI when a key is set and the
    # labeled scripted planner otherwise, so the demo and tests run without spending tokens.
    planner_provider: Literal["auto", "openai", "scripted"] = "auto"
    openai_api_key: str | None = Field(
        default=None, validation_alias=AliasChoices("OPEN_AI_API", "OPENAI_API_KEY")
    )
    planner_model: str = "gpt-5.5"
    planner_subagent_model: str = "gpt-5.4-mini"

    # Hard caps per task (decision v2-5).
    planner_max_model_calls: int = 12
    planner_max_tool_calls: int = 40
    planner_timeout_s: float = 90.0

    # How the assistant reaches the planner (decision v2-1: in-process first).
    planner_transport: Literal["inproc", "a2a"] = "inproc"
    planner_a2a_url: str = "http://127.0.0.1:8302"
    planner_host: str = "127.0.0.1"  # internal only (decision v2-2)
    planner_port: int = 8302
    # Shared secret for the gateway's short-lived delegation tokens (HS256). The dev
    # defaults below are refused outside dev by check().
    planner_delegation_secret: str = "dev-only-planner-delegation-secret-change-me"  # noqa: S105

    # The planner's own commerce identity: catalog reads only (PLANNER_ROUTES).
    commerce_api_url: str = Field(
        default="http://localhost:8000", validation_alias="COMMERCE_API_URL"
    )
    planner_service_token: str = "dev-only-planner-service-token"  # noqa: S105

    @property
    def uses_dev_secrets(self) -> bool:
        return self.planner_delegation_secret.startswith(
            "dev-only"
        ) or self.planner_service_token.startswith("dev-only")

    def check(self) -> None:
        if self.uses_dev_secrets and self.app_env in ("staging", "prod"):
            raise RuntimeError(
                "Set PLANNER_DELEGATION_SECRET and PLANNER_SERVICE_TOKEN outside dev"
            )


@lru_cache
def get_settings() -> PlannerSettings:
    return PlannerSettings()
