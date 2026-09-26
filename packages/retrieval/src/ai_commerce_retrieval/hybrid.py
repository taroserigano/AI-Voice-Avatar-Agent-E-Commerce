"""Hybrid retrieval: keyword search (OpenSearch) plus meaning search (Qdrant), fused by rank.

The vector leg has a time budget. If it's off, slow, or failing, the answer comes from the
keyword leg alone and :attr:`HybridRetriever.last_legs` says why, so callers can report it
(search never fails just because meaning search did).
"""

from __future__ import annotations

import logging
import time
from collections.abc import Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from typing import Literal, Protocol

from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle, TextNode
from llama_index.core.vector_stores.types import MetadataFilters

from ai_commerce_retrieval.fusion import rrf_scores
from ai_commerce_retrieval.records import Hit

log = logging.getLogger(__name__)

LegStatus = Literal["ok", "off", "timeout", "failed"]
_pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="semantic-leg")


class KeywordSearch(Protocol):
    def search(self, query: str, top_k: int) -> Sequence[Hit]: ...


class SemanticSearch(Protocol):
    def search(
        self, query: str, top_k: int, *, filters: MetadataFilters | None = None
    ) -> Sequence[Hit]: ...


class HybridRetriever(BaseRetriever):
    def __init__(
        self,
        *,
        keyword: KeywordSearch | None,
        semantic: SemanticSearch | None,
        top_k: int = 5,
        candidates: int = 20,
        filters: MetadataFilters | None = None,
        semantic_timeout_ms: int = 250,
    ) -> None:
        super().__init__()
        self.keyword = keyword
        self.semantic = semantic
        self.top_k = top_k
        self.candidates = candidates
        self.filters = filters
        self.semantic_timeout_s = semantic_timeout_ms / 1000
        self.last_legs: dict[str, LegStatus] = {}

    @staticmethod
    def _semantic_result(
        future: Future[Sequence[Hit]] | None, deadline: float
    ) -> tuple[list[Hit], LegStatus]:
        if future is None:
            return [], "off"
        remaining = deadline - time.monotonic()
        try:
            return list(future.result(timeout=max(remaining, 0.0))), "ok"
        except FutureTimeout:
            future.cancel()
            return [], "timeout"
        except Exception as exc:  # noqa: BLE001 - reported via last_legs; keywords still answer
            log.warning("semantic leg failed: %s", type(exc).__name__)
            return [], "failed"

    def _keyword_leg(self, query: str) -> tuple[list[Hit], LegStatus]:
        if self.keyword is None:
            return [], "off"
        try:
            return list(self.keyword.search(query, self.candidates)), "ok"
        except Exception as exc:  # noqa: BLE001
            log.warning("keyword leg failed: %s", type(exc).__name__)
            return [], "failed"

    def search(self, query: str) -> list[Hit]:
        """Fused hits in app terms; score is the RRF score."""
        # Start the vector leg first so it runs while the keyword leg does; its budget
        # counts from here.
        deadline = time.monotonic() + self.semantic_timeout_s
        semantic_future = (
            _pool.submit(self.semantic.search, query, self.candidates, filters=self.filters)
            if self.semantic is not None
            else None
        )
        keyword_hits, keyword_status = self._keyword_leg(query)
        semantic_hits, semantic_status = self._semantic_result(semantic_future, deadline)
        self.last_legs = {"keyword": keyword_status, "semantic": semantic_status}

        by_id: dict[str, Hit] = {}
        for hit in [*semantic_hits, *keyword_hits]:
            by_id.setdefault(hit.record_id, hit)
        fused = rrf_scores(
            [[h.record_id for h in keyword_hits], [h.record_id for h in semantic_hits]]
        )
        return [
            Hit(record_id=rid, score=score, text=by_id[rid].text, metadata=by_id[rid].metadata)
            for rid, score in fused[: self.top_k]
        ]

    def _retrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        return [
            NodeWithScore(
                node=TextNode(id_=h.record_id, text=h.text, metadata=dict(h.metadata)),
                score=h.score,
            )
            for h in self.search(query_bundle.query_str)
        ]
