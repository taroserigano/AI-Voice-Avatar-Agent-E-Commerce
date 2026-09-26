"""Hybrid search behavior with stand-in legs (the real Qdrant leg is in integration tests)."""

from __future__ import annotations

import time
from collections.abc import Sequence

from llama_index.core.vector_stores.types import MetadataFilter, MetadataFilters

from ai_commerce_retrieval.hybrid import HybridRetriever
from ai_commerce_retrieval.records import Hit


def hits(*ids: str) -> list[Hit]:
    return [Hit(record_id=i, score=1.0, text=f"text of {i}", metadata={"id": i}) for i in ids]


class Leg:
    def __init__(self, result: list[Hit], delay_s: float = 0.0, error: Exception | None = None):
        self.result, self.delay_s, self.error = result, delay_s, error
        self.calls: list[dict[str, object]] = []

    def search(
        self, query: str, top_k: int, *, filters: MetadataFilters | None = None
    ) -> Sequence[Hit]:
        self.calls.append({"query": query, "top_k": top_k, "filters": filters})
        time.sleep(self.delay_s)
        if self.error:
            raise self.error
        return self.result


def test_a_record_found_by_both_legs_ranks_first() -> None:
    r = HybridRetriever(keyword=Leg(hits("a", "b")), semantic=Leg(hits("c", "b")), top_k=3)

    result = r.search("milk")

    assert [h.record_id for h in result] == ["b", "a", "c"]
    assert r.last_legs == {"keyword": "ok", "semantic": "ok"}


def test_slow_meaning_search_falls_back_to_keywords_within_the_budget() -> None:
    r = HybridRetriever(
        keyword=Leg(hits("a", "b")), semantic=Leg(hits("z"), delay_s=1.0), semantic_timeout_ms=100
    )

    started = time.monotonic()
    result = r.search("milk")

    assert time.monotonic() - started < 0.6
    assert [h.record_id for h in result] == ["a", "b"]
    assert r.last_legs["semantic"] == "timeout"


def test_failing_meaning_search_is_reported_not_raised() -> None:
    r = HybridRetriever(keyword=Leg(hits("a")), semantic=Leg([], error=ConnectionError("down")))

    assert [h.record_id for h in r.search("milk")] == ["a"]
    assert r.last_legs["semantic"] == "failed"


def test_without_a_vector_index_search_is_keyword_only() -> None:
    r = HybridRetriever(keyword=Leg(hits("a")), semantic=None)

    assert [h.record_id for h in r.search("milk")] == ["a"]
    assert r.last_legs == {"keyword": "ok", "semantic": "off"}


def test_filters_reach_the_meaning_leg_and_top_k_cuts_results() -> None:
    filters = MetadataFilters(filters=[MetadataFilter(key="status", value="approved")])
    semantic = Leg(hits("a", "b", "c", "d"))
    r = HybridRetriever(keyword=None, semantic=semantic, top_k=2, candidates=7, filters=filters)

    assert [h.record_id for h in r.search("refund")] == ["a", "b"]
    assert semantic.calls == [{"query": "refund", "top_k": 7, "filters": filters}]


def test_llamaindex_retriever_interface_returns_app_record_ids() -> None:
    r = HybridRetriever(keyword=Leg(hits("a")), semantic=Leg(hits("a")))

    nodes = r.retrieve("milk")

    assert [(n.node.node_id, n.node.get_content()) for n in nodes] == [("a", "text of a")]
