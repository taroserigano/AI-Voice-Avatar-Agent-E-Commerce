"""Reciprocal rank fusion: merge ranked lists without comparing their raw scores.

OpenSearch BM25 scores and Pinecone similarity scores are on different scales, so we fuse
by rank only: score(d) = sum over lists of 1 / (k + rank_in_list(d)), with rank from 1.
k = 60 is the value from the original paper (Cormack et al., 2009).
"""

from __future__ import annotations

from collections.abc import Sequence

DEFAULT_K = 60


def reciprocal_rank_fusion(ranked_lists: Sequence[Sequence[str]], k: int = DEFAULT_K) -> list[str]:
    scores: dict[str, float] = {}
    first_seen: dict[str, tuple[int, int]] = {}
    for list_index, ranked in enumerate(ranked_lists):
        seen_in_list: set[str] = set()
        for rank, doc_id in enumerate(ranked, start=1):
            if doc_id in seen_in_list:
                continue  # a list that repeats an ID shouldn't count it twice
            seen_in_list.add(doc_id)
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
            first_seen.setdefault(doc_id, (rank, list_index))
    # Ties break toward the better single-list rank, then the earlier list: deterministic.
    return sorted(scores, key=lambda d: (-scores[d], first_seen[d]))
