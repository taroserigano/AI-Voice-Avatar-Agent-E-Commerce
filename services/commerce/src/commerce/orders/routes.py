from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from commerce.api_model import ApiModel
from commerce.auth.deps import CurrentUser
from commerce.db import get_db
from commerce.metrics import ownership_denials
from commerce.orders.models import Order, OrderStatus

router = APIRouter(prefix="/v1/orders", tags=["orders"])
DbDep = Annotated[Session, Depends(get_db)]


class OrderLineOut(ApiModel):
    id: uuid.UUID
    variant_id: uuid.UUID
    product_title: str
    variant_name: str
    sku: str
    image_path: str
    quantity: int
    unit_price_minor: int
    amount_discount_minor: int
    amount_tax_minor: int
    amount_total_minor: int


class OrderSummary(ApiModel):
    id: uuid.UUID
    status: OrderStatus
    currency: str
    total_minor: int
    item_count: int
    placed_at: datetime


class OrderDetail(OrderSummary):
    subtotal_minor: int
    discount_minor: int
    tax_minor: int
    shipping_minor: int
    delivered_at: datetime | None
    lines: list[OrderLineOut]


def _summary(o: Order) -> OrderSummary:
    return OrderSummary(
        id=o.id,
        status=o.status,
        currency=o.currency,
        total_minor=o.total_minor,
        item_count=sum(line.quantity for line in o.lines),
        placed_at=o.placed_at,
    )


@router.get("", response_model=list[OrderSummary])
def list_orders(principal: CurrentUser, db: DbDep) -> list[OrderSummary]:
    orders = db.scalars(
        select(Order)
        .options(selectinload(Order.lines))
        .where(Order.user_id == principal.id)
        .order_by(Order.placed_at.desc())
    )
    return [_summary(o) for o in orders]


@router.get(
    "/{order_id}", response_model=OrderDetail, responses={404: {"description": "Not found"}}
)
def get_order(order_id: uuid.UUID, principal: CurrentUser, db: DbDep) -> OrderDetail:
    order = db.scalar(
        select(Order)
        .options(selectinload(Order.lines))
        .where(Order.id == order_id, Order.user_id == principal.id)
    )
    if order is None:
        # 404, not 403: don't confirm that someone else's order exists.
        ownership_denials.add(1, {"resource": "order"})
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    return OrderDetail(
        **_summary(order).model_dump(),
        subtotal_minor=order.subtotal_minor,
        discount_minor=order.discount_minor,
        tax_minor=order.tax_minor,
        shipping_minor=order.shipping_minor,
        delivered_at=order.delivered_at,
        lines=[
            OrderLineOut(
                id=line.id,
                variant_id=line.variant_id,
                product_title=line.product_title,
                variant_name=line.variant_name,
                sku=line.sku,
                image_path=line.image_path,
                quantity=line.quantity,
                unit_price_minor=line.unit_price_minor,
                amount_discount_minor=line.amount_discount_minor,
                amount_tax_minor=line.amount_tax_minor,
                amount_total_minor=line.amount_total_minor,
            )
            for line in order.lines
        ],
    )
