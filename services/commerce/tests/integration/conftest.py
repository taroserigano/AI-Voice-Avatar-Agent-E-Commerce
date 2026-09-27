"""Integration fixtures: real PostgreSQL (commerce_test) and OpenSearch.

Start them with ``pnpm infra:up``. Pinecone is used only if PINECONE_API_KEY is set, in a
throwaway ``products-test-<id>`` namespace that is deleted afterwards.
"""

from __future__ import annotations

import functools
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from fastapi.testclient import TestClient
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from sqlalchemy import select, text, update
from sqlalchemy.orm import Session

from commerce.auth.models import User
from commerce.auth.sessions import hash_password
from commerce.catalog.models import InventoryBalance, Price, Variant
from commerce.config import get_settings
from commerce.db import get_engine, get_sessionmaker
from commerce.main import create_app
from commerce.search.keyword import get_keyword_index
from commerce.search.reindex import reindex
from commerce.search.semantic import get_semantic_index
from commerce.seed.catalog import PRODUCTS
from commerce.seed.data import DEV_USERS
from commerce.seed.run import make_sku, seed_catalog, seed_dev_users, seed_stores
from commerce.telemetry import init_telemetry

pytestmark = pytest.mark.integration

SPANS = InMemorySpanExporter()
MUTABLE_TABLES = (
    "cart_items",
    "carts",
    "order_lines",
    "orders",
    "sessions",
    "outbox_events",
    "product_reviews",
    "customer_events",
    "support_cases",
    "return_quotes",
    "refund_attempts",
    "return_items",
    "return_requests",
    "shipment_events",
    "shipments",
    "payment_attempts",
)
PASSWORDS = {u.email: u.password for u in DEV_USERS}


@pytest.fixture(scope="session", autouse=True)
def _telemetry() -> None:
    init_telemetry("commerce-api-test", extra_span_processors=[SimpleSpanProcessor(SPANS)])


@pytest.fixture(scope="session", autouse=True)
def _database(_telemetry: None) -> Iterator[None]:
    # Bring the test database to the latest schema, so a fresh clone needs no extra step.
    alembic_cfg = AlembicConfig(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    alembic_command.upgrade(alembic_cfg, "head")
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("SELECT 1"))
    with get_sessionmaker()() as db:
        seed_catalog(db)
        seed_stores(db)
        seed_dev_users(db)
        db.commit()
    _seed_password_hashes()
    reindex()
    yield
    get_keyword_index().client.indices.delete(
        index=get_settings().products_index, ignore_unavailable=True
    )
    try:
        semantic = get_semantic_index()
    except Exception:  # noqa: BLE001 - misconfigured Pinecone: nothing was written to clean up
        semantic = None
    if semantic is not None:
        semantic.clear()


@functools.cache
def _seed_password_hashes() -> dict[str, str]:
    """Hash each seeded account's dev password once per test session."""
    return {email: hash_password(password) for email, password in PASSWORDS.items()}


@functools.cache
def _seed_values() -> dict[str, tuple[int, int]]:
    """SKU -> (seed price, seed stock) for the whole catalog."""
    return {
        v.sku or make_sku(p.slug, v.code): (v.price_cents or p.price_cents, v.stock)
        for p in PRODUCTS
        for v in p.variants
    }


def _reset_catalog(db: Session) -> None:
    """Put every price and stock level back to the seed values.

    One read of the whole catalog, then updates only for the few rows a test changed.
    """
    rows = db.execute(
        select(Variant.id, Variant.sku, Price.amount_minor, InventoryBalance.on_hand,
               InventoryBalance.reserved)
        .join(Price, Price.variant_id == Variant.id)
        .join(InventoryBalance, InventoryBalance.variant_id == Variant.id)
    )  # fmt: skip
    seed = _seed_values()
    for variant_id, sku, price, on_hand, reserved in rows:
        seed_price, seed_stock = seed.get(sku, (price, on_hand))
        if price != seed_price:
            db.execute(
                update(Price).where(Price.variant_id == variant_id).values(amount_minor=seed_price)
            )
        if (on_hand, reserved) != (seed_stock, 0):
            db.execute(
                update(InventoryBalance)
                .where(InventoryBalance.variant_id == variant_id)
                .values(on_hand=seed_stock, reserved=0)
            )


@pytest.fixture(autouse=True)
def _clean_state() -> Iterator[None]:
    with get_sessionmaker()() as db:
        db.execute(text(f"TRUNCATE {', '.join(MUTABLE_TABLES)} RESTART IDENTITY CASCADE"))
        seed_emails = [u.email for u in DEV_USERS]
        db.execute(
            text("DELETE FROM users WHERE NOT (email = ANY(:emails))"), {"emails": seed_emails}
        )
        # Undo any password changes without re-hashing on every test.
        for email, password_hash in _seed_password_hashes().items():
            db.execute(update(User).where(User.email == email).values(password_hash=password_hash))
        _reset_catalog(db)
        db.commit()
    SPANS.clear()
    yield


@pytest.fixture
def db() -> Iterator[Session]:
    with get_sessionmaker()() as session:
        yield session


@pytest.fixture(scope="session")
def app():  # type: ignore[no-untyped-def]
    application = create_app()
    FastAPIInstrumentor.instrument_app(application)
    return application


@pytest.fixture
def client(app) -> TestClient:  # type: ignore[no-untyped-def]
    return TestClient(app)


def sign_in(client: TestClient, email: str) -> TestClient:
    resp = client.post("/v1/auth/sign-in", json={"email": email, "password": PASSWORDS[email]})
    assert resp.status_code == 200, resp.text
    return client


@pytest.fixture
def alice(app) -> TestClient:  # type: ignore[no-untyped-def]
    return sign_in(TestClient(app), "alice@example.com")


@pytest.fixture
def bob(app) -> TestClient:  # type: ignore[no-untyped-def]
    return sign_in(TestClient(app), "bob@example.com")


def variant_id_for(db: Session, slug: str, code: str) -> str:
    vid = db.scalar(select(Variant.id).where(Variant.sku == make_sku(slug, code)))
    assert vid is not None
    return str(vid)
