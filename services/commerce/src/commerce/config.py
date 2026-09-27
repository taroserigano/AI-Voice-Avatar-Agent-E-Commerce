"""Settings, read from the environment and the repo-root ``.env`` (see ``.env.example``)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, field_validator, model_validator
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

    # COMMERCE_DATABASE_URL, not DATABASE_URL: the repo-root .env may be shared with other
    # projects, and this app must never migrate another project's database.
    database_url: str = Field(
        default="postgresql+psycopg://commerce:commerce@localhost:5432/commerce",
        validation_alias="COMMERCE_DATABASE_URL",
    )
    opensearch_url: str = "http://localhost:9200"

    # Pinecone is always the real service. With no key, meaning-based search is reported
    # as unavailable; there is no local substitute.
    pinecone_api_key: str | None = None
    pinecone_index: str = Field(
        default="ai-commerce",
        validation_alias=AliasChoices("PINECONE_INDEX", "PINECONE_INDEX_NAME"),
    )
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"
    pinecone_embed_model: str = "llama-text-embed-v2"

    # Suffix for every search index and Pinecone namespace, e.g. "dev-taro" ->
    # OpenSearch index "products-dev-taro" and Pinecone namespace "products-dev-taro".
    search_env: str = "dev-local"
    semantic_top_k: int = 20
    semantic_min_score: float = 0.0
    # A meaning-only hit (one OpenSearch didn't find) must score at least this fraction of the
    # query's best Pinecone score: the top K always has a tail of barely related products.
    semantic_relative_score: float = Field(default=0.8, ge=0.0, le=1.0)
    # How long a search waits for Pinecone before answering with keyword results only.
    semantic_timeout_ms: int = 250
    # Keyword candidates per search. A search that fills it reports its total as a lower bound
    # ("400+") rather than an exact count.
    keyword_top_k: int = 400

    # Standard shipping (content/policies/shipping-and-delivery.md): $5.99, free at $35
    # after discounts and before tax. Shown in the cart before checkout.
    shipping_minor: int = 599
    free_shipping_at_minor: int = 3500

    # Keys the one-way customer hash put on telemetry (never the raw customer ID).
    session_secret: str = Field(default="dev-only-session-secret-change-me", min_length=16)
    session_ttl_hours: int = 12
    cookie_secure: bool = False
    session_cookie_name: str = "ac_session"

    # Shared secret the assistant service sends (with X-On-Behalf-Of) to act for a signed-in
    # customer on a short list of routes (see commerce.auth.deps). Outside development it must
    # be set to a long random value; the development default is refused there.
    assistant_service_token: str | None = DEV_ASSISTANT_TOKEN

    otel_exporter_otlp_endpoint: str | None = None
    log_level: str = "INFO"

    @field_validator("database_url")
    @classmethod
    def _use_psycopg_driver(cls, url: str) -> str:
        # Hosted providers (Supabase, Neon) hand out postgres:// or postgresql:// URLs.
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url.removeprefix(prefix)
        return url

    @model_validator(mode="after")
    def _no_dev_secrets_outside_dev(self) -> Settings:
        if not self.is_dev and self.assistant_service_token == DEV_ASSISTANT_TOKEN:
            raise ValueError("Set ASSISTANT_SERVICE_TOKEN; the development default isn't allowed")
        return self

    @property
    def policies_index(self) -> str:
        return f"policies-{self.search_env}"

    @property
    def policies_namespace(self) -> str:
        return f"policies-{self.search_env}"

    @property
    def products_index(self) -> str:
        return f"products-{self.search_env}"

    @property
    def products_namespace(self) -> str:
        return f"products-{self.search_env}"

    @property
    def is_dev(self) -> bool:
        return self.app_env in ("dev", "test", "ci")


@lru_cache
def get_settings() -> Settings:
    return Settings()
