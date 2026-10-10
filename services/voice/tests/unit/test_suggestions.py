"""Suggested questions on the voice screen: from the customer's own orders and what the last
answer covered, never one they've already asked (Taro, 2026-10-09)."""

from __future__ import annotations

from ai_commerce_voice.suggestions import SHOWN, Suggester, short_name

SNAPSHOT = [
    {
        "status": "In progress",
        "items": ["1 × Tempo Athletics Grip Yoga Mat, $34.99 each [carrier Swiftline Parcel]"],
    },
    {
        "status": "Delivered",
        "items": [
            "1 × Fernbrook Dairy Whole Milk, $3.99 each (refundable now only for a quality"
            " problem such as spoiled, damaged, or thawed, not a change of mind; nothing to"
            " send back)",
            "1 × Sonora Audio Pulse Wireless Earbuds, $79.99 each (returnable now, until"
            " Fri, Nov 6)",
        ],
    },
]


def test_an_item_reads_as_the_kind_of_thing_it_is() -> None:
    assert short_name(SNAPSHOT[0]["items"][0]) == "yoga mat"
    assert short_name("2 × Quillmark Quick-Dry Gel Pens, 12-Pack, $12.98 each") == "gel pens"
    assert short_name("not an item line") is None


def test_the_first_suggestions_come_from_the_customers_own_orders() -> None:
    first = Suggester(SNAPSHOT).initial()
    assert len(first) == SHOWN
    assert first[0] == "When's my yoga mat arriving?"
    # Milk is refunded only for a quality problem: not offered as a return.
    assert first[1] == "Can I return my wireless earbuds?"


def test_after_an_answer_the_follow_ups_fit_it_and_skip_what_was_asked() -> None:
    s = Suggester(SNAPSHOT)
    after_search = s.after("Do you have any oat milk?", ["search_products"])
    assert after_search[0] == "Which one is the cheapest?"
    assert "Do you have any oat milk?" not in after_search

    after_quote = s.after(
        "Can I return my wireless earbuds?", ["get_return_options", "propose_return"]
    )
    assert after_quote[:2] == ["Where can I drop it off?", "When will I get my refund?"]
    assert "Can I return my wireless earbuds?" not in after_quote


def test_without_orders_the_suggestions_are_general_and_change() -> None:
    s = Suggester(None)
    first = s.initial()
    second = s.after("hello", [])
    assert len(first) == len(second) == SHOWN
    assert first != second
