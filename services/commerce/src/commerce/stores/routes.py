"""Store locator: the Larkspur stores, their hours, and whether each is open right now."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce.api_model import ApiModel
from commerce.db import get_db, utcnow
from commerce.stores.models import STORE_TIMEZONE, Store

router = APIRouter(prefix="/v1/stores", tags=["stores"])
DbDep = Annotated[Session, Depends(get_db)]

DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


class DayHours(ApiModel):
    day: str = Field(description='"mon" through "sun"')
    opens: str | None = Field(description='"07:00" local time; null when closed')
    closes: str | None


class StoreOut(ApiModel):
    id: uuid.UUID
    code: str
    name: str
    address_line1: str
    city: str
    state: str
    postal_code: str
    latitude: float
    longitude: float
    phone: str
    timezone: str
    hours: list[DayHours]
    services: list[str]
    open_now: bool = Field(description="Whether the store is open at the time of the request")
    today_hours: DayHours


def is_open(hours: dict[str, list[str]], at: datetime) -> bool:
    """``at`` is local store time. Closing times are exclusive; no store is open past midnight."""
    window = hours.get(DAYS[at.weekday()])
    if not window:
        return False
    return window[0] <= at.strftime("%H:%M") < window[1]


def _day(hours: dict[str, list[str]], day: str) -> DayHours:
    window = hours.get(day)
    return DayHours(
        day=day, opens=window[0] if window else None, closes=window[1] if window else None
    )


def store_out(s: Store, now_local: datetime) -> StoreOut:
    return StoreOut(
        id=s.id,
        code=s.code,
        name=s.name,
        address_line1=s.address_line1,
        city=s.city,
        state=s.state,
        postal_code=s.postal_code,
        latitude=s.latitude,
        longitude=s.longitude,
        phone=s.phone,
        timezone=STORE_TIMEZONE,
        hours=[_day(s.hours, d) for d in DAYS],
        services=list(s.services),
        open_now=is_open(s.hours, now_local),
        today_hours=_day(s.hours, DAYS[now_local.weekday()]),
    )


@router.get("", response_model=list[StoreOut])
def list_stores(db: DbDep) -> list[StoreOut]:
    now_local = utcnow().astimezone(ZoneInfo(STORE_TIMEZONE))
    stores = db.scalars(select(Store).where(Store.is_active.is_(True)).order_by(Store.sort_order))
    return [store_out(s, now_local) for s in stores]
