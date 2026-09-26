"""Catalog reads. Price and stock are always read from PostgreSQL at request time.

Text search asks OpenSearch (keywords) and Pinecone (meaning) for candidate product IDs,
fuses the two ranked lists, then applies every filter, price, and stock check in SQL. The
search engines only ever decide *which* products and in what order, never the numbers.
"""

from __future__ import annotations

import contextvars
import logging
import time
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout
from dataclasses import dataclass
from typing import Any

from opentelemetry import trace
from sqlalchemy import Select, Subquery, and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from commerce.catalog.models import Category, InventoryBalance, Price, Product, Variant
from commerce.catalog.schemas import (
    CategoryOut,
    Facets,
    FacetValue,
    LegStatus,
    Nutrition,
    ProductDetail,
    ProductPage,
    ProductSummary,
    SearchMeta,
    SortOrder,
    TagOut,
    VariantOut,
)
from commerce.catalog.tags import tag_label
from commerce.config import get_settings
from commerce.db import utcnow
from commerce.metrics import (
    search_duration,
    search_leg_duration,
    search_leg_errors,
    search_requests,
)
from commerce.money import DEFAULT_CURRENCY
from commerce.reviews.service import rating_stats_subquery, round_average
from commerce.search.keyword import get_keyword_index
from commerce.search.rrf import reciprocal_rank_fusion
from commerce.search.semantic import get_semantic_index

log = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)
_pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="search-leg")
FACET_LIMIT = 40  # most common product types / tags shown as filters


@dataclass(frozen=True)
class ProductFilters:
    category: str | None = None
    brands: tuple[str, ...] = ()
    min_price_minor: int | None = None
    max_price_minor: int | None = None
    in_stock: bool = False
    product_types: tuple[str, ...] = ()  # any of these
    tags: tuple[str, ...] = ()  # all of these
    exclude_tags: tuple[str, ...] = ()  # none of these


def _stats_subquery() -> Subquery:
    """Per product: lowest current price, units available, active variant count."""
    available = func.coalesce(
        func.sum(func.greatest(InventoryBalance.on_hand - InventoryBalance.reserved, 0)), 0
    )
    return (
        select(
            Variant.product_id.label("product_id"),
            func.min(Price.amount_minor).label("min_price"),
            available.label("available"),
            func.count(func.distinct(Variant.id)).label("variant_count"),
        )
        .join(Price, and_(Price.variant_id == Variant.id, Price.currency == DEFAULT_CURRENCY))
        .outerjoin(InventoryBalance, InventoryBalance.variant_id == Variant.id)
        .where(Variant.is_active.is_(True))
        .group_by(Variant.product_id)
        .subquery()
    )


def _apply_filters[T: tuple[Any, ...]](
    stmt: Select[T],
    stats: Subquery,
    f: ProductFilters,
    *,
    skip_category: bool = False,
    skip_brand: bool = False,
    skip_type: bool = False,
) -> Select[T]:
    if f.category and not skip_category:
        stmt = stmt.where(Category.slug == f.category)
    if f.brands and not skip_brand:
        stmt = stmt.where(Product.brand.in_(f.brands))
    if f.product_types and not skip_type:
        stmt = stmt.where(Product.product_type.in_(f.product_types))
    if f.tags:
        stmt = stmt.where(Product.tags.contains(list(f.tags)))  # GIN-indexed @>
    if f.exclude_tags:
        stmt = stmt.where(~Product.tags.overlap(list(f.exclude_tags)))
    if f.min_price_minor is not None:
        stmt = stmt.where(stats.c.min_price >= f.min_price_minor)
    if f.max_price_minor is not None:
        stmt = stmt.where(stats.c.min_price <= f.max_price_minor)
    if f.in_stock:
        stmt = stmt.where(stats.c.available > 0)
    return stmt


def _base(stats: Subquery, ratings: Subquery, candidate_ids: list[uuid.UUID] | None) -> Select[Any]:
    stmt = (
        select(
            Product,
            Category,
            stats.c.min_price,
            stats.c.available,
            stats.c.variant_count,
            ratings.c.rating_avg,
            func.coalesce(ratings.c.rating_count, 0).label("rating_count"),
        )
        .join(Category, Category.id == Product.category_id)
        .join(stats, stats.c.product_id == Product.id)
        .outerjoin(ratings, ratings.c.product_id == Product.id)
        .where(Product.is_active.is_(True))
    )
    if candidate_ids is not None:
        stmt = stmt.where(Product.id.in_(candidate_ids))
    return stmt


def _category_out(c: Category) -> CategoryOut:
    return CategoryOut(slug=c.slug, name=c.name, policy_class=c.policy_class)


def _tags_out(tags: list[str] | None) -> list[TagOut]:
    return [TagOut(value=t, label=tag_label(t)) for t in tags or []]


def _timed_leg(name: str, fn: Callable[[], list[str]]) -> tuple[list[str] | None, float]:
    start = time.perf_counter()
    with tracer.start_as_current_span(f"search.{name}") as span:
        try:
            ids = fn()
            span.set_attribute("search.result_count", len(ids))
            return ids, (time.perf_counter() - start) * 1000
        except Exception as exc:  # noqa: BLE001 - a failed leg degrades search, it doesn't break it
            span.record_exception(exc)
            span.set_status(trace.StatusCode.ERROR)
            search_leg_errors.add(1, {"backend": name})
            log.warning("search leg %s failed: %s", name, type(exc).__name__)
            return None, (time.perf_counter() - start) * 1000


def _run_legs(query: str) -> tuple[list[str], SearchMeta]:
    settings = get_settings()

    def keyword() -> list[str]:
        return get_keyword_index().search(query, settings.keyword_top_k)

    semantic_index_error = False

    def semantic() -> list[str]:
        nonlocal semantic_index_error
        try:
            index = get_semantic_index()
        except Exception:
            semantic_index_error = True
            raise
        assert index is not None
        return index.search(query, settings.semantic_top_k, settings.semantic_min_score)

    semantic_enabled = bool(settings.pinecone_api_key)
    started = time.perf_counter()
    # Run both legs at once; each thread gets a copy of the trace context.
    kw_future = _pool.submit(contextvars.copy_context().run, _timed_leg, "opensearch", keyword)
    sem_future = (
        _pool.submit(contextvars.copy_context().run, _timed_leg, "pinecone", semantic)
        if semantic_enabled
        else None
    )
    kw_ids, kw_ms = kw_future.result()
    search_leg_duration.record(kw_ms, {"backend": "opensearch"})
    sem_ids: list[str] | None = None
    if sem_future is not None:
        # Meaning-based results are worth waiting for only within the latency budget; after
        # that, answer with keyword results rather than miss the search p95 target.
        remaining = max(0.0, settings.semantic_timeout_ms / 1000 - (time.perf_counter() - started))
        try:
            sem_ids, sem_ms = sem_future.result(timeout=remaining)
            search_leg_duration.record(sem_ms, {"backend": "pinecone"})
        except FuturesTimeout:
            search_leg_errors.add(1, {"backend": "pinecone", "reason": "timeout"})
            trace.get_current_span().set_attribute("search.semantic_timeout", True)

    meta = SearchMeta(
        keyword=LegStatus.OK if kw_ids is not None else LegStatus.UNAVAILABLE,
        semantic=(
            LegStatus.DISABLED
            if not semantic_enabled
            else LegStatus.OK
            if sem_ids is not None
            else LegStatus.UNAVAILABLE
        ),
    )
    if meta.keyword != LegStatus.OK and meta.semantic != LegStatus.OK:
        meta.notice = "Search is running in a reduced mode right now; results may be less relevant."
    elif meta.semantic == LegStatus.DISABLED:
        meta.notice = (
            "Meaning-based search is off (Pinecone is not configured); keyword search only."
        )
    elif meta.semantic == LegStatus.UNAVAILABLE or meta.keyword == LegStatus.UNAVAILABLE:
        meta.notice = "Part of search is temporarily unavailable; results may be less relevant."
    fused = reciprocal_rank_fusion([ids for ids in (kw_ids, sem_ids) if ids])
    return fused, meta


def _fallback_ids(db: Session, query: str, limit: int = 100) -> list[str]:
    """Last resort when both engines are down: a plain SQL text match."""
    terms = [t for t in query.split() if len(t) > 1][:6]
    if not terms:
        return []
    conds = [
        or_(
            Product.title.ilike(f"%{t}%"),
            Product.brand.ilike(f"%{t}%"),
            Product.description.ilike(f"%{t}%"),
        )
        for t in terms
    ]
    rows = db.scalars(
        select(Product.id).where(Product.is_active.is_(True), and_(*conds)).limit(limit)
    )
    return [str(r) for r in rows]


def list_products(
    db: Session,
    *,
    query: str | None,
    filters: ProductFilters,
    sort: SortOrder,
    page: int,
    page_size: int,
) -> ProductPage:
    started = time.perf_counter()
    stats = _stats_subquery()
    ratings = rating_stats_subquery()
    meta: SearchMeta | None = None
    candidate_ids: list[uuid.UUID] | None = None
    rank: dict[uuid.UUID, int] = {}

    q = (query or "").strip()
    if q:
        fused, meta = _run_legs(q)
        if meta.keyword != LegStatus.OK and meta.semantic != LegStatus.OK:
            fused = _fallback_ids(db, q)
        candidate_ids = []
        for i, raw in enumerate(fused):
            try:
                pid = uuid.UUID(raw)
            except ValueError:
                continue  # a stale or foreign ID in a projection is ignored, not trusted
            candidate_ids.append(pid)
            rank[pid] = i

    stmt = _apply_filters(_base(stats, ratings, candidate_ids), stats, filters)
    start = (page - 1) * page_size

    if candidate_ids is not None:
        # A text query has at most a few hundred candidates: rank them in memory.
        rows = list(db.execute(stmt).all())
        if sort == SortOrder.RELEVANCE:
            rows.sort(key=lambda r: rank.get(r[0].id, len(rank)))
        elif sort == SortOrder.PRICE_ASC:
            rows.sort(key=lambda r: (r.min_price, r[0].title))
        elif sort == SortOrder.PRICE_DESC:
            rows.sort(key=lambda r: (-r.min_price, r[0].title))
        elif sort == SortOrder.NEWEST:
            rows.sort(key=lambda r: r[0].created_at, reverse=True)
        elif sort == SortOrder.TOP_RATED:
            rows.sort(key=lambda r: (-(r.rating_avg or 0), -r.rating_count, r[0].title))
        total = len(rows)
        rows = rows[start : start + page_size]
    else:
        # Browsing can span the whole catalog: sort and page in SQL.
        order_by = {
            SortOrder.PRICE_ASC: (stats.c.min_price.asc(), Product.title),
            SortOrder.PRICE_DESC: (stats.c.min_price.desc(), Product.title),
            SortOrder.NEWEST: (Product.created_at.desc(), Product.title),
            SortOrder.TOP_RATED: (
                func.coalesce(ratings.c.rating_avg, 0).desc(),
                func.coalesce(ratings.c.rating_count, 0).desc(),
                Product.title,
            ),
        }.get(sort, (Category.sort_order, Product.title))
        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = list(db.execute(stmt.order_by(*order_by).offset(start).limit(page_size)).all())

    items = [
        ProductSummary(
            id=p.id,
            slug=p.slug,
            title=p.title,
            brand=p.brand,
            category=_category_out(c),
            product_type=p.product_type,
            tags=_tags_out(p.tags),
            image_path=p.image_path,
            price_minor=int(min_price),
            currency=DEFAULT_CURRENCY,
            in_stock=int(available) > 0,
            variant_count=int(variant_count),
            rating_average=round_average(rating_avg),
            rating_count=int(rating_count),
        )
        for p, c, min_price, available, variant_count, rating_avg, rating_count in rows
    ]
    facets = _facets(db, stats, candidate_ids, filters)

    elapsed_ms = (time.perf_counter() - started) * 1000
    if q:
        search_duration.record(elapsed_ms)
        search_requests.add(1, {"zero_results": total == 0})
        span = trace.get_current_span()
        span.set_attribute("search.total", total)
        if meta:
            span.set_attribute("search.keyword", meta.keyword.value)
            span.set_attribute("search.semantic", meta.semantic.value)
    return ProductPage(
        items=items, total=total, page=page, page_size=page_size, facets=facets, search=meta
    )


def _facets(
    db: Session,
    stats: Subquery,
    candidate_ids: list[uuid.UUID] | None,
    f: ProductFilters,
) -> Facets:
    """Each facet is counted with every filter except its own, the usual shopping behavior."""
    cat_stmt = _apply_filters(
        select(Category.slug, Category.name, func.count(Product.id))
        .select_from(Product)
        .join(Category, Category.id == Product.category_id)
        .join(stats, stats.c.product_id == Product.id)
        .where(Product.is_active.is_(True))
        .group_by(Category.slug, Category.name, Category.sort_order)
        .order_by(Category.sort_order),
        stats,
        f,
        skip_category=True,
    )
    brand_stmt = _apply_filters(
        select(Product.brand, func.count(Product.id))
        .select_from(Product)
        .join(Category, Category.id == Product.category_id)
        .join(stats, stats.c.product_id == Product.id)
        .where(Product.is_active.is_(True))
        .group_by(Product.brand)
        .order_by(Product.brand),
        stats,
        f,
        skip_brand=True,
    )
    type_stmt = _apply_filters(
        select(Product.product_type, func.count(Product.id))
        .select_from(Product)
        .join(Category, Category.id == Product.category_id)
        .join(stats, stats.c.product_id == Product.id)
        .where(Product.is_active.is_(True))
        .group_by(Product.product_type)
        .order_by(func.count(Product.id).desc(), Product.product_type)
        .limit(FACET_LIMIT),
        stats,
        f,
        skip_type=True,
    )
    # Tags narrow (every chosen tag must match), so they're counted with all filters applied.
    tag = func.unnest(Product.tags).label("tag")
    tag_stmt = _apply_filters(
        select(tag, func.count())
        .select_from(Product)
        .join(Category, Category.id == Product.category_id)
        .join(stats, stats.c.product_id == Product.id)
        .where(Product.is_active.is_(True))
        .group_by(tag)
        .order_by(func.count().desc(), tag)
        .limit(FACET_LIMIT),
        stats,
        f,
    )
    if candidate_ids is not None:
        cat_stmt = cat_stmt.where(Product.id.in_(candidate_ids))
        brand_stmt = brand_stmt.where(Product.id.in_(candidate_ids))
        type_stmt = type_stmt.where(Product.id.in_(candidate_ids))
        tag_stmt = tag_stmt.where(Product.id.in_(candidate_ids))
    return Facets(
        categories=[FacetValue(value=s, label=n, count=c) for s, n, c in db.execute(cat_stmt)],
        brands=[FacetValue(value=b, label=b, count=c) for b, c in db.execute(brand_stmt)],
        product_types=[
            FacetValue(value=t, label=t.replace("-", " ").capitalize(), count=c)
            for t, c in db.execute(type_stmt)
        ],
        tags=[FacetValue(value=t, label=tag_label(t), count=c) for t, c in db.execute(tag_stmt)],
    )


def get_product(db: Session, product_id: uuid.UUID) -> ProductDetail | None:
    product = db.scalar(
        select(Product)
        .options(
            selectinload(Product.category),
            selectinload(Product.variants).selectinload(Variant.price),
            selectinload(Product.variants).selectinload(Variant.balances),
        )
        .where(Product.id == product_id, Product.is_active.is_(True))
    )
    if product is None:
        return None
    variants = []
    for v in product.variants:
        if not v.is_active or v.price is None:
            continue
        available = sum(max(b.available, 0) for b in v.balances)
        variants.append(
            VariantOut(
                id=v.id,
                sku=v.sku,
                name=v.name,
                attributes=v.attributes,
                price_minor=v.price.amount_minor,
                currency=v.price.currency,
                available=available,
                in_stock=available > 0,
            )
        )
    if not variants:
        return None
    ratings = rating_stats_subquery()
    rating = db.execute(
        select(ratings.c.rating_avg, ratings.c.rating_count).where(
            ratings.c.product_id == product.id
        )
    ).first()
    details = product.details or {}
    return ProductDetail(
        id=product.id,
        slug=product.slug,
        title=product.title,
        brand=product.brand,
        category=_category_out(product.category),
        product_type=product.product_type,
        tags=_tags_out(product.tags),
        image_path=product.image_path,
        price_minor=min(v.price_minor for v in variants),
        currency=DEFAULT_CURRENCY,
        in_stock=any(v.in_stock for v in variants),
        variant_count=len(variants),
        rating_average=round_average(rating.rating_avg) if rating else None,
        rating_count=int(rating.rating_count) if rating else 0,
        description=product.description,
        nutrition=Nutrition(**details["nutrition"]) if details.get("nutrition") else None,
        ingredients=details.get("ingredients"),
        allergens=list(details.get("allergens") or []),
        specs=dict(details.get("specs") or {}),
        variants=variants,
        as_of=utcnow(),
    )


def list_categories(db: Session) -> list[CategoryOut]:
    return [_category_out(c) for c in db.scalars(select(Category).order_by(Category.sort_order))]
