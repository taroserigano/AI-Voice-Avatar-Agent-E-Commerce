from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from commerce.api_model import ApiModel
from commerce.auth.deps import CurrentUser
from commerce.catalog.models import Variant
from commerce.db import get_db, utcnow
from commerce.metrics import ownership_denials
from commerce.orders.models import Order, OrderStatus
from commerce.returns import service as returns
from commerce.returns.schemas import PaymentOut, ReturnOptions, ReturnOut, ShipmentOut

router = APIRouter(prefix="/v1/orders", tags=["orders"])
DbDep = Annotated[Session, Depends(get_db)]


class OrderLineOut(ApiModel):
    id: uuid.UUID
    variant_id: uuid.UUID
    product_id: uuid.UUID | None = Field(
        default=None, description="For linking to the product and buying it again"
    )
    product_title: str
    variant_name: str
    sku: str
    image_path: str
    quantity: int
    unit_price_minor: int
    amount_subtotal_minor: int = Field(
        description="Unit price times quantity, before discount and tax (the receipt's line amount)"
    )
    amount_discount_minor: int
    amount_tax_minor: int
    amount_total_minor: int


class ShippingAddressOut(ApiModel):
    """Where the order was sent, as recorded when it was placed."""

    name: str
    line1: str
    line2: str | None
    city: str
    state: str
    postal_code: str
    country: str = Field(description='ISO 3166-1 alpha-2, e.g. "US"')
    is_sample: bool = Field(description="Seeded demo address; label it as a sample on screen")


class OrderSummary(ApiModel):
    id: uuid.UUID
    status: OrderStatus
    currency: str
    total_minor: int
    item_count: int
    placed_at: datetime
    delivered_at: datetime | None
    preview_images: list[str] = Field(description="Up to 4 line images, for the order list")
    item_titles: list[str] = Field(
        description="Every line's product title, so the order list can be searched by item"
    )
    estimated_delivery_at: datetime | None = Field(description="While it's still on its way")
    return_window_ends_at: datetime | None = Field(
        description="Latest time any item can still be returned; null if nothing can be"
    )
    has_open_return: bool = Field(description="A return for this order is still in progress")


class OrderDetail(OrderSummary):
    subtotal_minor: int
    discount_minor: int
    tax_minor: int
    shipping_minor: int
    shipping_address: ShippingAddressOut | None = Field(
        description="Null when no delivery address was recorded"
    )
    lines: list[OrderLineOut]
    payment: PaymentOut | None
    shipments: list[ShipmentOut]
    returns: list[ReturnOut]


def _summary(
    o: Order,
    *,
    estimated_delivery_at: datetime | None = None,
    return_window_ends_at: datetime | None = None,
    has_open_return: bool = False,
) -> OrderSummary:
    return OrderSummary(
        id=o.id,
        status=o.status,
        currency=o.currency,
        total_minor=o.total_minor,
        item_count=sum(line.quantity for line in o.lines),
        placed_at=o.placed_at,
        delivered_at=o.delivered_at,
        preview_images=[line.image_path for line in o.lines[:4]],
        item_titles=[line.product_title for line in o.lines],
        estimated_delivery_at=estimated_delivery_at,
        return_window_ends_at=return_window_ends_at,
        has_open_return=has_open_return,
    )


@router.get("", response_model=list[OrderSummary])
def list_orders(principal: CurrentUser, db: DbDep) -> list[OrderSummary]:
    orders = list(
        db.scalars(
            select(Order)
            .options(selectinload(Order.lines))
            .where(Order.user_id == principal.id)
            .order_by(Order.placed_at.desc())
        )
    )
    ids = [o.id for o in orders]
    open_returns = returns.orders_with_open_returns(db, ids)
    arriving = returns.estimated_deliveries(db, ids)
    now = utcnow()
    return [
        _summary(
            o,
            estimated_delivery_at=arriving.get(o.id),
            return_window_ends_at=returns.return_window_ends_at(db, o, now),
            has_open_return=o.id in open_returns,
        )
        for o in orders
    ]


def _shipping_address(o: Order) -> ShippingAddressOut | None:
    if not (o.ship_to_name and o.ship_to_line1 and o.ship_to_city and o.ship_to_postal_code):
        return None
    return ShippingAddressOut(
        name=o.ship_to_name,
        line1=o.ship_to_line1,
        line2=o.ship_to_line2,
        city=o.ship_to_city,
        state=o.ship_to_state or "",
        postal_code=o.ship_to_postal_code,
        country=o.ship_to_country or "US",
        is_sample=o.ship_to_is_sample,
    )


def _own_order(db: Session, order_id: uuid.UUID, user_id: uuid.UUID) -> Order:
    order = db.scalar(
        select(Order)
        .options(selectinload(Order.lines))
        .where(Order.id == order_id, Order.user_id == user_id)
    )
    if order is None:
        # 404, not 403: don't confirm that someone else's order exists.
        ownership_denials.add(1, {"resource": "order"})
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    return order


@router.get(
    "/{order_id}", response_model=OrderDetail, responses={404: {"description": "Not found"}}
)
def get_order(order_id: uuid.UUID, principal: CurrentUser, db: DbDep) -> OrderDetail:
    order = _own_order(db, order_id, principal.id)
    now = utcnow()
    summary = _summary(
        order,
        estimated_delivery_at=returns.estimated_deliveries(db, [order.id]).get(order.id),
        return_window_ends_at=returns.return_window_ends_at(db, order, now),
        has_open_return=bool(returns.orders_with_open_returns(db, [order.id])),
    )
    variant_ids = [line.variant_id for line in order.lines]
    product_of: dict[uuid.UUID, uuid.UUID] = {
        vid: pid
        for vid, pid in db.execute(
            select(Variant.id, Variant.product_id).where(Variant.id.in_(variant_ids))
        ).all()
    }
    return OrderDetail(
        **summary.model_dump(),
        subtotal_minor=order.subtotal_minor,
        discount_minor=order.discount_minor,
        tax_minor=order.tax_minor,
        shipping_minor=order.shipping_minor,
        shipping_address=_shipping_address(order),
        payment=returns.order_payment(db, order.id),
        shipments=returns.order_shipments(db, order.id),
        returns=returns.order_returns(db, order),
        lines=[
            OrderLineOut(
                id=line.id,
                variant_id=line.variant_id,
                product_id=product_of.get(line.variant_id),
                product_title=line.product_title,
                variant_name=line.variant_name,
                sku=line.sku,
                image_path=line.image_path,
                quantity=line.quantity,
                unit_price_minor=line.unit_price_minor,
                amount_subtotal_minor=line.unit_price_minor * line.quantity,
                amount_discount_minor=line.amount_discount_minor,
                amount_tax_minor=line.amount_tax_minor,
                amount_total_minor=line.amount_total_minor,
            )
            for line in order.lines
        ],
    )


@router.get(
    "/{order_id}/return-options",
    response_model=ReturnOptions,
    responses={404: {"description": "Not found"}},
)
def get_return_options(order_id: uuid.UUID, principal: CurrentUser, db: DbDep) -> ReturnOptions:
    """What each line of the order can return right now, and roughly for how much. Read-only:
    starting a return needs a quote and the shopper's confirmation (Milestone 3a)."""
    return returns.return_options(db, _own_order(db, order_id, principal.id))
