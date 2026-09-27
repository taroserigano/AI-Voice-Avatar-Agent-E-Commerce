"""The conversation index: who owns each conversation and which assistant it's with.

The messages themselves are in the LangGraph checkpoint (PostgreSQL, keyed by conversation ID);
this table is the ownership check and the list a customer sees. Its schema has its own Alembic
history (version table ``alembic_version_assistant``) in the commerce database.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from sqlalchemy import DateTime, Integer, String, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from assistant.config import get_settings


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Conversation(Base):
    __tablename__ = "assistant_conversations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(index=True)
    agent: Mapped[str] = mapped_column(String(20))  # "steph" | "xana"
    title: Mapped[str] = mapped_column(String(120), default="New conversation")
    turn_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


@lru_cache
def get_engine() -> Engine:
    return create_engine(get_settings().database_url, pool_pre_ping=True)


@lru_cache
def get_sessionmaker() -> sessionmaker:  # type: ignore[type-arg]
    return sessionmaker(get_engine(), expire_on_commit=False)


def alembic_config() -> AlembicConfig:
    root = Path(__file__).resolve().parents[2]
    cfg = AlembicConfig(str(root / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "migrations"))
    return cfg


def migrate() -> None:
    """Bring the assistant's tables and the LangGraph checkpoint tables up to date."""
    from langgraph.checkpoint.postgres import PostgresSaver

    alembic_command.upgrade(alembic_config(), "head")
    with PostgresSaver.from_conn_string(get_settings().psycopg_dsn) as saver:
        saver.setup()


def migrate_main() -> None:
    migrate()
    print("assistant tables and checkpoints are up to date")
