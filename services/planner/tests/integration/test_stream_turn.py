"""A planner turn as the browser sees it: SSE v2 through the turn runner and PostgreSQL."""

from __future__ import annotations

import uuid

import httpx
import pytest

from ai_commerce_planner.a2a_server import create_app
from ai_commerce_planner.basket import ProposedLine, check_basket
from ai_commerce_planner.config import PlannerSettings
from ai_commerce_planner.constraints import parse_constraints
from ai_commerce_planner.port import A2APlanner, InProcessPlanner
from ai_commerce_planner.runner import PlannerRequest
from ai_commerce_planner.stream_bridge import planner_producer, reverify_basket
from ai_commerce_stream.runner import TurnRunner
from ai_commerce_stream.sse import parse_stream
from ai_commerce_stream.store import TurnStore
from tests.fakes import FakeCatalog, product

pytestmark = pytest.mark.integration

SECRET = "test-secret-0123456789-0123456789"
ALICE = uuid.UUID("00000000-0000-0000-0000-00000000a11c")
GOAL = PlannerRequest(goal="A week of nut-free dinners for 4 under $80")


def settings() -> PlannerSettings:
    return PlannerSettings(
        _env_file=None,
        planner_provider="scripted",
        planner_delegation_secret=SECRET,
        planner_a2a_url="http://planner.internal",
    )


@pytest.mark.parametrize("transport", ["inproc", "a2a"])
def test_a_planner_turn_streams_plan_progress_and_a_checked_basket(
    store: TurnStore, transport: str
) -> None:
    catalog = FakeCatalog()
    if transport == "a2a":
        app = create_app(settings(), catalog_factory=lambda _d: catalog)
        port = A2APlanner(settings(), transport=httpx.ASGITransport(app=app))
    else:
        port = InProcessPlanner(lambda _c: catalog, settings())
    runner = TurnRunner(store, poll_s=0.02)

    turn_id = runner.start(
        conversation_id="c1",
        customer_id=ALICE,
        agent="steph",
        produce=planner_producer(
            port, GOAL, customer_id=ALICE, conversation_id="c1", gateway_catalog=lambda: catalog
        ),
    )
    events = parse_stream("".join(runner.follow(turn_id, ALICE)))

    kinds = [e["event"] for e in events]
    assert kinds[0] == "turn.start" and kinds[-1] == "done"
    assert "plan" in kinds and "tool.start" in kinds and "tool.end" in kinds
    plans = [e["data"] for e in events if e["event"] == "plan"]
    assert plans[0]["constraints"] == [
        "Under $80.00",
        "No peanuts or tree nuts (per label)",
        "4 people",
    ]
    assert all(t["status"] == "completed" for t in plans[-1]["todos"])
    (card,) = [e["data"]["card"] for e in events if e["event"] == "card"]
    assert card["kind"] == "basket" and card["simulated"] is True
    assert card["within_budget"] is True and card["subtotal_minor"] <= 8000
    assert all(not {"peanuts", "tree nuts"} & set(line["allergens"]) for line in card["lines"])
    assert events[-1]["data"]["simulated"] is True and events[-1]["data"]["agent"] == "planner"
    assert [int(e["id"]) for e in events] == list(range(1, len(events) + 1))


def test_the_gateway_recomputes_a_tampered_basket() -> None:
    """Over A2A the basket is untrusted: prices and allergens are read again."""
    chicken = product("Chicken", "chicken", 1147)
    satay = product("Satay sauce", "pasta-sauce", 99, allergens=("peanuts",))
    gateway_view = FakeCatalog([chicken, satay])
    rules = parse_constraints("nut-free dinners under $30")
    honest = check_basket([ProposedLine(product_id=chicken.id, quantity=2)], gateway_view, rules)
    tampered = honest.model_copy(
        update={
            "subtotal_minor": 1,
            "lines": [
                honest.lines[0].model_copy(update={"unit_price_minor": 1, "line_total_minor": 2}),
                honest.lines[0].model_copy(
                    update={
                        "product_id": satay.id,
                        "variant_id": satay.variants[0].id,
                        "title": "Totally safe sauce",
                        "allergens": [],
                    }
                ),
            ],
        }
    )

    fixed = reverify_basket(tampered, gateway_view, rules)

    assert [(ln.title, ln.line_total_minor) for ln in fixed.lines] == [("Chicken", 2294)]
    assert fixed.subtotal_minor == 2294
    assert ("Satay sauce", "contains peanuts") in {(e.title, e.reason) for e in fixed.excluded}
