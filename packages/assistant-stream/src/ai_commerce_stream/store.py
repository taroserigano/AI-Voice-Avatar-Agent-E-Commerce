"""Turns and their events in PostgreSQL, so a stream can be replayed after a disconnect.

PostgreSQL is the source (never Redis, which is cache-only). One conversation has at most
one running turn: a partial unique index enforces that across processes. A turn whose
process died is marked failed after ``STALE_AFTER`` so the conversation isn't stuck.
Events are kept for ``RETENTION_DAYS`` (decision v2-6); the LangGraph checkpoint remains
the conversation record.

The tables live in this package's ``metadata``; the assistant's Alembic history creates
them (``include_object`` picks up ``assistant_turns`` / ``assistant_turn_events``).
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    delete,
    select,
    text,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

STALE_AFTER = timedelta(minutes=10)
RETENTION_DAYS = 30
RUNNING = "running"
TERMINAL = ("completed", "failed", "canceled", "interrupted", "input_required")

metadata = MetaData()


class _Base(DeclarativeBase):
    metadata = metadata


class TurnRow(_Base):
    __tablename__ = "assistant_turns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[str] = mapped_column(String(64), index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    agent: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), default=RUNNING)
    last_seq: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index(
            "uq_assistant_turns_one_running",
            "conversation_id",
            unique=True,
            postgresql_where=text("status = 'running'"),
        ),
    )


class TurnEventRow(_Base):
    __tablename__ = "assistant_turn_events"

    turn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assistant_turns.id", ondelete="CASCADE"), primary_key=True
    )
    seq: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String(32))
    data: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class TurnInProgress(Exception):
    def __init__(self, running_turn_id: uuid.UUID) -> None:
        super().__init__(f"turn {running_turn_id} is still running")
        self.running_turn_id = running_turn_id


@dataclass(frozen=True)
class Turn:
    id: uuid.UUID
    conversation_id: str
    customer_id: uuid.UUID
    agent: str
    status: str
    last_seq: int


def _now() -> datetime:
    return datetime.now(UTC)


def _turn(row: TurnRow) -> Turn:
    return Turn(row.id, row.conversation_id, row.customer_id, row.agent, row.status, row.last_seq)


class TurnStore:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def _reap_stale(self, db: Session, conversation_id: str) -> None:
        db.execute(
            update(TurnRow)
            .where(
                TurnRow.conversation_id == conversation_id,
                TurnRow.status == RUNNING,
                TurnRow.started_at < _now() - STALE_AFTER,
            )
            .values(status="failed", finished_at=_now())
        )

    def create_turn(self, conversation_id: str, customer_id: uuid.UUID, agent: str) -> Turn:
        """A new running turn, or :class:`TurnInProgress` with the one already running."""
        with Session(self.engine) as db:
            self._reap_stale(db, conversation_id)
            row = TurnRow(
                id=uuid.uuid4(),
                conversation_id=conversation_id,
                customer_id=customer_id,
                agent=agent,
                status=RUNNING,
                last_seq=0,
                started_at=_now(),
            )
            db.add(row)
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                running = db.scalar(
                    select(TurnRow.id).where(
                        TurnRow.conversation_id == conversation_id, TurnRow.status == RUNNING
                    )
                )
                if running is None:  # finished in between: try once more
                    return self.create_turn(conversation_id, customer_id, agent)
                raise TurnInProgress(running) from None
            return _turn(row)

    def append(self, turn_id: uuid.UUID, type_: str, data: dict[str, Any]) -> int:
        """Store one event; returns its sequence number (1, 2, 3... per turn)."""
        with Session(self.engine) as db, db.begin():
            seq = db.scalar(
                update(TurnRow)
                .where(TurnRow.id == turn_id)
                .values(last_seq=TurnRow.last_seq + 1)
                .returning(TurnRow.last_seq)
            )
            if seq is None:
                raise KeyError(turn_id)
            db.add(TurnEventRow(turn_id=turn_id, seq=seq, type=type_, data=data, created_at=_now()))
            return int(seq)

    def finish(self, turn_id: uuid.UUID, status: str) -> None:
        assert status in TERMINAL, status
        with Session(self.engine) as db, db.begin():
            db.execute(
                update(TurnRow)
                .where(TurnRow.id == turn_id, TurnRow.status == RUNNING)
                .values(status=status, finished_at=_now())
            )

    def get(self, turn_id: uuid.UUID) -> Turn | None:
        with Session(self.engine) as db:
            row = db.get(TurnRow, turn_id)
            return _turn(row) if row else None

    def events_after(self, turn_id: uuid.UUID, after: int) -> Sequence[tuple[int, dict[str, Any]]]:
        with Session(self.engine) as db:
            rows = db.execute(
                select(TurnEventRow.seq, TurnEventRow.data)
                .where(TurnEventRow.turn_id == turn_id, TurnEventRow.seq > after)
                .order_by(TurnEventRow.seq)
            ).all()
            return [(int(seq), dict(data)) for seq, data in rows]

    def running_turn(self, conversation_id: str) -> uuid.UUID | None:
        with Session(self.engine) as db:
            return db.scalar(
                select(TurnRow.id).where(
                    TurnRow.conversation_id == conversation_id, TurnRow.status == RUNNING
                )
            )

    def purge(self, older_than_days: int = RETENTION_DAYS) -> int:
        """Delete finished turns (and their events) older than the retention period."""
        with Session(self.engine) as db, db.begin():
            result = db.execute(
                delete(TurnRow).where(
                    TurnRow.status != RUNNING,
                    TurnRow.started_at < _now() - timedelta(days=older_than_days),
                )
            )
            return int(result.rowcount or 0)  # type: ignore[attr-defined]
