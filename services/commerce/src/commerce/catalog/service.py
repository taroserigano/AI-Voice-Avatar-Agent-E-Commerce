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
from sqlalchemy import Select, Subquery, and_, case, func, or_, select
from sqlalchemy.orm import Session, selectinload

from commerce.catalog.display import (
    PRIOR_MEAN,
    PRIOR_WEIGHT,
    bayesian_rating,
    type_label,
    unit_price,
)
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
from commerce.search.ranking import Candidate, Ranking, rank_candidates
from commerce.search.rrf import reciprocal_rank_fusion
from commerce.search.semantic import get_semantic_index

log = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)
_pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="search-leg")
FACET_LIMIT = 40  # most common product types / tags shown as filters across departments
DEPARTMENT_FACET_LIMIT = 200  # within one department, show every type


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


def _timed_leg[T](name: str, fn: Callable[[], list[T]]) -> tuple[list[T] | None, float]:
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


@dataclass(frozen=True)
class LegResults:
    ids: list[str]  # fused, best first
    meta: SearchMeta
    semantic_ids: frozenset[str] = frozenset()  # meaning-based hits that passed the score cut
    # The weakest keyword hit, when the leg returned as many hits as it asks for (so more
    # matches may exist past it); None when the list ended on its own.
    keyword_last: str | None = None


def _semantic_keep(
    hits: list[tuple[str, float]], keyword_ids: set[str], relative: float
) -> list[str]:
    """Drop the weak tail of meaning-only hits: below `relative` x the best score, a hit
    OpenSearch didn't also find is more likely noise than a synonym."""
    if not hits:
        return []
    cut = max(score for _, score in hits) * relative
    return [doc_id for doc_id, score in hits if score >= cut or doc_id in keyword_ids]


def _run_legs(query: str) -> LegResults:
    settings = get_settings()

    def keyword() -> list[str]:
        return get_keyword_index().search(query, settings.keyword_top_k)

    def semantic() -> list[tuple[str, float]]:
        index = get_semantic_index()
        assert index is not None
        return index.search_scored(query, settings.semantic_top_k, settings.semantic_min_score)

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
    sem_hits: list[tuple[str, float]] | None = None
    if sem_future is not None:
        # Meaning-based results are worth waiting for only within the latency budget; after
        # that, answer with keyword results rather than miss the search p95 target.
        remaining = max(0.0, settings.semantic_timeout_ms / 1000 - (time.perf_counter() - started))
        try:
            sem_hits, sem_ms = sem_future.result(timeout=remaining)
            search_leg_duration.record(sem_ms, {"backend": "pinecone"})
        except FuturesTimeout:
            search_leg_errors.add(1, {"backend": "pinecone", "reason": "timeout"})
            trace.get_current_span().set_attribute("search.semantic_timeout", True)

    # Shoppers see a notice only when keyword search itself failed. Meaning-based search
    # being off or unreachable is an operations problem (logged and measured), not theirs.
    meta = SearchMeta(
        keyword=LegStatus.OK if kw_ids is not None else LegStatus.UNAVAILABLE,
        semantic=(
            LegStatus.DISABLED
            if not semantic_enabled
            else LegStatus.OK
            if sem_hits is not None
            else LegStatus.UNAVAILABLE
        ),
    )
    if meta.keyword != LegStatus.OK and meta.semantic != LegStatus.OK:
        meta.notice = "Search is running in a reduced mode right now; results may be less relevant."
    elif meta.keyword == LegStatus.UNAVAILABLE:
        meta.notice = "Part of search is temporarily unavailable; results may be less relevant."
    sem_ids = _semantic_keep(sem_hits or [], set(kw_ids or ()), settings.semantic_relative_score)
    fused = reciprocal_rank_fusion([ids for ids in (kw_ids, sem_ids) if ids])
    return LegResults(
        ids=fused,
        meta=meta,
        semantic_ids=frozenset(sem_ids),
        keyword_last=(kw_ids[-1] if kw_ids and len(kw_ids) >= settings.keyword_top_k else None),
    )


FALLBACK_LIMIT = 100


def _fallback_ids(db: Session, query: str, limit: int = FALLBACK_LIMIT) -> list[str]:
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


def _rank(db: Session, query: str, ids: list[uuid.UUID], semantic_ids: set[uuid.UUID]) -> Ranking:
    """Re-rank fused candidates by the words they share with the query (text from PostgreSQL)."""
    if not ids:
        return Ranking([], 0, False)  # nothing matched, so nothing matched exactly
    rows = {
        r.id: r
        for r in db.execute(
            select(
                Product.id,
                Product.title,
                Product.brand,
                Product.product_type,
                Product.tags,
                Product.description,
            ).where(Product.id.in_(ids), Product.is_active.is_(True))
        )
    }
    return rank_candidates(
        query,
        [
            Candidate(
                id=pid,
                title=r.title,
                product_type=r.product_type,
                brand=r.brand,
                tag_labels=[tag_label(t) for t in r.tags or []],
                description=r.description,
                semantic=pid in semantic_ids,
            )
            for pid in ids
            if (r := rows.get(pid)) is not None
        ],
    )


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
        legs = _run_legs(q)
        meta, fused, last = legs.meta, legs.ids, legs.keyword_last
        if meta.keyword != LegStatus.OK and meta.semantic != LegStatus.OK:
            fused = _fallback_ids(db, q)
            last = fused[-1] if len(fused) >= FALLBACK_LIMIT else None
        parsed: list[uuid.UUID] = []
        for raw in fused:
            try:
                parsed.append(uuid.UUID(raw))
            except ValueError:
                continue  # a stale or foreign ID in a projection is ignored, not trusted
        semantic_ids = {pid for pid in parsed if str(pid) in legs.semantic_ids}
        ranking = _rank(db, q, parsed, semantic_ids)
        candidate_ids = [pid for pid in ranking.ids if isinstance(pid, uuid.UUID)]
        rank = {pid: i for i, pid in enumerate(candidate_ids)}
        meta.exact_match = ranking.exact
        # The candidate list stopped at its limit. If even its weakest hit is a real match
        # (it survived re-ranking), more lie past the limit and the total is a lower bound.
        meta.total_capped = last is not None and last in {str(pid) for pid in rank}

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
            rows.sort(key=lambda r: (-bayesian_rating(r.rating_avg, r.rating_count), r[0].title))
        total = len(rows)
        rows = rows[start : start + page_size]
    else:
        # Browsing can span the whole catalog: sort and page in SQL.
        # Rating blended with a prior, so a few perfect reviews don't beat many good ones.
        count = func.coalesce(ratings.c.rating_count, 0)
        blended = case(
            (
                count > 0,
                (ratings.c.rating_avg * count + PRIOR_MEAN * PRIOR_WEIGHT) / (count + PRIOR_WEIGHT),
            ),
            else_=PRIOR_MEAN - 0.5,
        )
        order_by = {
            SortOrder.PRICE_ASC: (stats.c.min_price.asc(), Product.title),
            SortOrder.PRICE_DESC: (stats.c.min_price.desc(), Product.title),
            SortOrder.NEWEST: (Product.created_at.desc(), Product.title),
            SortOrder.TOP_RATED: (blended.desc(), count.desc(), Product.title),
            # "Featured": well-reviewed, in-stock products first, in a stable but varied order
            # (not alphabetical, which put "1% Low Fat…" first everywhere).
            SortOrder.RELEVANCE: (
                (stats.c.available > 0).desc(),
                func.round(blended * 2).desc(),
                func.md5(Product.slug),
            ),
        }[sort]
        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = list(db.execute(stmt.order_by(*order_by).offset(start).limit(page_size)).all())

    defaults = _default_variants(db, [r[0].id for r in rows])
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
            type_label=type_label(p.product_type),
            **defaults.get(p.id, {}),
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


@dataclass(frozen=True)
class Offer:
    price_minor: int
    in_stock: bool


def product_offers(db: Session, product_ids: set[uuid.UUID]) -> dict[uuid.UUID, Offer]:
    """Per product, the price product cards show (the default option: cheapest in stock, else
    cheapest) and whether any option is in stock."""
    if not product_ids:
        return {}
    defaults = _default_variants(db, list(product_ids))
    stats = _stats_subquery()
    rows = db.execute(
        select(stats.c.product_id, stats.c.available).where(stats.c.product_id.in_(product_ids))
    ).all()
    return {
        pid: Offer(int(defaults[pid]["default_price_minor"]), int(avail) > 0)
        for pid, avail in rows
        if pid in defaults
    }


def _default_variants(db: Session, product_ids: list[uuid.UUID]) -> dict[uuid.UUID, dict[str, Any]]:
    """Per product, the option quick-add uses: the cheapest in-stock one (else the cheapest)."""
    if not product_ids:
        return {}
    available = func.coalesce(
        func.sum(func.greatest(InventoryBalance.on_hand - InventoryBalance.reserved, 0)), 0
    )
    rows = db.execute(
        select(Variant, Price.amount_minor, available.label("available"))
        .join(Price, and_(Price.variant_id == Variant.id, Price.currency == DEFAULT_CURRENCY))
        .outerjoin(InventoryBalance, InventoryBalance.variant_id == Variant.id)
        .where(Variant.product_id.in_(product_ids), Variant.is_active.is_(True))
        .group_by(Variant.id, Price.amount_minor)
    ).all()
    # in stock first, then cheapest, then the product page's option order (so the two agree)
    best: dict[uuid.UUID, tuple[tuple[bool, int, int, str], Variant]] = {}
    for variant, price, avail in rows:
        key = (int(avail) <= 0, int(price), variant.sort_order, variant.sku)
        current = best.get(variant.product_id)
        if current is None or key < current[0]:
            best[variant.product_id] = (key, variant)
    return {
        pid: {
            "default_variant_id": v.id,
            "default_variant_name": v.name,
            "default_price_minor": key[1],
            "unit_price": unit_price(key[1], v.attributes),
        }
        for pid, (key, v) in best.items()
    }


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
        .limit(DEPARTMENT_FACET_LIMIT if f.category else FACET_LIMIT),
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
            FacetValue(value=t, label=type_label(t), count=c) for t, c in db.execute(type_stmt)
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
                unit_price=unit_price(v.price.amount_minor, v.attributes),
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
    # the option quick add would pick: cheapest in stock, else cheapest (as in listings)
    default = min(variants, key=lambda v: (not v.in_stock, v.price_minor))
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
        type_label=type_label(product.product_type),
        default_variant_id=default.id,
        default_variant_name=default.name,
        default_price_minor=default.price_minor,
        unit_price=default.unit_price,
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
