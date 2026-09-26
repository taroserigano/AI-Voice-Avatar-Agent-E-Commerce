from __future__ import annotations

import pytest

from ai_commerce_retrieval.fusion import reciprocal_rank_fusion, rrf_scores


def test_item_found_by_both_engines_beats_item_found_by_one() -> None:
    keyword = ["boots", "jacket", "tent"]
    semantic = ["trail-shoes", "boots", "umbrella"]

    fused = reciprocal_rank_fusion([keyword, semantic])

    assert fused[0] == "boots"
    assert set(fused) == {"boots", "jacket", "tent", "trail-shoes", "umbrella"}


def test_ties_break_deterministically_by_best_single_rank_then_list_order() -> None:
    assert reciprocal_rank_fusion([["a", "b"], ["c", "d"]]) == ["a", "c", "b", "d"]


def test_one_empty_list_returns_the_other_in_order() -> None:
    assert reciprocal_rank_fusion([[], ["x", "y", "z"]]) == ["x", "y", "z"]
    assert reciprocal_rank_fusion([]) == []


def test_duplicate_ids_within_one_list_count_once() -> None:
    assert reciprocal_rank_fusion([["a", "a", "a", "b"], ["b"]])[0] == "b"


def test_scores_use_k_60_ranks_from_one() -> None:
    assert rrf_scores([["a"], ["a"]]) == [("a", pytest.approx(2 / 61))]


def test_matches_commerce_search_ordering() -> None:
    """Commerce moves to this module; the product-search order must not change when it does."""
    commerce_rrf = pytest.importorskip("commerce.search.rrf")
    cases = [
        [["boots", "jacket", "tent"], ["trail-shoes", "boots", "umbrella"]],
        [["a", "b"], ["c", "d"]],
        [["a", "a", "a", "b"], ["b"]],
        [["p1", "p2", "p3", "p4"], ["p4", "p9", "p1"], ["p9"]],
    ]
    for lists in cases:
        assert reciprocal_rank_fusion(lists) == commerce_rrf.reciprocal_rank_fusion(lists)
