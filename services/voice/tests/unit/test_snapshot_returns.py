"""The call-start orders snapshot says, per delivered item, what the returns engine allows.

Found by Xena's golden-set eval: from the delivery date alone, the voice model counted the days
itself and told a customer on day 29 of 30 that their tablet could no longer be returned.
"""

from __future__ import annotations

from ai_commerce_voice.brain import orders_snapshot

from .test_brain import order

TABLET = "11111111-1111-4111-8111-111111111111"


def test_each_delivered_item_carries_the_engines_answer() -> None:
    delivered = order("delivered")
    delivered["delivered_at"] = "2026-08-31T15:00:00Z"
    delivered["return_options"] = {
        "lines": [{"order_line_id": TABLET, "eligible": True, "reason": "within_window"}]
    }
    [snap] = orders_snapshot([delivered])
    assert snap["items"] == ["2 × Oat milk, 64 oz, $4.99 each (returnable now)"]

    delivered["return_options"]["lines"][0].update(eligible=False, reason="outside_window")
    [snap] = orders_snapshot([delivered])
    assert snap["items"] == ["2 × Oat milk, 64 oz, $4.99 each (not returnable: outside_window)"]


def test_an_order_without_return_options_says_nothing_about_returns() -> None:
    [snap] = orders_snapshot([order()])
    assert snap["items"] == ["2 × Oat milk, 64 oz, $4.99 each"]


def test_each_order_reads_items_first_with_its_own_carrier_and_tracking() -> None:
    """Found by the golden eval: with the items last, the voice model took carriers and dates
    from a neighbouring order. Each entry now starts with what was bought and holds that order's
    own delivery facts."""
    shipped = order("delivered")
    shipped["delivered_at"] = "2026-09-30T15:00:00Z"
    shipped["shipments"] = [
        {
            "status": "delivered",
            "carrier": "Serigan Mart Ground",
            "service": "Ground",
            "tracking_number": "LG686754189358",
            "delivered_at": "2026-09-30T15:00:00Z",
            "events": [],
        }
    ]
    [snap] = orders_snapshot([shipped])
    assert list(snap)[0] == "items"
    assert snap["carrier"] == "Serigan Mart Ground"
    assert snap["tracking_number"] == "LG686754189358"
    assert snap["delivered_on"] == "Wed, Sep 30"
    # And on the item's own line, so "tracking number for the oat milk?" needs no lookup.
    assert snap["items"][0].endswith("[carrier Serigan Mart Ground, tracking LG686754189358]")


def test_the_prompt_says_how_many_orders_there_are() -> None:
    from datetime import date

    from ai_commerce_voice.brain import system_prompt

    system = system_prompt(
        "Alice", date(2026, 10, 3), orders_snapshot([order(), order("delivered")])
    )
    assert '"order_count": 2' in system


def test_a_partly_returned_line_says_how_many_are_left_and_returns_say_where_they_stand() -> None:
    """Found by the golden eval: voice said both backpacks were returnable when one had been
    returned, and called an in-transit return "fully returned"."""
    d = order("delivered")
    d["return_options"] = {
        "lines": [
            {
                "order_line_id": d["lines"][0]["id"],
                "eligible": True,
                "reason": "within_window",
                "quantity": 2,
                "returned_quantity": 1,
                "returnable_quantity": 1,
            }
        ]
    }
    d["returns"] = [
        {
            "rma_number": "RMA-1",
            "status": "in_transit",
            "items": [{"quantity": 1, "product_title": "Oat milk"}],
            "refund": None,
        }
    ]
    [snap] = orders_snapshot([d])
    assert snap["items"] == [
        "2 × Oat milk, 64 oz, $4.99 each (returnable now: 1 of 2; 1 already returned)"
    ]
    assert snap["returns"] == [
        {
            "rma_number": "RMA-1",
            "status": "in transit",
            "items": ["1 × Oat milk"],
            "refund": "not issued yet",
        }
    ]


def test_fresh_food_is_refundable_only_for_a_quality_problem() -> None:
    """Found by the support set (2026-10-08): "I don't like the pizza, can I return it?" was
    told yes, because the snapshot said only "returnable now"."""
    d = order("delivered")
    d["return_options"] = {
        "lines": [
            {
                "order_line_id": d["lines"][0]["id"],
                "eligible": True,
                "reason": "perishable_within_7_days",
                "refund_timing": "no_return_needed",
            }
        ]
    }
    [snap] = orders_snapshot([d])
    assert "only for a quality problem" in snap["items"][0]
    assert "not a change of mind" in snap["items"][0]


def test_the_prompt_has_the_spending_total_worked_out() -> None:
    """Found by the support set: the voice model added up eleven totals and was off by $1."""
    from datetime import date

    from ai_commerce_voice.brain import system_prompt

    canceled = order("canceled")
    system = system_prompt(
        "Dana", date(2026, 10, 8), orders_snapshot([order(), order("delivered"), canceled])
    )
    one = orders_snapshot([order()])[0]["total"]
    cents = round(float(one.lstrip("$").replace(",", "")) * 100) * 2
    assert f'"total_spent_on_orders_not_canceled": "${cents // 100:,}.{cents % 100:02d}"' in system
    assert '"all_orders_listed": true' in system


def test_an_item_says_its_size_and_the_last_day_to_return_it() -> None:
    """Found by the support set (2026-10-08): size "M" was hidden because "m" is in "women's",
    and "how many days are left?" was answered from the voice model's own day count."""
    d = order("delivered")
    d["lines"][0].update(
        product_title="Women's High-Waisted Leggings, 25 in, Navy", variant_name="M"
    )
    d["return_window_ends_at"] = "2026-10-14T16:00:00+00:00"
    d["return_options"] = {
        "lines": [
            {"order_line_id": d["lines"][0]["id"], "eligible": True, "reason": "within_window"}
        ]
    }
    [snap] = orders_snapshot([d])
    assert "Leggings, 25 in, Navy, M," in snap["items"][0]
    assert "(returnable now, until Wed, Oct 14)" in snap["items"][0]
