from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from commerce.activity.models import EventType
from commerce.activity.service import record
from commerce.auth.deps import CurrentUser
from commerce.auth.schemas import MessageOut
from commerce.db import get_db
from commerce.reviews import service
from commerce.reviews.schemas import ReviewIn, ReviewOut, ReviewPage, ReviewSort

router = APIRouter(prefix="/v1/products/{product_id}/reviews", tags=["reviews"])
DbDep = Annotated[Session, Depends(get_db)]
NOT_FOUND: dict[int | str, dict[str, Any]] = {
    404: {"model": MessageOut, "description": "No such product"}
}


def _not_found() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")


@router.get("", response_model=ReviewPage, responses=NOT_FOUND)
def list_reviews(
    product_id: uuid.UUID,
    principal: CurrentUser,
    db: DbDep,
    sort: ReviewSort = ReviewSort.NEWEST,
    page: Annotated[int, Query(ge=1, le=1000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 10,
) -> ReviewPage:
    try:
        return service.list_reviews(
            db, product_id, principal.id, sort=sort, page=page, page_size=page_size
        )
    except service.ProductNotFound:
        raise _not_found() from None


@router.put("/mine", response_model=ReviewOut, responses=NOT_FOUND)
def put_my_review(
    product_id: uuid.UUID,
    body: ReviewIn,
    principal: CurrentUser,
    db: DbDep,
    background: BackgroundTasks,
) -> ReviewOut:
    try:
        review = service.upsert_review(db, product_id, principal.id, body)
    except service.ProductNotFound:
        db.rollback()
        raise _not_found() from None
    background.add_task(
        record,
        principal.id,
        EventType.WROTE_REVIEW,
        product_id=product_id,
        data={"rating": review.rating},
    )
    return review


@router.delete("/mine", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_review(product_id: uuid.UUID, principal: CurrentUser, db: DbDep) -> Response:
    service.delete_review(db, product_id, principal.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
