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


def test_tax_and_warranty_questions_are_policy_questions() -> None:
    assert wants_policy("do you charge sales tax?")
    assert wants_policy("is there a warranty on the kettle?")
    assert not wants_policy("where is my order")


def test_an_old_fault_also_searches_for_the_manufacturer_warranty() -> None:
    query = retrieval_query("my item is defective and it's been 2 months")
    assert "warranty manufacturer" in query
    # A fault with no sign of age is a return question, not a warranty one.
    assert "warranty" not in retrieval_query("the earbuds I got are defective")
