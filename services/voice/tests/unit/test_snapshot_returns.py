"""The call-start orders snapshot says, per delivered item, what the returns engine allows.

Found by Xana's golden-set eval: from the delivery date alone, the voice model counted the days
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
    assert snap["items"] == ["2 × Oat milk (returnable now)"]

    delivered["return_options"]["lines"][0].update(eligible=False, reason="outside_window")
    [snap] = orders_snapshot([delivered])
    assert snap["items"] == ["2 × Oat milk (not returnable: outside_window)"]


def test_an_order_without_return_options_says_nothing_about_returns() -> None:
    [snap] = orders_snapshot([order()])
    assert snap["items"] == ["2 × Oat milk"]
