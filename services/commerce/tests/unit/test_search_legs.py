"""How search combines its two backends when one is slow, failing, or off."""

from __future__ import annotations

import time

import pytest

from commerce.catalog import service
from commerce.catalog.schemas import LegStatus
from commerce.config import get_settings
from commerce.search.semantic import SemanticIndex
from tests.unit.fakes.pinecone_standin import PineconeIndexStandIn


class Keyword:
    def __init__(self, ids: list[str], fail: bool = False) -> None:
        self.ids, self.fail = ids, fail

    def search(self, query: str, top_k: int) -> list[str]:
        if self.fail:
            raise ConnectionError("opensearch down")
        return self.ids


class SlowStandIn(PineconeIndexStandIn):
    def search(self, **kw):  # type: ignore[no-untyped-def]
        time.sleep(1.0)
        return super().search(**kw)


@pytest.fixture
def pinecone_on(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "pinecone_api_key", "configured-for-this-test")
    monkeypatch.setattr(get_settings(), "semantic_timeout_ms", 200)


def test_both_backends_are_fused(monkeypatch: pytest.MonkeyPatch, pinecone_on: None) -> None:
    standin = PineconeIndexStandIn(scripted_hits=[("b", 0.9), ("c", 0.8)])
    monkeypatch.setattr(service, "get_keyword_index", lambda: Keyword(["a", "b"]))
    monkeypatch.setattr(service, "get_semantic_index", lambda: SemanticIndex(standin, "ns"))

    ids, meta = service._run_legs("rain boots")

    assert ids[0] == "b"  # found by both
    assert set(ids) == {"a", "b", "c"}
    assert (meta.keyword, meta.semantic, meta.notice) == (LegStatus.OK, LegStatus.OK, None)


def test_slow_semantic_leg_is_cut_off_at_the_budget(
    monkeypatch: pytest.MonkeyPatch, pinecone_on: None
) -> None:
    slow = SemanticIndex(SlowStandIn(scripted_hits=[("z", 0.9)]), "ns")
    monkeypatch.setattr(service, "get_keyword_index", lambda: Keyword(["a"]))
    monkeypatch.setattr(service, "get_semantic_index", lambda: slow)

    started = time.perf_counter()
    ids, meta = service._run_legs("rain boots")
    elapsed = time.perf_counter() - started

    assert elapsed < 0.6
    assert ids == ["a"]
    assert meta.semantic == LegStatus.UNAVAILABLE
    assert meta.notice


def test_semantic_setup_failure_degrades_to_keyword(
    monkeypatch: pytest.MonkeyPatch, pinecone_on: None
) -> None:
    def broken() -> SemanticIndex:
        raise RuntimeError("wrong index")

    monkeypatch.setattr(service, "get_keyword_index", lambda: Keyword(["a"]))
    monkeypatch.setattr(service, "get_semantic_index", broken)

    ids, meta = service._run_legs("q")
    assert ids == ["a"]
    assert (meta.keyword, meta.semantic) == (LegStatus.OK, LegStatus.UNAVAILABLE)


def test_no_pinecone_key_means_disabled_not_faked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "pinecone_api_key", None)
    monkeypatch.setattr(service, "get_keyword_index", lambda: Keyword(["a"]))

    ids, meta = service._run_legs("q")
    assert ids == ["a"]
    assert meta.semantic == LegStatus.DISABLED
    assert meta.notice and "Pinecone" in meta.notice


def test_both_backends_down_reports_reduced_mode(
    monkeypatch: pytest.MonkeyPatch, pinecone_on: None
) -> None:
    def broken() -> SemanticIndex:
        raise RuntimeError("down")

    monkeypatch.setattr(service, "get_keyword_index", lambda: Keyword([], fail=True))
    monkeypatch.setattr(service, "get_semantic_index", broken)

    ids, meta = service._run_legs("q")
    assert ids == []
    assert meta.keyword == meta.semantic == LegStatus.UNAVAILABLE
    assert meta.notice and "reduced mode" in meta.notice
