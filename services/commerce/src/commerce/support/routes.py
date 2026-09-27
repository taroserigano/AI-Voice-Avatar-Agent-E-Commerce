"""Support cases: a person takes over, with the conversation attached (returns regulations §7)."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce.activity.models import CustomerEvent, EventType
from commerce.api_model import ApiModel
from commerce.auth.deps import CurrentUser
from commerce.db import get_db, utcnow
from commerce.orders.models import Order
from commerce.support.models import CaseChannel, CaseStatus, SupportCase

router = APIRouter(prefix="/v1/support", tags=["support"])
DbDep = Annotated[Session, Depends(get_db)]


class CreateCase(ApiModel):
    subject: str = Field(min_length=3, max_length=200)
    summary: str = Field(min_length=3, max_length=4000)
    channel: Literal["chat", "voice", "email"] = "chat"
    order_id: uuid.UUID | None = None


class CaseOut(ApiModel):
    id: uuid.UUID
    reference: str
    subject: str
    status: CaseStatus
    channel: CaseChannel
    order_id: uuid.UUID | None
    opened_at: datetime
    reply_within: str = "1 business day"


def _out(c: SupportCase) -> CaseOut:
    return CaseOut(
        id=c.id,
        reference=c.reference,
        subject=c.subject,
        status=c.status,
        channel=c.channel,
        order_id=c.order_id,
        opened_at=c.opened_at,
    )


@router.post("/cases", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
def create_case(body: CreateCase, principal: CurrentUser, db: DbDep) -> CaseOut:
    """Open a case for a person to handle. The order, if given, must be the customer's own."""
    if (
        body.order_id is not None
        and db.scalar(
            select(Order.id).where(Order.id == body.order_id, Order.user_id == principal.id)
        )
        is None
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    now = utcnow()
    case = SupportCase(
        user_id=principal.id,
        order_id=body.order_id,
        reference=f"CS-{secrets.randbelow(900000) + 100000}",
        subject=body.subject,
        summary=body.summary,
        channel=CaseChannel(body.channel),
        status=CaseStatus.OPEN,
        opened_at=now,
    )
    db.add(case)
    db.add(
        CustomerEvent(
            user_id=principal.id,
            type=EventType.CONTACTED_SUPPORT,
            occurred_at=now,
            order_id=body.order_id,
            data={"reference": case.reference},
        )
    )
    db.commit()
    return _out(case)


@router.get("/cases", response_model=list[CaseOut])
def list_cases(principal: CurrentUser, db: DbDep) -> list[CaseOut]:
    rows = db.scalars(
        select(SupportCase)
        .where(SupportCase.user_id == principal.id)
        .order_by(SupportCase.opened_at.desc())
    )
    return [_out(c) for c in rows]
