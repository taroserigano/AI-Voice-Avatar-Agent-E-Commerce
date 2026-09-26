from __future__ import annotations

import pytest

from ai_commerce_planner.basket import ProposedLine, check_basket
from ai_commerce_planner.constraints import Constraints, parse_constraints
from tests.fakes import FakeCatalog, product


@pytest.mark.parametrize(
    ("goal", "budget", "allergens", "tags", "servings"),
    [
        ("A week of nut-free dinners for 4 under $80", 8000, ["peanuts", "tree nuts"], [], 4),
        (
            "dairy free and gluten-free lunches, budget of $45.50",
            4550,
            ["milk", "wheat"],
            ["gluten-free"],
            None,
        ),
        ("my son has a peanut allergy, snacks for 3", None, ["peanuts"], [], 3),
        ("peanut-free lunches", None, ["peanuts"], [], None),
        ("no nuts at all please", None, ["peanuts", "tree nuts"], [], None),
        ("vegan breakfasts for $30", 3000, ["egg", "fish", "milk", "shellfish"], ["vegan"], None),
        ("organic dinners", None, [], ["organic"], None),
    ],
)
def test_goal_rules_are_parsed_by_code(
    goal: str, budget: int | None, allergens: list[str], tags: list[str], servings: int | None
) -> None:
    c = parse_constraints(goal)
    assert (c.budget_minor, c.exclude_allergens, c.require_tags, c.servings) == (
        budget,
        allergens,
        tags,
        servings,
    )


def test_combining_rules_never_loosens_them() -> None:
    from_gateway = Constraints(budget_minor=6000, exclude_allergens=["sesame"])
    from_goal = parse_constraints("nut-free dinners under $80")

    both = from_gateway.tightened(from_goal)

    assert both.budget_minor == 6000
    assert both.exclude_allergens == ["peanuts", "sesame", "tree nuts"]


def test_basket_drops_lines_that_break_the_rules_and_says_why() -> None:
    catalog = FakeCatalog(
        [
            pesto := product("Basil pesto", "pasta-sauce", 499, allergens=("tree nuts",)),
            unlabeled := product("Mystery sauce", "pasta-sauce", 199, has_label=False),
            sold_out := product("Rare rice", "rice", 899, available=0),
            pasta := product("Pasta", "pasta", 218, allergens=("wheat",)),
        ]
    )
    rules = Constraints(exclude_allergens=["peanuts", "tree nuts"])

    basket = check_basket(
        [ProposedLine(product_id=p.id) for p in (pesto, unlabeled, sold_out, pasta)], catalog, rules
    )

    assert [ln.title for ln in basket.lines] == ["Pasta"]
    assert {(e.title, e.reason) for e in basket.excluded} == {
        ("Basil pesto", "contains tree nuts"),
        ("Mystery sauce", "no allergen information"),
        ("Rare rice", "out of stock"),
    }


def test_totals_come_from_the_catalog_and_budget_is_checked() -> None:
    chicken = product("Chicken", "chicken", 1147)
    rice = product("Rice", "rice", 299)
    catalog = FakeCatalog([chicken, rice])

    basket = check_basket(
        [
            ProposedLine(product_id=chicken.id, quantity=2),
            ProposedLine(product_id=rice.id, quantity=1),
            ProposedLine(product_id=rice.id, quantity=2),  # repeated: merged into one line
        ],
        catalog,
        Constraints(budget_minor=3000),
    )

    assert [(ln.title, ln.quantity, ln.line_total_minor) for ln in basket.lines] == [
        ("Chicken", 2, 2294),
        ("Rice", 3, 897),
    ]
    assert basket.subtotal_minor == 3191
    assert (basket.within_budget, basket.over_budget_by_minor) == (False, 191)
    assert basket.estimated_shipping_minor == 599  # $31.91 is under the $35 free-shipping line


def test_quantity_beyond_stock_is_excluded_not_trimmed() -> None:
    eggs = product("Eggs", "eggs", 399, available=2)
    basket = check_basket(
        [ProposedLine(product_id=eggs.id, quantity=5)], FakeCatalog([eggs]), Constraints()
    )
    assert basket.lines == []
    assert basket.excluded[0].reason == "only 2 in stock"


def test_required_tags_are_enforced() -> None:
    plain = product("Plain rice", "rice", 199)
    organic = product("Organic rice", "rice", 399, tags=("organic",))
    basket = check_basket(
        [ProposedLine(product_id=plain.id), ProposedLine(product_id=organic.id)],
        FakeCatalog([plain, organic]),
        Constraints(require_tags=["organic"]),
    )
    assert [ln.title for ln in basket.lines] == ["Organic rice"]
    assert basket.excluded[0].reason == "not organic"
