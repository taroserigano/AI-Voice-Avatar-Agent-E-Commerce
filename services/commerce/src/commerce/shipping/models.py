"""Outbound shipments and their tracking history.

Shipping is simulated until a carrier integration exists: carriers are fictional
("Larkspur Ground", "Swiftline Parcel") and the storefront labels tracking as simulated.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from commerce.db import Base, Timestamps, UUIDPk


class ShipmentStatus(enum.StrEnum):
    LABEL_CREATED = "label_created"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    EXCEPTION = "exception"


_status_enum = Enum(
    ShipmentStatus, name="shipment_status", values_callable=lambda e: [m.value for m in e]
)


class Shipment(UUIDPk, Timestamps, Base):
    __tablename__ = "shipments"

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )
    carrier: Mapped[str] = mapped_column(String(60))
    service: Mapped[str] = mapped_column(String(60))  # e.g. "Ground", "2-Day"
    tracking_number: Mapped[str] = mapped_column(String(60), unique=True)
    status: Mapped[ShipmentStatus] = mapped_column(_status_enum)
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    estimated_delivery_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    events: Mapped[list[ShipmentEvent]] = relationship(
        back_populates="shipment",
        order_by="ShipmentEvent.occurred_at",
        cascade="all, delete-orphan",
    )


class ShipmentEvent(UUIDPk, Base):
    """One tracking scan, e.g. "Departed facility, Dallas, TX"."""

    __tablename__ = "shipment_events"

    shipment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("shipments.id", ondelete="CASCADE"), index=True
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[ShipmentStatus] = mapped_column(_status_enum)
    description: Mapped[str] = mapped_column(String(200))
    location: Mapped[str | None] = mapped_column(String(120))

    shipment: Mapped[Shipment] = relationship(back_populates="events")
