"""Detached turns: a turn keeps running when the browser disconnects, and any client of the
same customer can pick its stream up again from the last event it saw.

``start`` runs the producer in a worker thread (the assistant's LangGraph graph is sync,
because psycopg's async driver doesn't run on Windows' default event loop). Every event
goes to PostgreSQL first, then wakes local followers. ``follow`` replays stored events
after ``Last-Event-ID`` and tails live ones, with heartbeats; a follower in another
process polls the store instead of waiting on the local wake-up.
"""

from __future__ import annotations

import logging
import threading
import uuid
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from ai_commerce_stream.events import Done, Error, Resumed, StreamEvent, TurnStart, parse_event
from ai_commerce_stream.sse import HEARTBEAT, encode, encode_v1, to_v1
from ai_commerce_stream.store import TurnInProgress, TurnStore

log = logging.getLogger(__name__)

Emit = Callable[[StreamEvent], int]
Producer = Callable[[Emit, threading.Event], None]


class TurnNotFound(Exception):
    """No such turn for this customer (someone else's turn looks exactly like this)."""


@dataclass
class _Live:
    wake: threading.Condition = field(default_factory=threading.Condition)
    stop: threading.Event = field(default_factory=threading.Event)
    finished: bool = False


class TurnRunner:
    def __init__(
        self,
        store: TurnStore,
        *,
        workers: int = 8,
        heartbeat_s: float = 15.0,
        poll_s: float = 0.5,
        resume_path: str = "/v1/assistant/turns/{turn_id}/events",
    ) -> None:
        self.store = store
        self.heartbeat_s = heartbeat_s
        self.poll_s = poll_s
        self.resume_path = resume_path
        self._pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="turn")
        self._live: dict[uuid.UUID, _Live] = {}
        self._lock = threading.Lock()

    # --- producing --------------------------------------------------------------------

    def start(
        self, *, conversation_id: str, customer_id: uuid.UUID, agent: str, produce: Producer
    ) -> uuid.UUID:
        """Start a turn. Raises :class:`TurnInProgress` if the conversation has one running."""
        turn = self.store.create_turn(conversation_id, customer_id, agent)
        live = _Live()
        with self._lock:
            self._live[turn.id] = live

        ended = threading.Event()  # set once a terminal event (done/error) is stored

        def emit(event: StreamEvent) -> int:
            if ended.is_set():
                raise RuntimeError("the turn already ended")
            stamped = event.model_copy(
                update={"turn_id": str(turn.id), "agent": event.agent or agent}
            )
            if stamped.terminal:
                ended.set()
            seq = self.store.append(turn.id, stamped.type, stamped.model_dump(mode="json"))
            with live.wake:
                live.wake.notify_all()
            return seq

        def run() -> None:
            status = "completed"
            try:
                emit(
                    TurnStart(
                        conversation_id=conversation_id,
                        resume_url=self.resume_path.format(turn_id=turn.id),
                    )
                )
                produce(emit, live.stop)
                if live.stop.is_set():
                    status = "canceled"
                    if not ended.is_set():
                        emit(Done(status="canceled", model="", simulated=False, prompt_version=""))
            except Exception:
                log.exception("assistant turn failed")
                status = "failed"
                if not ended.is_set():
                    emit(
                        Error(
                            code="turn_failed",
                            message="Sorry, something went wrong on our side. Please try again.",
                        )
                    )
            finally:
                self.store.finish(turn.id, status)
                with live.wake:
                    live.finished = True
                    live.wake.notify_all()
                with self._lock:
                    self._live.pop(turn.id, None)

        self._pool.submit(run)
        return turn.id

    def cancel(self, turn_id: uuid.UUID, customer_id: uuid.UUID) -> None:
        self._owned(turn_id, customer_id)
        with self._lock:
            live = self._live.get(turn_id)
        if live is not None:
            live.stop.set()

    # --- following --------------------------------------------------------------------

    def _owned(self, turn_id: uuid.UUID, customer_id: uuid.UUID) -> None:
        turn = self.store.get(turn_id)
        if turn is None or turn.customer_id != customer_id:
            raise TurnNotFound(turn_id)

    def follow(
        self, turn_id: uuid.UUID, customer_id: uuid.UUID, *, after: int = 0, v2: bool = True
    ) -> Iterator[str]:
        """SSE text for the turn: stored events after ``after``, then live ones, until the
        turn ends. Raises :class:`TurnNotFound` before yielding anything if it isn't theirs."""
        self._owned(turn_id, customer_id)
        return self._follow(turn_id, after, v2)

    def _follow(self, turn_id: uuid.UUID, after: int, v2: bool) -> Iterator[str]:
        if after > 0 and v2:
            yield encode(0, Resumed(turn_id=str(turn_id), from_seq=after))
        seen = after
        idle = 0.0
        while True:
            rows = self.store.events_after(turn_id, seen)
            for seq, data in rows:
                seen = seq
                event = parse_event(data)
                if v2:
                    yield encode(seq, event)
                elif (v1 := to_v1(event)) is not None:
                    yield encode_v1(*v1)
                if event.terminal:
                    return
            if rows:
                idle = 0.0
                continue
            turn = self.store.get(turn_id)
            if turn is None or turn.status != "running":
                # Finished without a terminal event (e.g. interrupted by a quote): drain once.
                if not self.store.events_after(turn_id, seen):
                    return
                continue
            with self._lock:
                live = self._live.get(turn_id)
            if live is not None:
                with live.wake:
                    if not live.finished:
                        live.wake.wait(timeout=self.poll_s)
            else:
                threading.Event().wait(self.poll_s)  # another process runs it: poll
            idle += self.poll_s
            if idle >= self.heartbeat_s:
                idle = 0.0
                yield HEARTBEAT


def start_or_attach(
    runner: TurnRunner,
    *,
    conversation_id: str,
    customer_id: uuid.UUID,
    agent: str,
    produce: Producer,
) -> tuple[uuid.UUID, bool]:
    """(turn_id, started). If a turn is already running, the caller gets 409 with its id."""
    try:
        return runner.start(
            conversation_id=conversation_id, customer_id=customer_id, agent=agent, produce=produce
        ), True
    except TurnInProgress as exc:
        return exc.running_turn_id, False


__all__ = ["Emit", "Producer", "TurnNotFound", "TurnRunner", "start_or_attach"]
