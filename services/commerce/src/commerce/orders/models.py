"""Order records. Orders are created only from verified payment evidence (Milestone 2).

Milestone 1 ships the tables and the owner-scoped read API so ownership rules are proven early.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from commerce.db import Base, Timestamps, UUIDPk


class OrderStatus(enum.StrEnum):
    PAID = "paid"
    FULFILLING = "fulfilling"
    DELIVERED = "delivered"
    CANCELED = "canceled"


class Order(UUIDPk, Timestamps, Base):
    __tablename__ = "orders"
    __table_args__ = (CheckConstraint("total_minor >= 0", name="total_non_negative"),)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status", values_callable=lambda e: [m.value for m in e])
    )
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    subtotal_minor: Mapped[int] = mapped_column(Integer)
    discount_minor: Mapped[int] = mapped_column(Integer, default=0)
    tax_minor: Mapped[int] = mapped_column(Integer, default=0)
    shipping_minor: Mapped[int] = mapped_column(Integer, default=0)
    total_minor: Mapped[int] = mapped_column(Integer)
    placed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Where it was sent, snapshotted when the order was placed (a later address-book edit
    # doesn't rewrite history). All null when there's no delivery address on file.
    ship_to_name: Mapped[str | None] = mapped_column(String(120))
    ship_to_line1: Mapped[str | None] = mapped_column(String(200))
    ship_to_line2: Mapped[str | None] = mapped_column(String(200))
    ship_to_city: Mapped[str | None] = mapped_column(String(100))
    ship_to_state: Mapped[str | None] = mapped_column(String(40))
    ship_to_postal_code: Mapped[str | None] = mapped_column(String(20))
    ship_to_country: Mapped[str | None] = mapped_column(String(2))
    # Seeded demo address (development accounts only); the storefront labels it as a sample.
    ship_to_is_sample: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    lines: Mapped[list[OrderLine]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderLine(UUIDPk, Base):
    """Purchase-time snapshot: price, discount, tax, and policy reference as charged."""

    __tablename__ = "order_lines"
    __table_args__ = (CheckConstraint("quantity > 0", name="quantity_positive"),)

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )
    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("variants.id"))
    product_title: Mapped[str] = mapped_column(String(200))
    variant_name: Mapped[str] = mapped_column(String(120))
    sku: Mapped[str] = mapped_column(String(64))
    image_path: Mapped[str] = mapped_column(String(300))
    policy_class: Mapped[str] = mapped_column(String(32))
    policy_version: Mapped[str | None] = mapped_column(String(64))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price_minor: Mapped[int] = mapped_column(Integer)
    amount_discount_minor: Mapped[int] = mapped_column(Integer, default=0)
    amount_tax_minor: Mapped[int] = mapped_column(Integer, default=0)
    amount_total_minor: Mapped[int] = mapped_column(Integer)

    order: Mapped[Order] = relationship(back_populates="lines")
