"""Support cases: conversations that need a person, or a record of help already given."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from commerce.db import Base, Timestamps, UUIDPk


class CaseStatus(enum.StrEnum):
    OPEN = "open"
    WAITING_ON_CUSTOMER = "waiting_on_customer"
    RESOLVED = "resolved"


class CaseChannel(enum.StrEnum):
    CHAT = "chat"
    VOICE = "voice"
    EMAIL = "email"


class SupportCase(UUIDPk, Timestamps, Base):
    __tablename__ = "support_cases"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    order_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("orders.id"), index=True)
    reference: Mapped[str] = mapped_column(String(32), unique=True)  # e.g. "CS-4821"
    subject: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(Text)
    channel: Mapped[CaseChannel] = mapped_column(
        Enum(CaseChannel, name="case_channel", values_callable=lambda e: [m.value for m in e])
    )
    status: Mapped[CaseStatus] = mapped_column(
        Enum(CaseStatus, name="case_status", values_callable=lambda e: [m.value for m in e])
    )
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
