"""``PlannerPort``: how the assistant runs the planner, in-process or over A2A.

Both adapters yield the same :mod:`ai_commerce_planner.events`, so switching
``PLANNER_TRANSPORT`` changes configuration, not behavior (decision v2-1). Neither lets
the caller's model choose who the planner acts for: the customer comes from the server's
own session lookup.
"""

from __future__ import annotations

import asyncio
import queue
import threading
import uuid
from collections.abc import AsyncIterator, Callable, Iterator
from typing import Any, Protocol

import httpx
from a2a.client import ClientConfig, create_client
from a2a.helpers import get_data_parts, new_data_message
from a2a.types import a2a_pb2 as pb
from pydantic import TypeAdapter

from ai_commerce_planner.a2a_server import agent_card
from ai_commerce_planner.catalog import CatalogPort
from ai_commerce_planner.config import PlannerSettings, get_settings
from ai_commerce_planner.delegation import mint
from ai_commerce_planner.events import ErrorEvent, PlannerEvent
from ai_commerce_planner.runner import PlannerRequest, run_planner

_EVENT: TypeAdapter[Any] = TypeAdapter(PlannerEvent)


class PlannerPort(Protocol):
    def run(
        self,
        request: PlannerRequest,
        *,
        customer_id: uuid.UUID,
        conversation_id: str,
        stop: threading.Event | None = None,
    ) -> Iterator[PlannerEvent]: ...


class InProcessPlanner:
    def __init__(
        self,
        catalog_for: Callable[[uuid.UUID], CatalogPort],
        settings: PlannerSettings | None = None,
    ) -> None:
        self.catalog_for = catalog_for
        self.settings = settings or get_settings()

    def run(
        self,
        request: PlannerRequest,
        *,
        customer_id: uuid.UUID,
        conversation_id: str,
        stop: threading.Event | None = None,
    ) -> Iterator[PlannerEvent]:
        catalog = self.catalog_for(customer_id)
        try:
            yield from run_planner(request, catalog, self.settings, stop)
        finally:
            close = getattr(catalog, "close", None)
            if callable(close):
                close()


def events_from(response: pb.StreamResponse) -> list[PlannerEvent]:
    """Planner events carried by one A2A stream response."""
    kind = response.WhichOneof("payload")
    parts: list[pb.Part] = []
    if kind == "status_update" and response.status_update.status.HasField("message"):
        parts = list(response.status_update.status.message.parts)
    elif kind == "artifact_update":
        parts = list(response.artifact_update.artifact.parts)
    elif kind == "task" and response.task.status.HasField("message"):
        parts = list(response.task.status.message.parts)
    elif kind == "message":
        parts = list(response.message.parts)
    out: list[PlannerEvent] = []
    for data in get_data_parts(parts):
        if isinstance(data, dict) and "type" in data:
            out.append(_EVENT.validate_python(data))
    return out


class A2APlanner:
    """The planner over A2A ``SendStreamingMessage``. Each HTTP request carries a fresh
    single-use delegation token, added by an httpx hook (never in message parts)."""

    def __init__(
        self,
        settings: PlannerSettings | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.transport = transport  # tests pass an ASGI transport

    async def _stream(
        self, request: PlannerRequest, customer_id: uuid.UUID, conversation_id: str
    ) -> AsyncIterator[PlannerEvent]:
        secret = self.settings.planner_delegation_secret

        async def sign(req: httpx.Request) -> None:
            req.headers["Authorization"] = f"Bearer {mint(secret, customer_id, conversation_id)}"

        async with httpx.AsyncClient(
            event_hooks={"request": [sign]},
            timeout=self.settings.planner_timeout_s + 10,
            transport=self.transport,
        ) as http:
            card = agent_card(self.settings)
            if self.settings.planner_a2a_url:
                card.supported_interfaces[0].url = (
                    self.settings.planner_a2a_url.rstrip("/") + "/a2a/"
                )
            client = await create_client(card, ClientConfig(streaming=True, httpx_client=http))
            message = new_data_message(request.model_dump(mode="json"), role=pb.Role.ROLE_USER)
            async for response in client.send_message(pb.SendMessageRequest(message=message)):
                for event in events_from(response):
                    yield event

    def run(
        self,
        request: PlannerRequest,
        *,
        customer_id: uuid.UUID,
        conversation_id: str,
        stop: threading.Event | None = None,
    ) -> Iterator[PlannerEvent]:
        """Sync, streaming wrapper for the assistant's worker thread: an event loop in a
        background thread feeds a queue, so progress reaches the shopper as it happens."""
        events: queue.Queue[PlannerEvent | object] = queue.Queue()
        end = object()

        async def pump() -> None:
            async for event in self._stream(request, customer_id, conversation_id):
                events.put(event)
                if stop is not None and stop.is_set():
                    break

        def run_loop() -> None:
            try:
                asyncio.run(pump())
            except Exception:  # noqa: BLE001 - reported to the shopper as a retryable error
                events.put(
                    ErrorEvent(
                        code="planner_unreachable",
                        message="The planner isn't available.",
                        retryable=True,
                    )
                )
            finally:
                events.put(end)

        threading.Thread(target=run_loop, name="a2a-planner", daemon=True).start()
        while (event := events.get()) is not end:
            yield event  # type: ignore[misc]
