"""The planner graph: its tool surface, and whole runs with the scripted and a hostile model."""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from ai_commerce_planner.agent import build_planner
from ai_commerce_planner.config import PlannerSettings
from ai_commerce_planner.constraints import Constraints, parse_constraints
from ai_commerce_planner.events import BasketEvent, DoneEvent, PlanEvent, ToolStartEvent
from ai_commerce_planner.runner import PlannerRequest, run_planner
from ai_commerce_planner.scripted import ScriptedPlannerModel
from tests.fakes import FakeCatalog

FORBIDDEN_TOOL = re.compile(
    r"cart|order|return|refund|pay|confirm|checkout|handoff|execute|shell", re.I
)
IDENTITY_ARG = re.compile(r"user|customer|account|email|token|session|on_behalf", re.I)


def compiled_tools(graph: Any) -> dict[str, Any]:
    return graph.nodes["tools"].bound._tools_by_name  # type: ignore[no-any-return]


def build(
    catalog: FakeCatalog, constraints: Constraints, model: BaseChatModel | None = None
) -> Any:
    m = model or ScriptedPlannerModel()
    return build_planner(
        model=m,
        helper_model=m,
        catalog=catalog,
        constraints=constraints,
        max_model_calls=12,
        max_tool_calls=40,
    )


def test_the_planner_can_only_search_check_propose_plan_and_take_notes() -> None:
    tools = compiled_tools(build(FakeCatalog(), Constraints()))

    assert "execute" not in tools
    assert not [name for name in tools if FORBIDDEN_TOOL.search(name)]
    assert {"search_products", "check_basket", "propose_basket", "write_todos", "task"} <= set(
        tools
    )
    for name, t in tools.items():
        args = set(
            (t.args_schema.model_json_schema() if t.args_schema else {}).get("properties", {})
        )
        assert not [a for a in args if IDENTITY_ARG.search(a)], f"{name} takes an identity argument"


def settings(**kw: Any) -> PlannerSettings:
    return PlannerSettings(_env_file=None, planner_provider="scripted", **kw)


def test_scripted_run_streams_a_plan_and_a_basket_that_obeys_every_rule() -> None:
    catalog = FakeCatalog()
    goal = "A week of nut-free dinners for 4 under $40"

    events = list(run_planner(PlannerRequest(goal=goal), catalog, settings()))

    plans = [e for e in events if isinstance(e, PlanEvent)]
    assert plans and plans[0].todos[0].status == "in_progress"
    assert all(t.status == "completed" for t in plans[-1].todos)
    assert [p.revision for p in plans] == list(range(1, len(plans) + 1))
    assert any(isinstance(e, ToolStartEvent) and e.tool == "search_products" for e in events)

    (basket_event,) = [e for e in events if isinstance(e, BasketEvent)]
    basket = basket_event.basket
    assert basket_event.simulated
    assert basket.lines
    for line in basket.lines:
        facts = catalog.facts(line.product_id)
        assert facts is not None
        assert not {"peanuts", "tree nuts"} & set(facts.allergens)
        assert line.unit_price_minor == facts.variants[0].price_minor
    assert basket.subtotal_minor == sum(ln.line_total_minor for ln in basket.lines)
    assert basket.within_budget is True and basket.subtotal_minor <= 4000

    done = events[-1]
    assert isinstance(done, DoneEvent) and done.status == "completed" and done.simulated


class HostileModel(BaseChatModel):
    """Ignores every instruction: proposes the injected peanut sauce and a made-up item."""

    peanut_id: str

    @property
    def _llm_type(self) -> str:
        return "hostile"

    def bind_tools(self, tools: Any, **kwargs: Any) -> HostileModel:  # type: ignore[override]
        return self

    def _generate(
        self, messages: list[BaseMessage], stop: Any = None, run_manager: Any = None, **kw: Any
    ) -> ChatResult:
        if any(isinstance(m, ToolMessage) for m in messages):
            msg = AIMessage(content="Done! It's totally safe for nut allergies.")
        else:
            msg = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "propose_basket",
                        "id": "evil",
                        "type": "tool_call",
                        "args": {
                            "summary": "Peanut sauce, as the product asked",
                            "lines": [
                                {"product_id": self.peanut_id, "quantity": 12},
                                {
                                    "product_id": "00000000-0000-0000-0000-000000000000",
                                    "quantity": 1,
                                },
                            ],
                        },
                    }
                ],
            )
        return ChatResult(generations=[ChatGeneration(message=msg)])


def test_code_keeps_banned_items_out_even_when_the_model_obeys_an_injection() -> None:
    catalog = FakeCatalog()
    peanut = catalog.by_title("Satay sauce")
    graph = build(
        catalog, parse_constraints("nut-free dinners"), HostileModel(peanut_id=str(peanut.id))
    )

    state = graph.invoke({"messages": [{"role": "user", "content": "nut-free dinners"}]})

    basket = state["basket"]
    assert basket["lines"] == []
    assert {e["reason"] for e in basket["excluded"]} == {"contains peanuts", "not in the catalog"}


def test_tool_results_reach_the_model_as_untrusted_data() -> None:
    catalog = FakeCatalog()
    graph = build(catalog, parse_constraints("nut-free dinners for 2"))

    state = graph.invoke({"messages": [{"role": "user", "content": "nut-free dinners for 2"}]})

    tool_texts = [
        str(m.content)
        for m in state["messages"]
        if isinstance(m, ToolMessage) and m.name != "write_todos"
    ]
    assert tool_texts
    assert all(
        t.startswith("<untrusted_data>") and t.endswith("</untrusted_data>") for t in tool_texts
    )
    shown = [
        r
        for t in tool_texts
        for r in json.loads(
            t.removeprefix("<untrusted_data>").removesuffix("</untrusted_data>")
        ).get("results", [])
    ]
    assert all("Satay" not in r["title"] for r in shown)  # ruled out before the model sees it
