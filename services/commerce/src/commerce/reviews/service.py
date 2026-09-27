"""Review reads and writes. The author is always the signed-in shopper, never the request body."""

from __future__ import annotations

import uuid
from collections.abc import Iterable

from sqlalchemy import Subquery, delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, selectinload

from commerce.catalog.models import Product, Variant
from commerce.db import utcnow
from commerce.orders.models import Order, OrderLine, OrderStatus
from commerce.reviews.models import Review
from commerce.reviews.schemas import (
    RatingBucket,
    RatingSummary,
    ReviewIn,
    ReviewOut,
    ReviewPage,
    ReviewSort,
)

_PURCHASED = (OrderStatus.PAID, OrderStatus.FULFILLING, OrderStatus.DELIVERED)


class ProductNotFound(Exception):
    pass


def rating_stats_subquery() -> Subquery:
    """Per product: mean rating and review count, for joining into catalog reads."""
    return (
        select(
            Review.product_id.label("product_id"),
            func.avg(Review.rating).label("rating_avg"),
            func.count(Review.id).label("rating_count"),
        )
        .group_by(Review.product_id)
        .subquery()
    )


def round_average(value: object) -> float | None:
    return None if value is None else round(float(value), 1)  # type: ignore[arg-type]


def author_name(display_name: str) -> str:
    """ "Alice Rivera" -> "Alice R."; shows enough to feel human without a full name."""
    parts = display_name.split()
    if not parts:
        return "Serigan Mart shopper"
    if len(parts) == 1:
        return parts[0]
    return f"{parts[0]} {parts[-1][0].upper()}."


def _product_exists(db: Session, product_id: uuid.UUID) -> bool:
    return (
        db.scalar(select(Product.id).where(Product.id == product_id, Product.is_active.is_(True)))
        is not None
    )


def _purchasers(
    db: Session, product_id: uuid.UUID, user_ids: Iterable[uuid.UUID]
) -> set[uuid.UUID]:
    ids = set(user_ids)
    if not ids:
        return set()
    rows = db.scalars(
        select(Order.user_id)
        .join(OrderLine, OrderLine.order_id == Order.id)
        .join(Variant, Variant.id == OrderLine.variant_id)
        .where(
            Variant.product_id == product_id,
            Order.user_id.in_(ids),
            Order.status.in_(_PURCHASED),
        )
        .distinct()
    )
    return set(rows)


def _out(review: Review, viewer_id: uuid.UUID, purchasers: set[uuid.UUID]) -> ReviewOut:
    return ReviewOut(
        id=review.id,
        rating=review.rating,
        title=review.title,
        body=review.body,
        author_name=author_name(review.user.display_name),
        created_at=review.created_at,
        updated_at=review.updated_at,
        is_mine=review.user_id == viewer_id,
        verified_purchase=review.user_id in purchasers,
        is_sample=review.is_sample,
    )


def summary(db: Session, product_id: uuid.UUID) -> RatingSummary:
    counts: dict[int, int] = {
        int(stars): int(n)
        for stars, n in db.execute(
            select(Review.rating, func.count(Review.id))
            .where(Review.product_id == product_id)
            .group_by(Review.rating)
        ).all()
    }
    total = sum(counts.values())
    average = sum(stars * n for stars, n in counts.items()) / total if total else None
    return RatingSummary(
        average=round_average(average),
        count=total,
        distribution=[RatingBucket(stars=s, count=counts.get(s, 0)) for s in range(5, 0, -1)],
    )


def list_reviews(
    db: Session,
    product_id: uuid.UUID,
    viewer_id: uuid.UUID,
    *,
    sort: ReviewSort,
    page: int,
    page_size: int,
    rating: int | None = None,
) -> ReviewPage:
    if not _product_exists(db, product_id):
        raise ProductNotFound
    order_by = {
        ReviewSort.NEWEST: (Review.created_at.desc(), Review.id),
        ReviewSort.HIGHEST: (Review.rating.desc(), Review.created_at.desc(), Review.id),
        ReviewSort.LOWEST: (Review.rating.asc(), Review.created_at.desc(), Review.id),
    }[sort]
    rating_summary = summary(db, product_id)
    matching = [Review.product_id == product_id]
    if rating is not None:
        matching.append(Review.rating == rating)
    reviews = list(
        db.scalars(
            select(Review)
            .options(selectinload(Review.user))
            .where(*matching)
            .order_by(*order_by)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    mine = db.scalar(
        select(Review)
        .options(selectinload(Review.user))
        .where(Review.product_id == product_id, Review.user_id == viewer_id)
    )
    purchasers = _purchasers(
        db, product_id, [r.user_id for r in reviews] + ([mine.user_id] if mine else [])
    )
    return ReviewPage(
        summary=rating_summary,
        items=[_out(r, viewer_id, purchasers) for r in reviews],
        total=rating_summary.count
        if rating is None
        else next((b.count for b in rating_summary.distribution if b.stars == rating), 0),
        page=page,
        page_size=page_size,
        my_review=_out(mine, viewer_id, purchasers) if mine else None,
    )


def upsert_review(
    db: Session, product_id: uuid.UUID, user_id: uuid.UUID, data: ReviewIn
) -> ReviewOut:
    """Create or replace the shopper's review. One statement, so retries and double submits
    converge on the same single row instead of racing on the unique index."""
    if not _product_exists(db, product_id):
        raise ProductNotFound
    now = utcnow()
    stmt = insert(Review).values(
        id=uuid.uuid4(),
        product_id=product_id,
        user_id=user_id,
        rating=data.rating,
        title=data.title,
        body=data.body,
        is_sample=False,
        created_at=now,
        updated_at=now,
    )
    upsert = stmt.on_conflict_do_update(
        index_elements=[Review.product_id, Review.user_id],
        set_={
            "rating": stmt.excluded.rating,
            "title": stmt.excluded.title,
            "body": stmt.excluded.body,
            # Once the shopper edits it, it is their own words, not seeded demo content.
            "is_sample": False,
            "updated_at": now,
        },
    ).returning(Review.id)
    review_id = db.execute(upsert).scalar_one()
    db.commit()
    review = db.scalars(
        select(Review)
        .options(selectinload(Review.user))
        .where(Review.id == review_id)
        .execution_options(populate_existing=True)
    ).one()
    return _out(review, user_id, _purchasers(db, product_id, [user_id]))


def delete_review(db: Session, product_id: uuid.UUID, user_id: uuid.UUID) -> None:
    """Remove the shopper's own review. Deleting a review that isn't there is a no-op."""
    db.execute(delete(Review).where(Review.product_id == product_id, Review.user_id == user_id))
    db.commit()
