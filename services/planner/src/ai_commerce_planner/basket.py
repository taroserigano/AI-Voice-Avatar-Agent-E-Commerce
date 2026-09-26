"""The basket check: code, not the model, decides what a proposed basket may contain.

Every line is re-read from the catalog (price, stock, tags, allergens), so a model that
misremembers a price or an allergen can't get it past this. Lines that break a rule are
dropped with a reason the shopper sees; the budget is checked on the item subtotal.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from ai_commerce_planner.catalog import CatalogPort, ProductFacts, VariantFacts
from ai_commerce_planner.constraints import Constraints

# Same rule as commerce's order pricing (seed/orders.py): $5.99 under $35 after discounts.
# An estimate only; commerce's cart estimate replaces it once it exists.
FREE_SHIPPING_MINOR = 3500
SHIPPING_MINOR = 599
MAX_QUANTITY = 12


class ProposedLine(BaseModel):
    """What the model proposes. Only IDs and a quantity: never a price."""

    product_id: uuid.UUID
    variant_id: uuid.UUID | None = Field(
        default=None, description="Omit to use the product's cheapest in-stock variant"
    )
    quantity: int = Field(default=1, ge=1, le=MAX_QUANTITY)
    reason: str = Field(default="", max_length=120, description='e.g. "Mon and Thu dinners"')


class BasketLine(BaseModel):
    product_id: uuid.UUID
    variant_id: uuid.UUID
    title: str
    variant_name: str
    image_path: str
    quantity: int
    unit_price_minor: int
    line_total_minor: int
    allergens: list[str]
    tags: list[str]
    reason: str


class ExcludedLine(BaseModel):
    title: str
    reason: str


class Basket(BaseModel):
    """The basket card. Every number here was computed by code from catalog data."""

    lines: list[BasketLine]
    excluded: list[ExcludedLine]
    subtotal_minor: int
    estimated_shipping_minor: int
    currency: str = "USD"
    budget_minor: int | None
    within_budget: bool | None
    over_budget_by_minor: int
    constraints: list[str]
    priced_at: datetime


def _variant(facts: ProductFacts, line: ProposedLine) -> tuple[VariantFacts | None, str | None]:
    if line.variant_id is not None:
        match = next((v for v in facts.variants if v.id == line.variant_id), None)
        return (match, None) if match else (None, "that option isn't sold")
    in_stock = [v for v in facts.variants if v.available > 0]
    if not in_stock:
        return None, "out of stock"
    return min(in_stock, key=lambda v: v.price_minor), None


def rule_violation(facts: ProductFacts, constraints: Constraints) -> str | None:
    """Why this product can't be in the basket, or None."""
    if constraints.exclude_allergens:
        if not facts.has_label:
            return "no allergen information"
        contains = sorted(set(facts.allergens) & set(constraints.exclude_allergens))
        if contains:
            return "contains " + ", ".join(contains)
    missing = [t for t in constraints.require_tags if t not in facts.tags]
    if missing:
        return "not " + ", ".join(t.replace("-", " ") for t in missing)
    unwanted = [t for t in constraints.exclude_tags if t in facts.tags]
    if unwanted:
        return ", ".join(t.replace("-", " ") for t in unwanted)
    return None


def check_basket(
    proposed: list[ProposedLine], catalog: CatalogPort, constraints: Constraints
) -> Basket:
    lines: list[BasketLine] = []
    excluded: list[ExcludedLine] = []
    seen: dict[uuid.UUID, BasketLine] = {}
    for p in proposed:
        facts = catalog.facts(p.product_id)
        if facts is None:
            excluded.append(ExcludedLine(title="Unknown item", reason="not in the catalog"))
            continue
        if reason := rule_violation(facts, constraints):
            excluded.append(ExcludedLine(title=facts.title, reason=reason))
            continue
        variant, problem = _variant(facts, p)
        if variant is None:
            excluded.append(ExcludedLine(title=facts.title, reason=problem or "unavailable"))
            continue
        if variant.id in seen:  # the same item twice: one line, quantities added
            prev = seen[variant.id]
            p = p.model_copy(update={"quantity": min(prev.quantity + p.quantity, MAX_QUANTITY)})
            lines.remove(prev)
        if variant.available < p.quantity:
            excluded.append(
                ExcludedLine(title=facts.title, reason=f"only {variant.available} in stock")
            )
            continue
        line = BasketLine(
            product_id=facts.id,
            variant_id=variant.id,
            title=facts.title,
            variant_name=variant.name,
            image_path=facts.image_path,
            quantity=p.quantity,
            unit_price_minor=variant.price_minor,
            line_total_minor=variant.price_minor * p.quantity,
            allergens=facts.allergens,
            tags=facts.tags,
            reason=p.reason,
        )
        seen[variant.id] = line
        lines.append(line)

    subtotal = sum(line.line_total_minor for line in lines)
    budget = constraints.budget_minor
    return Basket(
        lines=lines,
        excluded=excluded,
        subtotal_minor=subtotal,
        estimated_shipping_minor=0
        if not lines or subtotal >= FREE_SHIPPING_MINOR
        else SHIPPING_MINOR,
        budget_minor=budget,
        within_budget=None if budget is None else subtotal <= budget,
        over_budget_by_minor=0 if budget is None else max(0, subtotal - budget),
        constraints=constraints.labels(),
        priced_at=datetime.now(UTC),
    )
