from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce.activity.models import EventType
from commerce.activity.service import record
from commerce.auth.deps import CurrentUser
from commerce.auth.schemas import MessageOut
from commerce.cart import service
from commerce.cart.schemas import CartOut, SetCartItemRequest
from commerce.catalog.models import Variant
from commerce.db import get_db
from commerce.metrics import cart_adds, ownership_denials

router = APIRouter(prefix="/v1/cart", tags=["cart"])
DbDep = Annotated[Session, Depends(get_db)]


@router.get("", response_model=CartOut)
def get_cart(principal: CurrentUser, db: DbDep) -> CartOut:
    return service.cart_view(db, principal.id)


@router.put(
    "/items",
    response_model=CartOut,
    responses={404: {"model": MessageOut}, 409: {"model": MessageOut}},
)
def set_cart_item(
    body: SetCartItemRequest, principal: CurrentUser, db: DbDep, background: BackgroundTasks
) -> CartOut:
    try:
        service.set_item(db, principal.id, body.variant_id, body.quantity)
    except service.CartError as exc:
        db.rollback()
        raise HTTPException(exc.status_code, exc.message) from None
    if body.quantity > 0:
        cart_adds.add(1)
        product_id = db.scalar(select(Variant.product_id).where(Variant.id == body.variant_id))
        background.add_task(
            record,
            principal.id,
            EventType.ADDED_TO_CART,
            product_id=product_id,
            data={"variant_id": str(body.variant_id), "quantity": body.quantity},
        )
    return service.cart_view(db, principal.id)


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": MessageOut}},
)
def delete_cart_item(item_id: uuid.UUID, principal: CurrentUser, db: DbDep) -> Response:
    if not service.remove_item(db, principal.id, item_id):
        # Same answer whether the line doesn't exist or belongs to someone else.
        ownership_denials.add(1, {"resource": "cart_item"})
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cart item not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
