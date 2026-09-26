"""How each order was paid. Refunds always go back to this payment ("original payment method").

We never store card numbers: only the brand and last four digits the provider reports.
Milestone 2 fills these from Stripe; development seed data uses the ``simulated`` provider,
and the storefront labels those payments as simulated.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from commerce.db import Base, Timestamps, UUIDPk


class PaymentProvider(enum.StrEnum):
    STRIPE = "stripe"
    SIMULATED = "simulated"  # development seed data and early tests only


class PaymentStatus(enum.StrEnum):
    SUCCEEDED = "succeeded"
    PARTIALLY_REFUNDED = "partially_refunded"
    REFUNDED = "refunded"
    FAILED = "failed"


class PaymentAttempt(UUIDPk, Timestamps, Base):
    __tablename__ = "payment_attempts"
    __table_args__ = (
        CheckConstraint("amount_minor >= 0", name="amount_non_negative"),
        CheckConstraint(
            "refunded_minor >= 0 AND refunded_minor <= amount_minor", name="refunded_within_amount"
        ),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[PaymentProvider] = mapped_column(
        Enum(
            PaymentProvider, name="payment_provider", values_callable=lambda e: [m.value for m in e]
        )
    )
    # e.g. Stripe's PaymentIntent ID; "sim_pi_…" for simulated payments.
    provider_payment_id: Mapped[str] = mapped_column(String(120), unique=True)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status", values_callable=lambda e: [m.value for m in e])
    )
    amount_minor: Mapped[int] = mapped_column(Integer)
    refunded_minor: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    card_brand: Mapped[str | None] = mapped_column(String(20))  # "visa", "mastercard", …
    card_last4: Mapped[str | None] = mapped_column(String(4))
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
