"""The planner over A2A, served in-process through httpx's ASGI transport."""

from __future__ import annotations

import asyncio
import uuid

import httpx
import pytest
from a2a.client import ClientConfig, create_client
from a2a.types import a2a_pb2 as pb

from ai_commerce_planner.a2a_server import agent_card, create_app
from ai_commerce_planner.config import PlannerSettings
from ai_commerce_planner.delegation import mint
from ai_commerce_planner.events import BasketEvent, DoneEvent, PlanEvent
from ai_commerce_planner.port import A2APlanner, InProcessPlanner
from ai_commerce_planner.runner import PlannerRequest
from tests.fakes import FakeCatalog

SECRET = "test-secret-0123456789-0123456789"
ALICE = uuid.UUID("00000000-0000-0000-0000-00000000a11c")
BOB = uuid.UUID("00000000-0000-0000-0000-000000000b0b")
GOAL = PlannerRequest(goal="A week of nut-free dinners for 4 under $40")


@pytest.fixture
def settings() -> PlannerSettings:
    return PlannerSettings(
        _env_file=None,
        planner_provider="scripted",
        planner_delegation_secret=SECRET,
        planner_a2a_url="http://planner.internal",
    )


@pytest.fixture
def catalog() -> FakeCatalog:
    return FakeCatalog()


@pytest.fixture
def seen_customers() -> list[uuid.UUID]:
    return []


@pytest.fixture
def transport(
    settings: PlannerSettings, catalog: FakeCatalog, seen_customers: list[uuid.UUID]
) -> httpx.ASGITransport:
    def factory(d):  # noqa: ANN001, ANN202
        seen_customers.append(d.customer_id)
        return catalog

    return httpx.ASGITransport(app=create_app(settings, catalog_factory=factory))


def test_every_route_but_health_needs_a_gateway_token(transport: httpx.ASGITransport) -> None:
    async def go() -> dict[str, int]:
        async with httpx.AsyncClient(transport=transport, base_url="http://planner.internal") as c:
            return {
                "health": (await c.get("/healthz")).status_code,
                "card": (await c.get("/.well-known/agent-card.json")).status_code,
                "rpc": (
                    await c.post("/a2a/", json={"jsonrpc": "2.0", "id": 1, "method": "SendMessage"})
                ).status_code,
                "forged": (
                    await c.post("/a2a/", headers={"Authorization": "Bearer not-a-jwt"}, json={})
                ).status_code,
            }

    assert asyncio.run(go()) == {"health": 200, "card": 401, "rpc": 401, "forged": 401}


def test_a2a_run_matches_the_in_process_run(
    settings: PlannerSettings,
    catalog: FakeCatalog,
    transport: httpx.ASGITransport,
    seen_customers: list[uuid.UUID],
) -> None:
    over_a2a = list(
        A2APlanner(settings, transport=transport).run(GOAL, customer_id=ALICE, conversation_id="c1")
    )
    in_process = list(
        InProcessPlanner(lambda _: catalog, settings).run(
            GOAL, customer_id=ALICE, conversation_id="c1"
        )
    )

    assert [type(e).__name__ for e in over_a2a] == [type(e).__name__ for e in in_process]
    a2a_basket = next(e for e in over_a2a if isinstance(e, BasketEvent)).basket
    local_basket = next(e for e in in_process if isinstance(e, BasketEvent)).basket
    assert [(ln.product_id, ln.quantity, ln.line_total_minor) for ln in a2a_basket.lines] == [
        (ln.product_id, ln.quantity, ln.line_total_minor) for ln in local_basket.lines
    ]
    assert a2a_basket.subtotal_minor == local_basket.subtotal_minor
    assert any(isinstance(e, PlanEvent) for e in over_a2a)
    done = over_a2a[-1]
    assert isinstance(done, DoneEvent) and done.status == "completed"
    assert seen_customers == [ALICE]  # the catalog acted for the token's customer


def test_one_customer_cannot_read_anothers_task(
    settings: PlannerSettings, transport: httpx.ASGITransport
) -> None:
    card = agent_card(settings)
    card.supported_interfaces[0].url = "http://planner.internal/a2a/"

    def client_for(customer: uuid.UUID) -> httpx.AsyncClient:
        async def sign(req: httpx.Request) -> None:
            req.headers["Authorization"] = f"Bearer {mint(SECRET, customer, 'c1')}"

        return httpx.AsyncClient(transport=transport, event_hooks={"request": [sign]})

    async def go() -> tuple[str, str, str]:
        async with client_for(ALICE) as alice_http, client_for(BOB) as bob_http:
            alice = await create_client(card, ClientConfig(streaming=True, httpx_client=alice_http))
            task_id = ""
            message = pb.Message(role=pb.Role.ROLE_USER, message_id=uuid.uuid4().hex)
            message.parts.add().data.struct_value.update(GOAL.model_dump(mode="json"))
            async for resp in alice.send_message(pb.SendMessageRequest(message=message)):
                if resp.WhichOneof("payload") == "task":
                    task_id = resp.task.id
            mine = await alice.get_task(pb.GetTaskRequest(id=task_id))
            bob = await create_client(card, ClientConfig(streaming=True, httpx_client=bob_http))
            try:
                await bob.get_task(pb.GetTaskRequest(id=task_id))
                bob_result = "saw the task"
            except Exception as exc:  # noqa: BLE001
                bob_result = type(exc).__name__
            return task_id, pb.TaskState.Name(mine.status.state), bob_result

    task_id, alice_state, bob_result = asyncio.run(go())
    assert task_id
    assert alice_state == "TASK_STATE_COMPLETED"
    assert bob_result == "TaskNotFoundError"  # not "forbidden": it doesn't exist for Bob
