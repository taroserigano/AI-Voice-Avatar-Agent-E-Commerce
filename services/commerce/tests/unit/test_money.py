from __future__ import annotations

import pytest

from commerce.money import line_total, split_evenly


def test_policy_example_discount_split() -> None:
    # PRODUCT_REQUIREMENTS.md: a $10.00 discount over 3 units is 333, 333, 334 cents.
    assert split_evenly(1000, 3) == [333, 333, 334]


@pytest.mark.parametrize("total", [0, 1, 2, 99, 100, 1000, 12999, 1_000_001])
@pytest.mark.parametrize("parts", [1, 2, 3, 7, 10])
def test_shares_always_add_up_exactly_and_last_takes_remainder(total: int, parts: int) -> None:
    shares = split_evenly(total, parts)
    assert sum(shares) == total
    assert len(shares) == parts
    assert all(s == shares[0] for s in shares[:-1])
    assert 0 <= shares[-1] - shares[0] < parts


def test_invalid_inputs_are_rejected() -> None:
    with pytest.raises(ValueError):
        split_evenly(100, 0)
    with pytest.raises(ValueError):
        line_total(-1, 2)
    with pytest.raises(ValueError):
        line_total(100, -2)


def test_line_total_is_exact_integer_math() -> None:
    assert line_total(1999, 3) == 5997
