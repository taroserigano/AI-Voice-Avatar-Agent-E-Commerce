from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce.activity.models import EventType
from commerce.activity.service import recent_events
from commerce.api_model import ApiModel
from commerce.auth.deps import CurrentUser
from commerce.catalog.models import Product
from commerce.db import get_db

router = APIRouter(prefix="/v1/activity", tags=["activity"])
DbDep = Annotated[Session, Depends(get_db)]


class ActivityProduct(ApiModel):
    id: uuid.UUID
    title: str
    image_path: str


class ActivityOut(ApiModel):
    id: uuid.UUID
    type: EventType
    occurred_at: datetime
    product: ActivityProduct | None
    order_id: uuid.UUID | None
    data: dict[str, Any]
    is_sample: bool = Field(description="Seeded demo activity; label it on screen")


@router.get("", response_model=list[ActivityOut])
def my_activity(
    principal: CurrentUser,
    db: DbDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    type: Annotated[list[EventType] | None, Query()] = None,
) -> list[ActivityOut]:
    """The signed-in shopper's own activity, newest first."""
    events = recent_events(db, principal.id, limit=limit, types=type)
    product_ids = {e.product_id for e in events if e.product_id}
    products = (
        {p.id: p for p in db.scalars(select(Product).where(Product.id.in_(product_ids)))}
        if product_ids
        else {}
    )
    out = []
    for e in events:
        product = products.get(e.product_id) if e.product_id else None
        out.append(
            ActivityOut(
                id=e.id,
                type=e.type,
                occurred_at=e.occurred_at,
                product=ActivityProduct(
                    id=product.id, title=product.title, image_path=product.image_path
                )
                if product
                else None,
                order_id=e.order_id,
                data=e.data,
                is_sample=e.is_sample,
            )
        )
    return out
