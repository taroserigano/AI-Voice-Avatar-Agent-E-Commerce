"""Alembic environment for the assistant's tables (in the commerce database).

A separate version table keeps this history independent of the commerce service's.
"""

from __future__ import annotations

from alembic import context
from sqlalchemy import create_engine

from assistant.config import get_settings
from assistant.db import Base

VERSION_TABLE = "alembic_version_assistant"
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=get_settings().database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        version_table=VERSION_TABLE,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(get_settings().database_url)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table=VERSION_TABLE,
            # Only this service's tables; the commerce tables have their own history.
            include_name=lambda name, type_, _parent: (
                type_ != "table" or name in target_metadata.tables
            ),
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
