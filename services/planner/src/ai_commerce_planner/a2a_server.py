"""The planner as an internal A2A agent (``pnpm dev`` process ``planner``, port 8302).

Internal only (decision v2-2): it binds to localhost, every route including the Agent Card
needs a gateway delegation token, and there are no push notifications. Events are the same
:mod:`ai_commerce_planner.events` the in-process planner yields: progress as ``working``
status messages, the basket as an artifact, the final ``done`` in the completion message.
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from collections.abc import Callable
from typing import Any

from a2a.helpers import get_data_parts, new_data_part, new_task_from_user_message, new_text_part
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    add_a2a_routes_to_fastapi,
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import a2a_pb2 as pb
from fastapi import FastAPI
from pydantic import ValidationError
from starlette.authentication import BaseUser
from starlette.types import ASGIApp, Receive, Scope, Send

from ai_commerce_planner.catalog import CatalogPort, CommerceCatalog
from ai_commerce_planner.config import PlannerSettings, get_settings
from ai_commerce_planner.delegation import Delegation, DelegationError, ReplayGuard, verify
from ai_commerce_planner.events import BasketEvent, DoneEvent, ErrorEvent
from ai_commerce_planner.runner import PlannerRequest, run_planner

log = logging.getLogger(__name__)

RPC_PATH = "/a2a/"
PUBLIC_PATHS = frozenset({"/healthz"})
CatalogFactory = Callable[[Delegation], CatalogPort]


class DelegatedUser(BaseUser):
    """The customer the gateway is acting for. ``display_name`` is the A2A task owner, so
    one customer's tasks are invisible to another's."""

    def __init__(self, delegation: Delegation) -> None:
        self.delegation = delegation

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return str(self.delegation.customer_id)


class DelegationMiddleware:
    def __init__(self, app: ASGIApp, *, secret: str, replay: ReplayGuard) -> None:
        self.app, self.secret, self.replay = app, secret, replay

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"] in PUBLIC_PATHS:
            await self.app(scope, receive, send)
            return
        header = dict(scope["headers"]).get(b"authorization", b"").decode("latin-1")
        token = header.removeprefix("Bearer ").strip() if header.startswith("Bearer ") else ""
        try:
            delegation = verify(token, self.secret, self.replay)
        except DelegationError as exc:
            log.info("planner request refused: %s", exc)
            body = json.dumps({"error": "unauthorized"}).encode()
            await send(
                {
                    "type": "http.response.start",
                    "status": 401,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"www-authenticate", b"Bearer"),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})
            return
        scope["user"] = DelegatedUser(delegation)
        scope["auth"] = delegation
        await self.app(scope, receive, send)


def commerce_catalog_factory(settings: PlannerSettings) -> CatalogFactory:
    """The planner's own least-privilege commerce identity, acting for the customer."""

    def factory(d: Delegation) -> CatalogPort:
        return CommerceCatalog(
            settings.commerce_api_url,
            headers={
                "Authorization": f"Bearer {settings.planner_service_token}",
                "X-On-Behalf-Of": str(d.customer_id),
            },
        )

    return factory


class PlannerExecutor(AgentExecutor):
    def __init__(self, catalog_factory: CatalogFactory, settings: PlannerSettings) -> None:
        self.catalog_factory = catalog_factory
        self.settings = settings
        self._stops: dict[str, threading.Event] = {}

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        assert context.message is not None
        task = context.current_task or new_task_from_user_message(context.message)
        await event_queue.enqueue_event(task)  # A2A 1.0: the Task first, then updates
        updater = TaskUpdater(event_queue, task.id, task.context_id)

        delegation = (context.call_context.state if context.call_context else {}).get("auth")
        if not isinstance(delegation, Delegation):
            await updater.reject(updater.new_agent_message([new_text_part("Not authorized.")]))
            return
        try:
            data = next(iter(get_data_parts(context.message.parts)), None)
            request = PlannerRequest.model_validate(data)
        except ValidationError:
            await updater.reject(
                updater.new_agent_message(
                    [new_text_part("Send one data part: {goal, constraints}.")]
                )
            )
            return

        await updater.start_work()
        stop = self._stops[task.id] = threading.Event()
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[Any] = asyncio.Queue()
        catalog = self.catalog_factory(delegation)

        def work() -> None:
            try:
                for event in run_planner(request, catalog, self.settings, stop):
                    loop.call_soon_threadsafe(queue.put_nowait, event)
            finally:
                close = getattr(catalog, "close", None)
                if callable(close):
                    close()
                loop.call_soon_threadsafe(queue.put_nowait, None)

        worker = loop.run_in_executor(None, work)
        done: DoneEvent | None = None
        failed = False
        try:
            while (event := await queue.get()) is not None:
                part = new_data_part(event.model_dump(mode="json"))
                if isinstance(event, BasketEvent):
                    await updater.add_artifact([part], name="basket")
                elif isinstance(event, DoneEvent):
                    done = event
                else:
                    failed = failed or isinstance(event, ErrorEvent)
                    await updater.update_status(
                        pb.TaskState.TASK_STATE_WORKING, message=updater.new_agent_message([part])
                    )
            await worker
        finally:
            self._stops.pop(task.id, None)

        final = (
            updater.new_agent_message([new_data_part(done.model_dump(mode="json"))])
            if done
            else None
        )
        if done is not None and done.status == "canceled":
            await updater.cancel(final)
        elif failed or done is None:
            await updater.failed(final)
        else:
            await updater.complete(final)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        if context.task_id and (stop := self._stops.get(context.task_id)):
            stop.set()


def agent_card(settings: PlannerSettings) -> pb.AgentCard:
    return pb.AgentCard(
        name="larkspur-shopping-planner",
        description="Builds baskets from the Larkspur catalog for multi-step goals: meal "
        "plans, budgets, and allergen rules checked against product labels. Internal only.",
        version="0.1.0",
        supported_interfaces=[
            pb.AgentInterface(
                url=f"http://{settings.planner_host}:{settings.planner_port}{RPC_PATH}",
                protocol_binding="JSONRPC",
                protocol_version="1.0",
            )
        ],
        capabilities=pb.AgentCapabilities(streaming=True, push_notifications=False),
        security_schemes={
            "gatewayDelegation": pb.SecurityScheme(
                http_auth_security_scheme=pb.HTTPAuthSecurityScheme(
                    scheme="Bearer", bearer_format="JWT"
                )
            )
        },
        security_requirements=[
            pb.SecurityRequirement(schemes={"gatewayDelegation": pb.StringList()})
        ],
        default_input_modes=["application/json"],
        default_output_modes=["application/json"],
        skills=[
            pb.AgentSkill(
                id="meal_plan",
                name="Meal plan basket",
                description='e.g. "a week of dinners for 4 under $80"',
                tags=["grocery", "planning"],
            ),
            pb.AgentSkill(
                id="allergen_aware_basket",
                name="Allergen-aware basket",
                description="Leaves out items whose labels list the shopper's allergens",
                tags=["grocery", "allergens"],
            ),
        ],
    )


def create_app(
    settings: PlannerSettings | None = None, catalog_factory: CatalogFactory | None = None
) -> FastAPI:
    settings = settings or get_settings()
    settings.check()
    card = agent_card(settings)
    handler = DefaultRequestHandler(
        agent_executor=PlannerExecutor(
            catalog_factory or commerce_catalog_factory(settings), settings
        ),
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )
    app = FastAPI(
        title="Larkspur shopping planner (internal)",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    add_a2a_routes_to_fastapi(
        app,
        agent_card_routes=create_agent_card_routes(card),
        jsonrpc_routes=create_jsonrpc_routes(handler, rpc_url=RPC_PATH),
    )
    app.add_middleware(
        DelegationMiddleware, secret=settings.planner_delegation_secret, replay=ReplayGuard()
    )
    return app


def main() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(create_app(settings), host=settings.planner_host, port=settings.planner_port)


if __name__ == "__main__":
    main()
