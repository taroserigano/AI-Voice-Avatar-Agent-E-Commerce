"""The planner on the real OpenAI model. Costs money: opt in with PLANNER_LIVE_MODEL=1."""

from __future__ import annotations

import os

import pytest

from ai_commerce_planner.config import PlannerSettings
from ai_commerce_planner.events import BasketEvent, DoneEvent, PlanEvent
from ai_commerce_planner.runner import PlannerRequest, run_planner
from tests.fakes import FakeCatalog

pytestmark = [
    pytest.mark.openai,
    pytest.mark.skipif(
        os.environ.get("PLANNER_LIVE_MODEL") != "1", reason="set PLANNER_LIVE_MODEL=1"
    ),
]


def test_real_model_plans_a_basket_that_code_accepts() -> None:
    settings = PlannerSettings(planner_provider="openai")  # reads OPEN_AI_API from .env
    catalog = FakeCatalog()

    events = list(
        run_planner(
            PlannerRequest(goal="Three nut-free dinners for 2 under $30"), catalog, settings
        )
    )

    done = events[-1]
    assert isinstance(done, DoneEvent) and not done.simulated, events
    assert done.model_calls <= settings.planner_max_model_calls
    assert any(isinstance(e, PlanEvent) for e in events), "the model should plan with write_todos"
    baskets = [e for e in events if isinstance(e, BasketEvent)]
    assert baskets, f"no basket; done={done}"
    basket = baskets[0].basket
    for line in basket.lines:
        facts = catalog.facts(line.product_id)
        assert facts is not None and not {"peanuts", "tree nuts"} & set(facts.allergens)
    assert basket.subtotal_minor == sum(ln.line_total_minor for ln in basket.lines)
