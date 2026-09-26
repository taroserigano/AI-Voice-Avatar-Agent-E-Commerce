"""Detached, resumable turns against a real PostgreSQL."""

from __future__ import annotations

import threading
import time
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import update
from sqlalchemy.orm import Session

from ai_commerce_stream.events import Done, TextDelta
from ai_commerce_stream.runner import Emit, TurnNotFound, TurnRunner, start_or_attach
from ai_commerce_stream.sse import HEARTBEAT, parse_stream
from ai_commerce_stream.store import TurnInProgress, TurnRow, TurnStore

ALICE = uuid.UUID("00000000-0000-0000-0000-00000000a11c")
BOB = uuid.UUID("00000000-0000-0000-0000-000000000b0b")


def words(n: int, delay_s: float = 0.0, gate: threading.Event | None = None):  # noqa: ANN201
    def produce(emit: Emit, stop: threading.Event) -> None:
        for i in range(n):
            if stop.is_set():
                return
            if gate is not None and i == n // 2:
                gate.wait(5)
            emit(TextDelta(delta=f"w{i} "))
            time.sleep(delay_s)
        emit(Done(model="scripted", simulated=True, prompt_version="steph.v1"))

    return produce


def collect(
    runner: TurnRunner, turn_id: uuid.UUID, customer: uuid.UUID = ALICE, **kw: object
) -> list[dict]:
    return parse_stream("".join(runner.follow(turn_id, customer, **kw)))  # type: ignore[arg-type]


def wait_finished(store: TurnStore, turn_id: uuid.UUID, timeout_s: float = 5.0) -> str:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        turn = store.get(turn_id)
        if turn and turn.status != "running":
            return turn.status
        time.sleep(0.02)
    raise AssertionError("turn didn't finish")


def test_a_resumed_stream_continues_exactly_where_the_client_left_off(store: TurnStore) -> None:
    runner = TurnRunner(store, poll_s=0.02)
    turn_id = runner.start(
        conversation_id="c1", customer_id=ALICE, agent="steph", produce=words(12, 0.01)
    )

    live = collect(runner, turn_id)
    dropped_at = int(live[5]["id"])  # the browser saw events 1..6, then lost the connection
    resumed = collect(runner, turn_id, after=dropped_at)

    assert resumed[0]["event"] == "resumed" and resumed[0]["data"]["from_seq"] == dropped_at
    assert live[:6] + resumed[1:] == live  # no gaps, no duplicates
    assert [e["id"] for e in live] == [str(i) for i in range(1, len(live) + 1)]
    assert live[0]["event"] == "turn.start" and live[-1]["event"] == "done"


def test_a_disconnect_doesnt_stop_the_turn(store: TurnStore) -> None:
    runner = TurnRunner(store, poll_s=0.02)
    turn_id = runner.start(
        conversation_id="c1", customer_id=ALICE, agent="steph", produce=words(20, 0.01)
    )

    stream = runner.follow(turn_id, ALICE)
    next(stream)
    stream.close()  # the browser tab closed

    assert wait_finished(store, turn_id) == "completed"
    assert collect(runner, turn_id)[-1]["event"] == "done"


def test_one_running_turn_per_conversation(store: TurnStore) -> None:
    runner = TurnRunner(store, poll_s=0.02)
    gate = threading.Event()
    first = runner.start(
        conversation_id="c1", customer_id=ALICE, agent="steph", produce=words(4, gate=gate)
    )

    with pytest.raises(TurnInProgress) as err:
        runner.start(conversation_id="c1", customer_id=ALICE, agent="steph", produce=words(1))
    assert err.value.running_turn_id == first
    assert start_or_attach(
        runner, conversation_id="c1", customer_id=ALICE, agent="steph", produce=words(1)
    ) == (first, False)
    other = runner.start(conversation_id="c2", customer_id=ALICE, agent="steph", produce=words(1))

    gate.set()
    assert wait_finished(store, first) == "completed"
    assert wait_finished(store, other) == "completed"
    second, started = start_or_attach(
        runner, conversation_id="c1", customer_id=ALICE, agent="steph", produce=words(1)
    )
    assert started and second != first


def test_another_customer_cant_follow_or_cancel_a_turn(store: TurnStore) -> None:
    runner = TurnRunner(store, poll_s=0.02)
    turn_id = runner.start(conversation_id="c1", customer_id=ALICE, agent="steph", produce=words(2))

    with pytest.raises(TurnNotFound):
        runner.follow(turn_id, BOB)
    with pytest.raises(TurnNotFound):
        runner.cancel(turn_id, BOB)
    with pytest.raises(TurnNotFound):
        runner.follow(uuid.uuid4(), ALICE)
    assert wait_finished(store, turn_id) == "completed"


def test_cancel_ends_the_turn_with_a_canceled_done(store: TurnStore) -> None:
    runner = TurnRunner(store, poll_s=0.02)
    turn_id = runner.start(
        conversation_id="c1", customer_id=ALICE, agent="steph", produce=words(200, 0.01)
    )
    time.sleep(0.1)

    runner.cancel(turn_id, ALICE)

    assert wait_finished(store, turn_id) == "canceled"
    last = collect(runner, turn_id)[-1]
    assert last["event"] == "done" and last["data"]["status"] == "canceled"


def test_a_failing_turn_ends_with_an_error_event(store: TurnStore) -> None:
    def boom(emit: Emit, stop: threading.Event) -> None:
        emit(TextDelta(delta="partial "))
        raise RuntimeError("model exploded")

    runner = TurnRunner(store, poll_s=0.02)
    turn_id = runner.start(conversation_id="c1", customer_id=ALICE, agent="steph", produce=boom)

    events = collect(runner, turn_id)
    assert [e["event"] for e in events] == ["turn.start", "text.delta", "error"]
    assert "model exploded" not in str(events[-1]["data"])  # no internals reach the browser
    assert wait_finished(store, turn_id) == "failed"


def test_a_turn_left_running_by_a_dead_process_doesnt_block_the_conversation(
    store: TurnStore,
) -> None:
    stuck = store.create_turn("c1", ALICE, "steph")
    with Session(store.engine) as db, db.begin():
        db.execute(
            update(TurnRow)
            .where(TurnRow.id == stuck.id)
            .values(started_at=datetime.now(UTC) - timedelta(hours=1))
        )

    runner = TurnRunner(store, poll_s=0.02)
    fresh = runner.start(conversation_id="c1", customer_id=ALICE, agent="steph", produce=words(1))

    assert store.get(stuck.id).status == "failed"  # type: ignore[union-attr]
    assert wait_finished(store, fresh) == "completed"


def test_idle_streams_get_heartbeats(store: TurnStore) -> None:
    gate = threading.Event()
    runner = TurnRunner(store, poll_s=0.02, heartbeat_s=0.05)
    turn_id = runner.start(
        conversation_id="c1", customer_id=ALICE, agent="steph", produce=words(2, gate=gate)
    )

    chunks = []
    for chunk in runner.follow(turn_id, ALICE):
        chunks.append(chunk)
        if chunk == HEARTBEAT:
            gate.set()
    assert HEARTBEAT in chunks


def test_v1_clients_get_only_v1_events_without_ids(store: TurnStore) -> None:
    runner = TurnRunner(store, poll_s=0.02)
    turn_id = runner.start(conversation_id="c1", customer_id=ALICE, agent="steph", produce=words(2))

    events = collect(runner, turn_id, v2=False)

    assert [e["event"] for e in events] == ["text", "text", "done"]
    assert all(e["id"] is None for e in events)


def test_old_finished_turns_are_purged(store: TurnStore) -> None:
    runner = TurnRunner(store, poll_s=0.02)
    old = runner.start(conversation_id="c1", customer_id=ALICE, agent="steph", produce=words(1))
    wait_finished(store, old)
    with Session(store.engine) as db, db.begin():
        db.execute(
            update(TurnRow)
            .where(TurnRow.id == old)
            .values(started_at=datetime.now(UTC) - timedelta(days=31))
        )

    assert store.purge() == 1
    assert store.get(old) is None
    assert store.events_after(old, 0) == []
