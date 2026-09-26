"""Retrieval settings, read from the environment and the repo-root ``.env``."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[4]


class RetrievalSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Qdrant is the only vector store (decision 23) and always a real server: the local
    # native binary from `pnpm local:up`, or Qdrant Cloud when QDRANT_URL points there.
    # QDRANT_CLUSTER is the name the shared .env uses for the Qdrant Cloud cluster URL.
    qdrant_url: str = Field(
        default="http://127.0.0.1:6333",
        validation_alias=AliasChoices("QDRANT_URL", "QDRANT_CLUSTER"),
    )
    qdrant_api_key: str | None = None
    qdrant_timeout_s: int = 10

    # Embeddings: OpenAI, for product and policy text only (never customer data).
    # The shared .env names the key OPEN_AI_API; OPENAI_API_KEY also works.
    openai_api_key: str | None = Field(
        default=None, validation_alias=AliasChoices("OPEN_AI_API", "OPENAI_API_KEY")
    )
    embed_model: str = Field(
        default="text-embedding-3-small", validation_alias="RETRIEVAL_EMBED_MODEL"
    )
    embed_dimensions: int = Field(default=1536, validation_alias="RETRIEVAL_EMBED_DIMENSIONS")

    # One set of collections per developer/environment, like the OpenSearch index suffix.
    search_env: str = "dev-local"
    # How long hybrid search waits for the vector leg before answering with keywords only.
    semantic_timeout_ms: int = 250

    @property
    def qdrant_key_for_url(self) -> str | None:
        """The API key, but only over HTTPS: a key sent to plain-HTTP localhost is pointless
        and would leak if the URL were ever mistyped to a remote host."""
        return self.qdrant_api_key if self.qdrant_url.startswith("https://") else None


@lru_cache
def get_settings() -> RetrievalSettings:
    return RetrievalSettings()
