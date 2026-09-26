"""Build a :class:`VectorIndex` from settings, or report why meaning search is off."""

from __future__ import annotations

from qdrant_client import QdrantClient

from ai_commerce_retrieval.config import RetrievalSettings, get_settings
from ai_commerce_retrieval.embeddings import openai_embedder
from ai_commerce_retrieval.index import VectorIndex
from ai_commerce_retrieval.qdrant_collections import collection_name


def qdrant_client(settings: RetrievalSettings) -> QdrantClient:
    return QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_key_for_url,
        timeout=settings.qdrant_timeout_s,
    )


def vector_index(corpus: str, settings: RetrievalSettings | None = None) -> VectorIndex:
    """The collection for ``corpus`` (``products``, ``policies``) in this SEARCH_ENV.

    Raises ``EmbeddingConfigError`` without an OpenAI key, ``CollectionOwnershipError`` for a
    collection this app didn't create, and Qdrant's own errors when the server is down.
    """
    settings = settings or get_settings()
    return VectorIndex(
        qdrant_client(settings),
        collection_name(corpus, settings.search_env),
        openai_embedder(settings),
        corpus=corpus,
        embed_model_name=settings.embed_model,
        dimensions=settings.embed_dimensions,
    )
