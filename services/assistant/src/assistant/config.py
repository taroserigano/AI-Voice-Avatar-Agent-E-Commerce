"""Settings, read from the environment and the repo-root ``.env`` (see ``.env.example``)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[4]
DEV_ASSISTANT_TOKEN = "dev-only-assistant-service-token"  # noqa: S105 - refused outside dev


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["dev", "test", "ci", "staging", "prod"] = "dev"

    # Conversations live in the same PostgreSQL database as commerce (their own tables).
    # Never DATABASE_URL: the repo-root .env may belong to other projects too.
    database_url: str = Field(
        default="postgresql+psycopg://commerce:commerce@localhost:5432/commerce",
        validation_alias=AliasChoices("ASSISTANT_DATABASE_URL", "COMMERCE_DATABASE_URL"),
    )
    commerce_api_url: str = "http://127.0.0.1:8000"  # not localhost: ~2 s on Windows
    assistant_service_token: str = DEV_ASSISTANT_TOKEN
    session_cookie_name: str = "ac_session"

    # The LLM. "auto" tries Claude, then OpenAI, then the labeled scripted fallback.
    anthropic_api_key: str | None = None
    assistant_model: str = "claude-sonnet-5"
    openai_api_key: str | None = Field(
        default=None, validation_alias=AliasChoices("OPEN_AI_API", "OPENAI_API_KEY")
    )
    assistant_openai_model: str = "gpt-6-sol"
    assistant_openai_reasoning: Literal["low", "medium", "high"] = "medium"
    # "priority" answers sooner and costs more per token.
    assistant_openai_service_tier: Literal["default", "priority", "flex"] = "default"
    # Search the policies before the model when a Xana message is about policy (one model
    # round fewer); off makes the model call search_policies itself.
    assistant_policy_prefetch: bool = True
    assistant_model_mode: Literal["auto", "claude", "openai", "scripted"] = "auto"
    assistant_max_tokens: int = 1024

    # TypeSafe Jev: typed decisions about each turn (intent, return reason, which order line,
    # escalation). With JEV_ENABLED and no key, a labeled local simulator answers instead.
    jev_enabled: bool = True
    typesafe_api_key: str | None = None
    typesafe_base_url: str = "https://api.typesafe.ai"
    # Pin a version (e.g. jev-1.13.0) once thresholds are tuned against it.
    jev_model: str = "jev-latest"
    jev_timeout_s: float = 1.5

    # Voice (Xena). Speech-to-text: Deepgram, else Groq Whisper, else the browser's.
    # Text-to-speech: Cartesia, else the browser's. Audio is never stored.
    deepgram_api_key: str | None = None
    groq_api_key: str | None = None
    groq_stt_model: str = "whisper-large-v3-turbo"
    cartesia_api_key: str | None = Field(
        default=None, validation_alias=AliasChoices("CARTESIA_SONIC_API_KEY", "CARTESIA_API_KEY")
    )
    cartesia_api_key2: str | None = Field(
        default=None, validation_alias=AliasChoices("CARTESIA_SONIC_API_KEY2", "CARTESIA_API_KEY2")
    )
    cartesia_preferred_key: Literal["primary", "secondary"] = "primary"
    cartesia_model: str = "sonic-3.6-2026-08-27"
    xana_voice_id: str = "9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"  # "Jacqueline - Reassuring Agent"
    steph_voice_id: str = "db6b0ed5-d5d3-463d-ae85-518a07d3c2b4"  # "Skylar - Friendly Guide"
    voice_max_audio_bytes: int = 2_000_000
    voice_max_seconds: int = 30
    voice_max_speak_chars: int = 800

    # Limits per conversation and per turn.
    max_input_chars: int = 2000
    max_turns_per_conversation: int = 60
    max_tool_calls_per_turn: int = 6
    commerce_timeout_s: float = 8.0

    otel_exporter_otlp_endpoint: str | None = None
    log_level: str = "INFO"

    @field_validator("database_url")
    @classmethod
    def _use_psycopg_driver(cls, url: str) -> str:
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url.removeprefix(prefix)
        return url

    @property
    def psycopg_dsn(self) -> str:
        """The same database as a plain libpq URL, for the LangGraph checkpointer."""
        return self.database_url.replace("postgresql+psycopg://", "postgresql://", 1)

    @property
    def is_dev(self) -> bool:
        return self.app_env in ("dev", "test", "ci")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if not settings.is_dev and settings.assistant_service_token == DEV_ASSISTANT_TOKEN:
        raise ValueError("Set ASSISTANT_SERVICE_TOKEN; the development default isn't allowed")
    return settings
