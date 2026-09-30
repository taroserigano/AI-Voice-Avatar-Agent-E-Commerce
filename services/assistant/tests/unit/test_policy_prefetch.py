"""The words the policy prefetch searches with (the search itself is covered live by the
golden sets in evals/xana)."""

from __future__ import annotations

from assistant.policy_prefetch import retrieval_query, wants_policy


def test_refund_amount_questions_search_for_how_much_you_get_back() -> None:
    assert retrieval_query("How do you calculate my refund?") == "much back paid refund"
    assert retrieval_query("How much will I get back for the sweater?") == "much back paid sweater"
    # Other "how much" questions keep their own words.
    assert retrieval_query("How much is shipping?") == "much shipping"


def test_only_policy_questions_are_searched_first() -> None:
    assert wants_policy("How do you calculate my refund?")
    assert not wants_policy("find me organic whole milk")
