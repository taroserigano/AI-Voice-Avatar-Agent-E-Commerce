"""Product ratings and reviews. One review per shopper per product; the shopper can edit it."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from commerce.auth.models import User
from commerce.db import Base, Timestamps, UUIDPk


class Review(UUIDPk, Timestamps, Base):
    __tablename__ = "product_reviews"
    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="rating_range"),
        # Also the lookup index for a product's reviews (product_id leads).
        Index("uq_product_reviews_product_user", "product_id", "user_id", unique=True),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    rating: Mapped[int] = mapped_column(Integer)
    title: Mapped[str | None] = mapped_column(String(120))
    body: Mapped[str | None] = mapped_column(Text)
    # Seeded demo content, labeled as such on screen. Never set from the API.
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    user: Mapped[User] = relationship()
