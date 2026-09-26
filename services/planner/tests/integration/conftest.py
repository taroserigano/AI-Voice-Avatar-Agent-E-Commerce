"""PostgreSQL for the turn store: this worktree's own test database by default."""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from ai_commerce_stream.store import TurnStore, metadata

DEFAULT_URL = "postgresql+psycopg://commerce:commerce@localhost:5432/commerce_assistant_test"


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    url = os.environ.get("ASSISTANT_STREAM_TEST_DATABASE_URL", DEFAULT_URL)
    eng = create_engine(url, pool_pre_ping=True)
    try:
        with eng.connect() as c:
            c.execute(text("select 1"))
    except Exception as exc:  # noqa: BLE001
        pytest.fail(f"PostgreSQL isn't reachable at {url} ({exc}); run `pnpm local:up`")
    metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def store(engine: Engine) -> TurnStore:
    with engine.begin() as c:
        c.execute(text("truncate assistant_turn_events, assistant_turns"))
    return TurnStore(engine)
