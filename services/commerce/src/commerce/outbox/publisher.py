"""Polling outbox publisher: claims unpublished events and feeds the search projections.

Several publishers can run at once: ``FOR UPDATE SKIP LOCKED`` gives each a disjoint batch.
Delivery is at-least-once, so every handler is idempotent (index by ID, delete by ID).
In the cloud, the same loop publishes to EventBridge/SQS instead of calling the sinks.
"""

from __future__ import annotations

import logging
import signal
import time
from collections import defaultdict

from opentelemetry import trace
from opentelemetry.propagate import extract
from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce.db import get_sessionmaker, utcnow
from commerce.metrics import index_lag, outbox_published
from commerce.outbox.models import OutboxEvent
from commerce.outbox.service import PRODUCT_DELETED, PRODUCT_UPSERTED
from commerce.search.documents import load_docs
from commerce.search.keyword import KeywordIndex, get_keyword_index
from commerce.search.semantic import SemanticIndex, get_semantic_index

log = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

BATCH_SIZE = 50
MAX_ATTEMPTS = 10


def publish_batch(
    db: Session,
    keyword: KeywordIndex,
    semantic: SemanticIndex | None,
    batch_size: int = BATCH_SIZE,
) -> int:
    """Publish one batch in one transaction. Returns how many events were handled."""
    events = list(
        db.scalars(
            select(OutboxEvent)
            .where(OutboxEvent.published_at.is_(None), OutboxEvent.attempts < MAX_ATTEMPTS)
            .order_by(OutboxEvent.id)
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )
    )
    if not events:
        db.rollback()
        return 0

    # Collapse repeats: only the latest state of each product matters.
    by_topic: dict[str, set[str]] = defaultdict(set)
    for ev in events:
        by_topic[ev.topic].add(ev.aggregate_id)

    first_ctx = extract(events[0].trace_context or {})
    with tracer.start_as_current_span("outbox.publish", context=first_ctx) as span:
        span.set_attribute("outbox.batch_size", len(events))
        # Link every source trace, so each product change's trace shows its indexing.
        for ev in events[1:]:
            link_ctx = trace.get_current_span(extract(ev.trace_context or {})).get_span_context()
            if link_ctx.is_valid:
                span.add_link(link_ctx)
        try:
            upsert_ids = sorted(by_topic.get(PRODUCT_UPSERTED, set()))
            delete_ids = sorted(by_topic.get(PRODUCT_DELETED, set()))
            if upsert_ids:
                docs = load_docs(db, upsert_ids)
                found = {d.id for d in docs}
                keyword.upsert(docs)
                if semantic is not None:
                    semantic.upsert(docs)
                # An "upserted" product that is now inactive or gone must leave the index.
                delete_ids = sorted(set(delete_ids) | (set(upsert_ids) - found))
            if delete_ids:
                keyword.delete(delete_ids)
                if semantic is not None:
                    semantic.delete(delete_ids)
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(trace.StatusCode.ERROR)
            for ev in events:
                ev.attempts += 1
                ev.last_error = f"{type(exc).__name__}: {exc}"[:500]
            db.commit()
            for ev in events:
                outbox_published.add(1, {"topic": ev.topic, "outcome": "error"})
            log.warning("outbox batch failed: %s", type(exc).__name__)
            return len(events)

        now = utcnow()
        for ev in events:
            ev.published_at = now
            ev.attempts += 1
            index_lag.record((now - ev.created_at).total_seconds() * 1000, {"topic": ev.topic})
            outbox_published.add(1, {"topic": ev.topic, "outcome": "ok"})
        db.commit()
        return len(events)


def run_forever(poll_interval: float = 1.0) -> None:
    stop = False

    def _stop(*_: object) -> None:
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    keyword = get_keyword_index()
    keyword.ensure_index()
    try:
        semantic = get_semantic_index()
    except Exception as exc:  # noqa: BLE001 - keep keyword search fresh; say why loudly
        semantic = None
        log.error(
            "Pinecone is unavailable (%s): publishing to OpenSearch only. "
            "Fix the Pinecone settings, then run the reindex command.",
            exc,
        )
    if semantic is None:
        log.warning(
            "Meaning-based search is not being updated. Run the reindex command once Pinecone "
            "is configured."
        )
    session_factory = get_sessionmaker()
    log.info("outbox publisher started")
    while not stop:
        with session_factory() as db:
            try:
                handled = publish_batch(db, keyword, semantic)
            except Exception:
                log.exception("outbox publisher loop error")
                handled = 0
        if handled == 0:
            time.sleep(poll_interval)
    log.info("outbox publisher stopped")


def main() -> None:
    from commerce.telemetry import init_telemetry

    init_telemetry("commerce-outbox")
    run_forever()


if __name__ == "__main__":
    main()
