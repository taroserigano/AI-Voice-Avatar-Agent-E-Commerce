"""Return and refund records (TECHNICAL_SPEC.md, "State and retries").

A return and its refund are tracked separately: the return follows the package, the refund
follows the payment provider. States name what was actually observed, never a guess.
Quotes and confirmation tokens (Milestone 3a) build on these tables.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from commerce.db import Base, Timestamps, UUIDPk, utcnow


class PolicyVersion(UUIDPk, Base):
    """A saved version of the return policy. Order lines keep the version they were sold under."""

    __tablename__ = "policy_versions"

    version: Mapped[str] = mapped_column(String(64), unique=True)
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    rules: Mapped[dict[str, Any]] = mapped_column(JSON)
    summary: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ReturnStatus(enum.StrEnum):
    REQUESTED = "requested"
    AUTHORIZED = "authorized"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    INSPECTED = "inspected"
    CLOSED = "closed"
    REVIEW = "review"
    REJECTED = "rejected"
    CANCELED = "canceled"


# Returns in these states don't count against what's left to return on a line.
INACTIVE_RETURN_STATES = frozenset({ReturnStatus.REJECTED, ReturnStatus.CANCELED})


class RefundStatus(enum.StrEnum):
    NOT_REQUESTED = "not_requested"
    REQUESTED = "requested"
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REQUIRES_ACTION = "requires_action"
    CANCELED = "canceled"


class ReturnRequest(UUIDPk, Timestamps, Base):
    __tablename__ = "return_requests"
    __table_args__ = (
        CheckConstraint("shipping_refund_minor >= 0", name="shipping_refund_non_negative"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), index=True)
    # Unique business-operation key: a repeated confirm finds this row instead of a new one.
    operation_key: Mapped[str] = mapped_column(String(120), unique=True)
    rma_number: Mapped[str] = mapped_column(String(32), unique=True)  # shown to the shopper
    status: Mapped[ReturnStatus] = mapped_column(
        Enum(ReturnStatus, name="return_status", values_callable=lambda e: [m.value for m in e])
    )
    policy_version: Mapped[str] = mapped_column(String(64))
    reason: Mapped[str] = mapped_column(String(60))  # e.g. "doesnt_fit", "damaged"
    note: Mapped[str | None] = mapped_column(Text)
    shipping_refund_minor: Mapped[int] = mapped_column(Integer, default=0)
    return_tracking_number: Mapped[str | None] = mapped_column(String(60))
    authorized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    inspected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Seeded demo history, labeled on screen. Never set by the API.
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    items: Mapped[list[ReturnItem]] = relationship(
        back_populates="return_request", cascade="all, delete-orphan"
    )
    refunds: Mapped[list[RefundAttempt]] = relationship(
        back_populates="return_request",
        order_by="RefundAttempt.requested_at",
        cascade="all, delete-orphan",
    )


class ReturnItem(UUIDPk, Base):
    __tablename__ = "return_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("refund_minor >= 0", name="refund_non_negative"),
    )

    return_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("return_requests.id", ondelete="CASCADE"), index=True
    )
    order_line_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("order_lines.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    refund_minor: Mapped[int] = mapped_column(Integer)  # computed by commerce.returns.policy
    condition: Mapped[str] = mapped_column(String(40))  # "unopened", "like_new", "damaged", …

    return_request: Mapped[ReturnRequest] = relationship(back_populates="items")


class RefundAttempt(UUIDPk, Timestamps, Base):
    """One refund call to the payment provider. Always to the order's original payment."""

    __tablename__ = "refund_attempts"
    __table_args__ = (CheckConstraint("amount_minor > 0", name="amount_positive"),)

    return_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("return_requests.id", ondelete="CASCADE"), index=True
    )
    payment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payment_attempts.id"), index=True)
    # Deterministic operation ID sent to the provider as its idempotency key.
    operation_id: Mapped[str] = mapped_column(String(120), unique=True)
    status: Mapped[RefundStatus] = mapped_column(
        Enum(RefundStatus, name="refund_status", values_callable=lambda e: [m.value for m in e])
    )
    amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    provider_refund_id: Mapped[str | None] = mapped_column(String(120))
    failure_reason: Mapped[str | None] = mapped_column(String(200))
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    return_request: Mapped[ReturnRequest] = relationship(back_populates="refunds")
