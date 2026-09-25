from __future__ import annotations

from commerce.search.rrf import reciprocal_rank_fusion


def test_item_found_by_both_engines_beats_item_found_by_one() -> None:
    keyword = ["boots", "jacket", "tent"]
    semantic = ["trail-shoes", "boots", "umbrella"]

    fused = reciprocal_rank_fusion([keyword, semantic])

    assert fused[0] == "boots"
    assert set(fused) == {"boots", "jacket", "tent", "trail-shoes", "umbrella"}


def test_ties_break_deterministically_by_best_single_rank_then_list_order() -> None:
    fused = reciprocal_rank_fusion([["a", "b"], ["c", "d"]])
    # a and c tie (rank 1 each); a's list comes first. Same for b and d.
    assert fused == ["a", "c", "b", "d"]


def test_one_empty_list_returns_the_other_in_order() -> None:
    assert reciprocal_rank_fusion([[], ["x", "y", "z"]]) == ["x", "y", "z"]
    assert reciprocal_rank_fusion([]) == []


def test_duplicate_ids_within_one_list_count_once() -> None:
    fused = reciprocal_rank_fusion([["a", "a", "a", "b"], ["b"]])
    assert fused[0] == "b"
