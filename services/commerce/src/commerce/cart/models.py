from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from commerce.catalog.models import Variant
from commerce.db import Base, Timestamps, UUIDPk, utcnow

MAX_LINE_QUANTITY = 10


class Cart(UUIDPk, Timestamps, Base):
    """One durable cart per signed-in customer. There are no guest carts."""

    __tablename__ = "carts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    # Bumped on every change, so a checkout quote can prove it priced this exact cart.
    version: Mapped[int] = mapped_column(Integer, default=1)

    items: Mapped[list[CartItem]] = relationship(
        back_populates="cart", cascade="all, delete-orphan", order_by="CartItem.added_at"
    )


class CartItem(UUIDPk, Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint("cart_id", "variant_id"),
        CheckConstraint(
            f"quantity > 0 AND quantity <= {MAX_LINE_QUANTITY}", name="quantity_in_range"
        ),
    )

    cart_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("carts.id", ondelete="CASCADE"), index=True
    )
    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("variants.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    cart: Mapped[Cart] = relationship(back_populates="items")
    variant: Mapped[Variant] = relationship()
