"""Store locations for the store locator. Online orders still ship from one warehouse."""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from commerce.db import Base, UUIDPk

STORE_TIMEZONE = "America/Chicago"  # every store is in the Dallas-Fort Worth area


class Store(UUIDPk, Base):
    __tablename__ = "stores"

    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    address_line1: Mapped[str] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(80))
    state: Mapped[str] = mapped_column(String(2))
    postal_code: Mapped[str] = mapped_column(String(10))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    phone: Mapped[str] = mapped_column(String(20))
    # {"mon": ["07:00", "22:00"], ...} in STORE_TIMEZONE; a missing day means closed.
    hours: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    services: Mapped[list[str]] = mapped_column(JSON, default=list)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
