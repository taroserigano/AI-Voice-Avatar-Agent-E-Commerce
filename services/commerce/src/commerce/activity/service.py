"""Record and read the shopper's activity timeline."""

from __future__ import annotations

import logging
import uuid
from datetime import timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce.activity.models import CustomerEvent, EventType
from commerce.db import get_sessionmaker, utcnow

log = logging.getLogger(__name__)

# Viewing the same product again within this long is one visit, not a new event.
VIEW_DEDUPE = timedelta(minutes=30)


def record(
    user_id: uuid.UUID,
    type: EventType,
    *,
    product_id: uuid.UUID | None = None,
    order_id: uuid.UUID | None = None,
    data: dict[str, Any] | None = None,
) -> None:
    """Append one event in its own short transaction. Best effort: a failure here is logged
    and never breaks the page or action that caused it."""
    try:
        with get_sessionmaker()() as db:
            now = utcnow()
            if type == EventType.VIEWED_PRODUCT and product_id is not None:
                recent = db.scalar(
                    select(CustomerEvent.id)
                    .where(
                        CustomerEvent.user_id == user_id,
                        CustomerEvent.type == EventType.VIEWED_PRODUCT,
                        CustomerEvent.product_id == product_id,
                        CustomerEvent.occurred_at > now - VIEW_DEDUPE,
                    )
                    .limit(1)
                )
                if recent is not None:
                    return
            db.add(
                CustomerEvent(
                    user_id=user_id,
                    type=type,
                    occurred_at=now,
                    product_id=product_id,
                    order_id=order_id,
                    data=data or {},
                )
            )
            db.commit()
    except Exception:  # noqa: BLE001 - activity is a nice-to-have, never a blocker
        log.warning("couldn't record %s activity", type.value, exc_info=True)


def recent_events(
    db: Session, user_id: uuid.UUID, *, limit: int, types: list[EventType] | None = None
) -> list[CustomerEvent]:
    stmt = select(CustomerEvent).where(CustomerEvent.user_id == user_id)
    if types:
        stmt = stmt.where(CustomerEvent.type.in_(types))
    return list(db.scalars(stmt.order_by(CustomerEvent.occurred_at.desc()).limit(limit)))
