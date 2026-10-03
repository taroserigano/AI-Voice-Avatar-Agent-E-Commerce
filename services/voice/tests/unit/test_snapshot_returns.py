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
    assert snap["items"] == ["2 × Oat milk, 64 oz (returnable now)"]

    delivered["return_options"]["lines"][0].update(eligible=False, reason="outside_window")
    [snap] = orders_snapshot([delivered])
    assert snap["items"] == ["2 × Oat milk, 64 oz (not returnable: outside_window)"]


def test_an_order_without_return_options_says_nothing_about_returns() -> None:
    [snap] = orders_snapshot([order()])
    assert snap["items"] == ["2 × Oat milk, 64 oz"]


def test_each_order_reads_items_first_with_its_own_carrier_and_tracking() -> None:
    """Found by the golden eval: with the items last, the voice model took carriers and dates
    from a neighbouring order. Each entry now starts with what was bought and holds that order's
    own delivery facts."""
    shipped = order("delivered")
    shipped["delivered_at"] = "2026-09-30T15:00:00Z"
    shipped["shipments"] = [{"status": "delivered", "carrier": "Serigan Mart Ground", "service": "Ground",
                             "tracking_number": "LG686754189358", "delivered_at": "2026-09-30T15:00:00Z",
                             "events": []}]  # fmt: skip
    [snap] = orders_snapshot([shipped])
    assert list(snap)[0] == "items"
    assert snap["carrier"] == "Serigan Mart Ground"
    assert snap["tracking_number"] == "LG686754189358"
    assert snap["delivered_on"] == "Sep 30"


def test_the_prompt_says_how_many_orders_there_are() -> None:
    from datetime import date

    from ai_commerce_voice.brain import system_prompt

    system = system_prompt("Alice", date(2026, 10, 3), orders_snapshot([order(), order("delivered")]))
    assert '"order_count": 2' in system
