"""The planner's tools. Read-only catalog access plus two deterministic basket checks.

Tools are built per request with the customer's catalog client and constraints already
bound, so the model never passes an identity and can't change the rules. There is no
cart write, order, return, payment, or handoff tool here: "Add all" is the shopper's click,
sent from the browser straight to the commerce API.

Everything a tool returns to the model is catalog data wrapped as untrusted content:
product text is written by sellers and may contain instructions, which the prompt says to
ignore.
"""

from __future__ import annotations

import json
from typing import Annotated, Any

from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool, InjectedToolCallId, tool
from langgraph.types import Command
from pydantic import BaseModel, Field

from ai_commerce_planner.basket import Basket, ProposedLine, check_basket, rule_violation
from ai_commerce_planner.catalog import CatalogPort
from ai_commerce_planner.constraints import Constraints

FACTS_PER_SEARCH = 8
TOOL_NAMES = ("search_products", "check_basket", "propose_basket")


def untrusted(payload: Any) -> str:
    return (
        "<untrusted_data>\n"
        + json.dumps(payload, ensure_ascii=False, default=str)
        + "\n</untrusted_data>"
    )


class SearchArgs(BaseModel):
    text: str | None = Field(default=None, max_length=120, description='e.g. "chicken thighs"')
    product_types: list[str] | None = Field(
        default=None, max_length=8, description='Catalog types, e.g. ["pasta", "pasta-sauce"]'
    )
    tags: list[str] | None = Field(default=None, max_length=5, description='e.g. ["organic"]')
    max_price_cents: int | None = Field(default=None, ge=0)


class BasketArgs(BaseModel):
    lines: list[ProposedLine] = Field(min_length=1, max_length=40)


class ProposeArgs(BasketArgs):
    summary: str = Field(max_length=400, description="One or two sentences for the shopper")


def _basket_digest(basket: Basket) -> dict[str, Any]:
    return {
        "items": [
            {
                "product_id": str(ln.product_id),
                "title": ln.title,
                "qty": ln.quantity,
                "line_total_cents": ln.line_total_minor,
            }
            for ln in basket.lines
        ],
        "excluded": [e.model_dump() for e in basket.excluded],
        "subtotal_cents": basket.subtotal_minor,
        "budget_cents": basket.budget_minor,
        "within_budget": basket.within_budget,
        "over_budget_by_cents": basket.over_budget_by_minor,
    }


def build_tools(catalog: CatalogPort, constraints: Constraints) -> list[BaseTool]:
    @tool("search_products", args_schema=SearchArgs)
    def search_products(
        text: str | None = None,
        product_types: list[str] | None = None,
        tags: list[str] | None = None,
        max_price_cents: int | None = None,
    ) -> str:
        """Find in-stock products. Results already respect the shopper's rules (allergens,
        required tags); items that break them are counted, not shown."""
        hits = catalog.search(
            text=text,
            product_types=product_types,
            tags=sorted({*(tags or []), *constraints.require_tags}),
            exclude_tags=constraints.exclude_tags,
            max_price_minor=max_price_cents,
            limit=FACTS_PER_SEARCH * 2,
        )
        shown: list[dict[str, Any]] = []
        ruled_out = 0
        for hit in hits:
            if len(shown) >= FACTS_PER_SEARCH:
                break
            facts = catalog.facts(hit.id)
            if facts is None or rule_violation(facts, constraints):
                ruled_out += 1
                continue
            cheapest = min(
                (v for v in facts.variants if v.available > 0),
                key=lambda v: v.price_minor,
                default=None,
            )
            if cheapest is None:
                continue
            shown.append(
                {
                    "product_id": str(facts.id),
                    "title": facts.title,
                    "type": facts.product_type,
                    "tags": facts.tags,
                    "allergens": facts.allergens,
                    "price_cents": cheapest.price_minor,
                    "option": cheapest.name,
                }
            )
        return untrusted({"results": shown, "ruled_out_by_shopper_rules": ruled_out})

    @tool("check_basket", args_schema=BasketArgs)
    def check_basket_tool(lines: list[ProposedLine]) -> str:
        """Price a draft basket from the catalog and check it against the shopper's rules
        and budget. Use it before proposing; it changes nothing."""
        return untrusted(_basket_digest(check_basket(lines, catalog, constraints)))

    @tool("propose_basket", args_schema=ProposeArgs)
    def propose_basket(
        lines: list[ProposedLine],
        summary: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command[Any]:
        """Show the final basket to the shopper. Call once, at the end. The shopper adds it
        to their cart themselves."""
        basket = check_basket(lines, catalog, constraints)
        return Command(
            update={
                "basket": basket.model_dump(mode="json"),
                "basket_summary": summary,
                "messages": [
                    ToolMessage(untrusted(_basket_digest(basket)), tool_call_id=tool_call_id)
                ],
            }
        )

    return [search_products, check_basket_tool, propose_basket]
