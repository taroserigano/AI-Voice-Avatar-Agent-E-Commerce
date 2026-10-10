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


def test_food_that_went_bad_asks_for_the_perishable_rule() -> None:
    """Found by the golden eval: "the whole milk ... was bad" didn't retrieve section 2.2."""
    from assistant.policy_prefetch import retrieval_query

    assert "perishable" in retrieval_query(
        "the whole milk from the older grocery order was bad, refund it"
    )
    assert "perishable" in retrieval_query("my eggs were cracked")
    assert "perishable" not in retrieval_query("my headphones were cracked")
    from assistant.policy_prefetch import wants_policy

    assert wants_policy("my eggs were cracked")
    assert not wants_policy("do you have eggs?")


def test_buying_subscriptions_and_delivery_times_are_policy_questions() -> None:
    """Voice answered these from the prompt, uncited (s-011, s-051)."""
    from assistant.policy_prefetch import wants_policy

    assert wants_policy("can I buy what's in my cart?")
    assert wants_policy("do you have a coffee subscription?")
    assert wants_policy("when will my order arrive if I order today?")
    assert wants_policy("how long does shipping take?")
    # Shopping and order status aren't policy questions.
    assert not wants_policy("where can I buy oat milk?")
    assert not wants_policy("when will my order arrive?")


def test_asking_xena_to_decide_searches_for_what_assistants_may_do() -> None:
    from assistant.policy_prefetch import retrieval_query

    for asked in ("can you approve my refund yourself?", "could you make an exception?"):
        query = retrieval_query(asked)
        assert "never decide" in query and "customer confirms" in query
    assert "never decide" not in retrieval_query("how long do refunds take?")


def test_a_malformed_citation_is_invalid_not_left_in_the_answer() -> None:
    from assistant.turns import split_citations

    good = "shipping-and-delivery#sd-3"
    valid, invalid = split_citations(
        f"Two to five days. [[cite:shipping#...]] [[cite:{good}]]", {good: {"cite": good}}
    )
    assert valid == [{"cite": good}] and invalid == ["shipping#..."]


def test_the_readback_says_units_returned_before_first() -> None:
    """ "Return both backpacks" with one already returned: the quote is for one (xr-075)."""
    from assistant.return_tools import readback

    quote = {
        "lines": [
            {
                "quantity": 1,
                "product_title": "Commuter Laptop Backpack",
                "variant_name": "Charcoal",
                "refund_timing": "after_receipt",
            }
        ],
        "shipping_refund_minor": 0,
        "total_refund_minor": 7577,
        "refund_destination": None,
    }
    said = readback(quote, ["1 × Commuter Laptop Backpack"])
    assert said.startswith("1 × Commuter Laptop Backpack from this order was already returned. ")
    assert "Here's your return: 1 × Commuter Laptop Backpack (Charcoal)." in said
    assert readback(quote).startswith("Here's your return:")
