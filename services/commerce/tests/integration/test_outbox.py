from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce.catalog.models import Product
from commerce.outbox.models import OutboxEvent
from commerce.outbox.publisher import publish_batch
from commerce.outbox.service import PRODUCT_UPSERTED, emit
from commerce.search.keyword import get_keyword_index

pytestmark = pytest.mark.integration


def _product(db: Session, slug: str) -> Product:
    product = db.scalar(select(Product).where(Product.slug == slug))
    assert product is not None
    return product


def test_product_change_reaches_search_through_the_outbox(db: Session) -> None:
    product = _product(db, "tempo-jump-rope")
    product.title = "Speed Jump Rope Zephyrcord"  # a word nothing else in the catalog has
    emit(db, PRODUCT_UPSERTED, str(product.id))
    db.commit()

    keyword = get_keyword_index()
    assert str(product.id) not in keyword.search("zephyrcord", 5)

    assert publish_batch(db, keyword, semantic=None) == 1
    assert keyword.search("zephyrcord", 5) == [str(product.id)]
    event = db.scalar(select(OutboxEvent))
    assert event is not None and event.published_at is not None

    product.title = "Speed Jump Rope"
    emit(db, PRODUCT_UPSERTED, str(product.id))
    db.commit()
    publish_batch(db, keyword, semantic=None)


def test_deactivated_product_leaves_the_index(db: Session) -> None:
    product = _product(db, "pebble-pine-plush-otter")
    keyword = get_keyword_index()
    assert str(product.id) in keyword.search("plush otter", 5)

    product.is_active = False
    emit(db, PRODUCT_UPSERTED, str(product.id))
    db.commit()
    publish_batch(db, keyword, semantic=None)
    assert str(product.id) not in keyword.search("plush otter", 5)

    product.is_active = True
    emit(db, PRODUCT_UPSERTED, str(product.id))
    db.commit()
    publish_batch(db, keyword, semantic=None)
    assert str(product.id) in keyword.search("plush otter", 5)


def test_failed_publish_is_retried_later_not_lost(db: Session) -> None:
    product = _product(db, "tempo-foam-roller")
    emit(db, PRODUCT_UPSERTED, str(product.id))
    db.commit()

    class Down:
        def upsert(self, docs):  # type: ignore[no-untyped-def]
            raise ConnectionError("index down")

    publish_batch(db, Down(), semantic=None)  # type: ignore[arg-type]
    event = db.scalar(select(OutboxEvent))
    assert event is not None
    assert (
        event.published_at is None
        and event.attempts == 1
        and "index down" in (event.last_error or "")
    )

    assert publish_batch(db, get_keyword_index(), semantic=None) == 1
    db.refresh(event)
    assert event.published_at is not None


def test_concurrent_publishers_claim_disjoint_batches(db: Session) -> None:
    from commerce.db import get_sessionmaker

    ids = [str(p.id) for p in db.scalars(select(Product).limit(4))]
    for pid in ids:
        emit(db, PRODUCT_UPSERTED, pid)
    db.commit()

    first = get_sessionmaker()()
    locked = list(
        first.scalars(
            select(OutboxEvent).order_by(OutboxEvent.id).limit(2).with_for_update(skip_locked=True)
        )
    )
    try:
        # While the first publisher holds two rows, a second one gets only the other two.
        with get_sessionmaker()() as second:
            handled = publish_batch(second, get_keyword_index(), semantic=None)
        assert handled == 2
    finally:
        first.rollback()
        first.close()
    assert len(locked) == 2
