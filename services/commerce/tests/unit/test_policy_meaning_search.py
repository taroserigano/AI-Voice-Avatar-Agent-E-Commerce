"""Policy search fuses keywords with Qdrant meaning search, and never fails because of it."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import pytest

from commerce.policies import search as policy_search

STANDARD = "returns-and-refunds#rr-4-1"  # "Opened items are fine."
PRIVACY = "returns-and-refunds#rr-14"


@dataclass
class FakeHit:
    record_id: str


class FakeKeywords:
    def __init__(self, ids: list[str]) -> None:
        self.ids = ids

    def search(self, query: str, top_k: int) -> list[str]:
        return self.ids[:top_k]


class FakeVectors:
    def __init__(self, ids: list[str], delay_s: float = 0.0, fail: bool = False) -> None:
        self.ids, self.delay_s, self.fail = ids, delay_s, fail

    def search(self, query: str, top_k: int) -> list[FakeHit]:
        if self.fail:
            raise ConnectionError("qdrant is down")
        time.sleep(self.delay_s)
        return [FakeHit(i) for i in self.ids[:top_k]]


@pytest.fixture
def wired(monkeypatch: pytest.MonkeyPatch) -> Any:
    def wire(keyword_ids: list[str], vectors: FakeVectors) -> None:
        monkeypatch.setattr(
            policy_search, "get_policy_keyword_index", lambda: FakeKeywords(keyword_ids)
        )
        monkeypatch.setattr(policy_search, "_qdrant_policy_index", lambda: vectors)
        monkeypatch.setattr(policy_search, "_sync_in_background", lambda: None)
        policy_search._cache.clear()

    return wire


def test_meaning_search_brings_up_the_section_keywords_missed(wired: Any) -> None:
    wired([PRIVACY], FakeVectors([STANDARD]))
    result = policy_search.search_policies("can I send back opened headphones?", top_k=4)
    assert result.semantic == "used"
    assert STANDARD in [h.key for h in result.hits]


def test_a_slow_vector_leg_is_dropped_and_keywords_answer(
    wired: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(policy_search.get_settings(), "policy_semantic_timeout_ms", 50)
    wired([PRIVACY], FakeVectors([STANDARD], delay_s=0.5))
    started = time.monotonic()
    result = policy_search.search_policies("opened headphones", top_k=4)
    assert time.monotonic() - started < 0.4
    assert result.semantic == "unavailable"
    assert [h.key for h in result.hits] == [PRIVACY]


def test_a_down_vector_store_never_fails_the_search(wired: Any) -> None:
    wired([PRIVACY], FakeVectors([], fail=True))
    result = policy_search.search_policies("opened headphones", top_k=4)
    assert result.semantic == "unavailable"
    assert [h.key for h in result.hits] == [PRIVACY]


class CountingVectors(FakeVectors):
    calls = 0

    def search(self, query: str, top_k: int) -> list[FakeHit]:
        CountingVectors.calls += 1
        return super().search(query, top_k)


def test_a_repeated_question_is_answered_from_the_cache_until_a_policy_changes(
    wired: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    CountingVectors.calls = 0
    wired([PRIVACY], CountingVectors([STANDARD]))
    first = policy_search.search_policies("Can I return opened headphones?", top_k=4)
    again = policy_search.search_policies("can i return  opened headphones?", top_k=4)
    assert again.hits == first.hits and CountingVectors.calls == 1
    # An edited policy changes the content hash: the old answer isn't served.
    monkeypatch.setattr(policy_search, "content_hash", lambda: "edited")
    policy_search.search_policies("can I return opened headphones?", top_k=4)
    assert CountingVectors.calls == 2


def test_a_keywords_only_answer_is_not_cached(
    wired: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    wired([PRIVACY], FakeVectors([], fail=True))
    policy_search.search_policies("opened headphones", top_k=4)
    # Qdrant is back: the next search uses it instead of the keywords-only answer.
    monkeypatch.setattr(policy_search, "_qdrant_policy_index", lambda: FakeVectors([STANDARD]))
    result = policy_search.search_policies("opened headphones", top_k=4)
    assert result.semantic == "used" and STANDARD in [h.key for h in result.hits]
