"""Test-only embedding models. App code never imports this module (see test_boundaries)."""

from __future__ import annotations

import hashlib
import math
import re

from llama_index.core.base.embeddings.base import BaseEmbedding
from pydantic import PrivateAttr

DIMS = 64


class HashingEmbedding(BaseEmbedding):
    """Deterministic bag-of-words vectors: texts sharing words point the same way.

    Good enough to test ranking, filters, and sync against a real Qdrant without paying for
    embeddings. It counts document embeddings so tests can prove sync skips unchanged records.
    """

    model_name: str = "test-hashing"
    _documents_embedded: int = PrivateAttr(default=0)

    @property
    def documents_embedded(self) -> int:
        return self._documents_embedded

    @staticmethod
    def vector(text: str) -> list[float]:
        v = [0.0] * DIMS
        for word in re.findall(r"[a-z]+", text.lower()):
            v[int(hashlib.md5(word.encode(), usedforsecurity=False).hexdigest(), 16) % DIMS] += 1.0
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]

    def _get_text_embedding(self, text: str) -> list[float]:
        self._documents_embedded += 1
        return self.vector(text)

    def _get_query_embedding(self, query: str) -> list[float]:
        return self.vector(query)

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return self.vector(query)


class ExplodingEmbedding(BaseEmbedding):
    """Stands in for LlamaIndex's global default: any use fails the test."""

    model_name: str = "must-not-be-used"

    def _get_text_embedding(self, text: str) -> list[float]:
        raise AssertionError("fell back to LlamaIndex's global Settings.embed_model")

    def _get_query_embedding(self, query: str) -> list[float]:
        raise AssertionError("fell back to LlamaIndex's global Settings.embed_model")

    async def _aget_query_embedding(self, query: str) -> list[float]:
        raise AssertionError("fell back to LlamaIndex's global Settings.embed_model")
