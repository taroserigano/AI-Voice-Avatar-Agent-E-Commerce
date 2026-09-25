"""Settings, read from the environment and the repo-root ``.env`` (see ``.env.example``)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["dev", "test", "ci", "staging", "prod"] = "dev"

    database_url: str = "postgresql+psycopg://commerce:commerce@localhost:5432/commerce"
    redis_url: str = "redis://localhost:6379/0"
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
    # How long a search waits for Pinecone before answering with keyword results only.
    semantic_timeout_ms: int = 250
    keyword_top_k: int = 100

    auth_provider: Literal["dev", "oidc"] = "dev"
    session_secret: str = Field(default="dev-only-session-secret-change-me", min_length=16)
    session_ttl_hours: int = 12
    cookie_secure: bool = False
    session_cookie_name: str = "ac_session"
    web_origin: str = "http://localhost:3000"

    signin_max_failures_per_account: int = 5
    signin_max_attempts_per_ip: int = 30
    signin_window_seconds: int = 900

    oidc_issuer: str | None = None
    oidc_client_id: str | None = None
    oidc_client_secret: str | None = None
    oidc_redirect_uri: str | None = None

    otel_exporter_otlp_endpoint: str | None = None
    log_level: str = "INFO"

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
