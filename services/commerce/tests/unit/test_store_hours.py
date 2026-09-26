from __future__ import annotations

from datetime import datetime, timedelta

from commerce.seed.stores import STORES
from commerce.stores.routes import is_open

HOURS = {"mon": ["07:00", "22:00"], "sun": ["08:00", "21:00"]}  # closed Tuesday-Saturday


def at(day: int, hhmm: str) -> datetime:
    """2026-09-28 is a Monday; ``day`` 0 = Monday."""
    h, m = map(int, hhmm.split(":"))
    return datetime(2026, 9, 28, h, m) + timedelta(days=day)


def test_open_from_opening_time_until_just_before_closing() -> None:
    assert not is_open(HOURS, at(0, "06:59"))
    assert is_open(HOURS, at(0, "07:00"))
    assert is_open(HOURS, at(0, "21:59"))
    assert not is_open(HOURS, at(0, "22:00"))


def test_days_without_hours_are_closed() -> None:
    assert not is_open(HOURS, at(1, "12:00"))
    assert is_open(HOURS, at(6, "08:30"))


def test_seeded_stores_have_sane_hours() -> None:
    assert len(STORES) == 10 and len({s.code for s in STORES}) == 10
    for s in STORES:
        for opens, closes in s.hours.values():
            assert "05:00" <= opens < closes <= "23:59", s.code
