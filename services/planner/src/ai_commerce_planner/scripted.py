"""The labeled scripted planner: a stand-in chat model with no LLM behind it.

It drives the same deep-agent graph, tools, and basket check as the real model, so the
demo and tests exercise everything except the model's judgment. It reads the goal with
simple rules (meal type, days, people), searches by catalog type, keeps the cheapest
results that pass the shopper's rules, trims to budget, and proposes. Every run it drives is
reported as ``simulated``.
"""

from __future__ import annotations

import json
import math
import re
from typing import Any

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult

# What goes into a meal, as catalog product types, cheapest first within each slot.
MEALS: dict[str, list[tuple[str, list[str]]]] = {
    "dinner": [
        ("protein", ["chicken", "ground-turkey", "ground-beef", "pork", "salmon", "fish"]),
        ("starch", ["pasta", "rice", "tortillas", "potatoes", "grains"]),
        ("vegetable", ["frozen-vegetables", "salad-greens", "peppers", "onions", "tomatoes"]),
        ("sauce", ["pasta-sauce", "canned-tomatoes", "broth", "salad-dressing"]),
    ],
    "breakfast": [
        ("main", ["eggs", "oatmeal", "cereal", "yogurt", "granola"]),
        ("bread", ["bread", "bagels", "english-muffins", "tortillas"]),
        ("fruit", ["berries", "apples", "citrus", "cut-fruit", "frozen-fruit"]),
        ("drink", ["milk", "plant-milk"]),
    ],
    "lunch": [
        ("filling", ["deli-meat", "canned-fish", "cheese", "peanut-butter", "canned-beans"]),
        ("bread", ["bread", "tortillas", "buns"]),
        ("side", ["salad-greens", "cut-fruit", "soup", "apples"]),
    ],
}
_UNTRUSTED = re.compile(r"</?untrusted_data>")


def _goal(messages: list[BaseMessage]) -> str:
    human = [m for m in messages if isinstance(m, HumanMessage)]
    return str(human[0].content) if human else ""


def meal_of(goal: str) -> str:
    g = goal.lower()
    return next((m for m in ("breakfast", "lunch", "dinner") if m in g), "dinner")


def days_of(goal: str) -> int:
    g = goal.lower()
    if m := re.search(r"(\d{1,2})\s*(?:days|dinners|lunches|breakfasts|nights|meals)", g):
        return max(1, min(int(m.group(1)), 14))
    return 7 if "week" in g else 3


def _tool_payload(msg: ToolMessage) -> Any:
    try:
        return json.loads(_UNTRUSTED.sub("", str(msg.content)))
    except json.JSONDecodeError:
        return {}


class ScriptedPlannerModel(BaseChatModel):
    """Rule-based stand-in for the planner LLM. Stateless: each step is derived from the
    conversation so far, like a real model's."""

    servings: int = 4

    @property
    def _llm_type(self) -> str:
        return "scripted-planner"

    def bind_tools(self, tools: Any, **kwargs: Any) -> ScriptedPlannerModel:
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        return ChatResult(generations=[ChatGeneration(message=self._next(messages))])

    def _next(self, messages: list[BaseMessage]) -> AIMessage:
        goal = _goal(messages)
        meal = meal_of(goal)
        slots = MEALS[meal]
        called = [tc["name"] for m in messages if isinstance(m, AIMessage) for tc in m.tool_calls]
        results = {m.tool_call_id: m for m in messages if isinstance(m, ToolMessage)}

        if "write_todos" not in called:
            return self._calls(
                "plan",
                [("write_todos", {"todos": self._todos(meal, goal, done=0)})],
            )
        if "search_products" not in called:
            return self._calls(
                "search",
                [("search_products", {"product_types": types}) for _, types in slots],
            )
        if "check_basket" not in called:
            lines = self._draft(messages, results, meal, goal)
            if not lines:
                return AIMessage(
                    content="I couldn't find products that match all of your rules, so I "
                    "didn't build a basket. Try loosening a rule or a different budget."
                )
            return self._calls(
                "check",
                [
                    ("write_todos", {"todos": self._todos(meal, goal, done=2)}),
                    ("check_basket", {"lines": lines}),
                ],
            )
        if "propose_basket" not in called:
            lines = self._last_args(messages, "check_basket")["lines"]
            check = self._result_of(messages, results, "check_basket")
            lines = self._fit_budget(lines, check)
            return self._calls(
                "propose",
                [
                    ("write_todos", {"todos": self._todos(meal, goal, done=5)}),
                    (
                        "propose_basket",
                        {"lines": lines, "summary": f"Ingredients for {days_of(goal)} {meal}s."},
                    ),
                ],
            )
        proposal = self._result_of(messages, results, "propose_basket")
        left_out = proposal.get("excluded") or []
        note = (
            " I left out " + "; ".join(f"{e['title']} ({e['reason']})" for e in left_out) + "."
            if left_out
            else ""
        )
        return AIMessage(
            content=f"Here's a basket for {days_of(goal)} {meal}s using items that match your "
            f"rules.{note} Allergen information comes from product labels, so please check each "
            "package."
        )

    # --- steps ---------------------------------------------------------------------------

    @staticmethod
    def _calls(step: str, calls: list[tuple[str, dict[str, Any]]]) -> AIMessage:
        return AIMessage(
            content="",
            tool_calls=[
                {"name": name, "args": args, "id": f"scripted_{step}_{i}", "type": "tool_call"}
                for i, (name, args) in enumerate(calls)
            ],
        )

    @staticmethod
    def _todos(meal: str, goal: str, done: int) -> list[dict[str, str]]:
        steps = [
            f"Pick {days_of(goal)} {meal} ideas",
            "Find ingredients that match your rules",
            "Check prices and stock",
            "Fit to your budget",
            "Build your basket",
        ]
        return [
            {
                "content": s,
                "status": "completed" if i < done else ("in_progress" if i == done else "pending"),
            }
            for i, s in enumerate(steps)
        ]

    def _draft(
        self,
        messages: list[BaseMessage],
        results: dict[str, ToolMessage],
        meal: str,
        goal: str,
    ) -> list[dict[str, Any]]:
        days = days_of(goal)
        # Two different options per slot for variety; enough units for the days and people.
        per_slot = 2 if days >= 4 else 1
        qty = max(1, math.ceil(days * self.servings / (per_slot * 8)))
        lines: list[dict[str, Any]] = []
        for msg in messages:
            if not isinstance(msg, AIMessage):
                continue
            for tc in msg.tool_calls:
                if tc["name"] != "search_products" or tc["id"] not in results:
                    continue
                found = _tool_payload(results[tc["id"]]).get("results") or []
                for item in sorted(found, key=lambda r: r["price_cents"])[:per_slot]:
                    lines.append(
                        {"product_id": item["product_id"], "quantity": qty, "reason": f"{meal}s"}
                    )
        return lines

    @staticmethod
    def _last_args(messages: list[BaseMessage], name: str) -> dict[str, Any]:
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                for tc in msg.tool_calls:
                    if tc["name"] == name:
                        return dict(tc["args"])
        return {}

    @staticmethod
    def _result_of(
        messages: list[BaseMessage], results: dict[str, ToolMessage], name: str
    ) -> dict[str, Any]:
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                for tc in msg.tool_calls:
                    if tc["name"] == name and tc["id"] in results:
                        payload = _tool_payload(results[tc["id"]])
                        return payload if isinstance(payload, dict) else {}
        return {}

    @staticmethod
    def _fit_budget(lines: list[dict[str, Any]], check: dict[str, Any]) -> list[dict[str, Any]]:
        """Lower quantities, then drop the priciest lines, until the checked subtotal fits.

        Works from the check's own prices (catalog data). Lines the check left out are
        dropped here too."""
        over = check.get("over_budget_by_cents") or 0
        unit = {
            item["product_id"]: item["line_total_cents"] / max(item["qty"], 1)
            for item in check.get("items") or []
        }
        priced = [
            {**line, "_unit": unit[line["product_id"]]}
            for line in lines
            if line["product_id"] in unit
        ]
        while over > 0:
            biggest = max(
                (p for p in priced if p["quantity"] > 1), key=lambda p: p["_unit"], default=None
            )
            if biggest is not None:
                biggest["quantity"] -= 1
                over -= biggest["_unit"]
                continue
            if len(priced) <= 1:
                break
            drop = max(priced, key=lambda p: p["_unit"])
            priced.remove(drop)
            over -= drop["_unit"]
        return [{k: v for k, v in p.items() if k != "_unit"} for p in priced]
