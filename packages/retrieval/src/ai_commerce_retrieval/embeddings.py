"""The embedding model. Always passed explicitly: nothing here reads LlamaIndex's global
``Settings``, whose defaults would silently pick a model and vendor for us."""

from __future__ import annotations

from llama_index.core.base.embeddings.base import BaseEmbedding

from ai_commerce_retrieval.config import RetrievalSettings


class EmbeddingConfigError(RuntimeError):
    pass


def openai_embedder(settings: RetrievalSettings) -> BaseEmbedding:
    if not settings.openai_api_key:
        raise EmbeddingConfigError(
            "No OpenAI key (OPEN_AI_API or OPENAI_API_KEY), so meaning-based search is off."
        )
    from llama_index.embeddings.openai import OpenAIEmbedding

    return OpenAIEmbedding(
        model=settings.embed_model,
        dimensions=settings.embed_dimensions,
        api_key=settings.openai_api_key,
        max_retries=3,
        timeout=20.0,
    )
