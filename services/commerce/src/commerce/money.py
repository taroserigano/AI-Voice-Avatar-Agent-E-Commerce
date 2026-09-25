"""Money is always an integer count of minor units (cents) plus an ISO 4217 currency code."""

from __future__ import annotations

from pydantic import BaseModel, Field

DEFAULT_CURRENCY = "USD"


class Money(BaseModel):
    amount_minor: int = Field(description="Integer minor units, e.g. cents")
    currency: str = Field(default=DEFAULT_CURRENCY, min_length=3, max_length=3)


def line_total(unit_price_minor: int, quantity: int) -> int:
    if quantity < 0 or unit_price_minor < 0:
        raise ValueError("amounts and quantities must be non-negative")
    return unit_price_minor * quantity


def split_evenly(total_minor: int, parts: int) -> list[int]:
    """Split ``total_minor`` into ``parts`` integer shares; the last share takes the remainder.

    Used by the sandbox return policy: a 1000-cent discount over 3 units is [333, 333, 334].
    The shares always add up to exactly ``total_minor``.
    """
    if parts <= 0:
        raise ValueError("parts must be positive")
    base, remainder = divmod(total_minor, parts)
    return [base] * (parts - 1) + [base + remainder]
