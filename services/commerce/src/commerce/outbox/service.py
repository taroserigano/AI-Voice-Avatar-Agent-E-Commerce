from __future__ import annotations

from typing import Any

from opentelemetry.propagate import inject
from sqlalchemy.orm import Session

from commerce.outbox.models import OutboxEvent

PRODUCT_UPSERTED = "product.upserted"
PRODUCT_DELETED = "product.deleted"


def emit(db: Session, topic: str, aggregate_id: str, payload: dict[str, Any] | None = None) -> None:
    """Add an outbox event to the caller's transaction. It commits with the business change."""
    carrier: dict[str, str] = {}
    inject(carrier)  # the current W3C trace context, so the publisher joins this trace
    db.add(
        OutboxEvent(
            topic=topic, aggregate_id=aggregate_id, payload=payload or {}, trace_context=carrier
        )
    )
