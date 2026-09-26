"""The shopper's own activity timeline: what they viewed, searched, bought, and returned.

Append-only. It powers "recently viewed" and gives the assistant context such as "the
headphones from last week". It stays in PostgreSQL: telemetry only ever sees the hashed
customer ID, never these rows.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from commerce.db import Base, UUIDPk


class EventType(enum.StrEnum):
    SIGNED_IN = "signed_in"
    SEARCHED = "searched"
    VIEWED_PRODUCT = "viewed_product"
    ADDED_TO_CART = "added_to_cart"
    PLACED_ORDER = "placed_order"
    ORDER_DELIVERED = "order_delivered"
    STARTED_RETURN = "started_return"
    REFUND_ISSUED = "refund_issued"
    WROTE_REVIEW = "wrote_review"
    CONTACTED_SUPPORT = "contacted_support"


class CustomerEvent(UUIDPk, Base):
    __tablename__ = "customer_events"
    __table_args__ = (Index("ix_customer_events_user_time", "user_id", "occurred_at"),)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    type: Mapped[EventType] = mapped_column(
        Enum(EventType, name="customer_event_type", values_callable=lambda e: [m.value for m in e])
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL")
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("orders.id", ondelete="SET NULL"))
    # Small typed details, e.g. {"query": "rain boots"} or {"quantity": 2}.
    data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
