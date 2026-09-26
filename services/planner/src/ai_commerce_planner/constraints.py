"""What the shopper asked for, as rules code enforces: budget, allergens, tags, servings.

Constraints are parsed from the request by code before the model runs, and they are bound
into the basket check. The model can add to them (it may notice "no mushrooms"), but it can
never remove one, so a missed or ignored "nut-free" can't reach a basket.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

# The major US food allergens as the catalog labels them (products.details.allergens).
ALLERGENS = (
    "milk",
    "egg",
    "fish",
    "shellfish",
    "tree nuts",
    "peanuts",
    "wheat",
    "soy",
    "sesame",
)

# Shopper words -> label allergens they rule out. Order matters only for readability.
_ALLERGEN_WORDS: dict[str, tuple[str, ...]] = {
    # Word boundaries keep "peanut allergy" / "peanut-free" from matching the broader nut rules.
    r"\bnut[- ]?free|\bno nuts\b|\bwithout nuts\b|\bnut allerg\w*|tree[- ]nut allerg\w*": (
        "peanuts",
        "tree nuts",
    ),
    r"peanut[- ]?free|no peanuts?|peanut allerg\w*": ("peanuts",),
    r"dairy[- ]?free|no dairy|milk allerg\w*|without dairy": ("milk",),
    r"egg[- ]?free|no eggs?|egg allerg\w*": ("egg",),
    r"gluten[- ]?free|wheat[- ]?free|no gluten|no wheat|celiac|coeliac": ("wheat",),
    r"soy[- ]?free|no soy|soy allerg\w*": ("soy",),
    r"sesame[- ]?free|no sesame|sesame allerg\w*": ("sesame",),
    r"shellfish[- ]?free|no shellfish|shellfish allerg\w*": ("shellfish",),
    r"fish[- ]?free|no fish|fish allerg\w*": ("fish",),
    r"\bvegan\b": ("milk", "egg", "fish", "shellfish"),
}
# Shopper words -> catalog tags every item must carry.
_TAG_WORDS: dict[str, str] = {
    r"\bvegan\b": "vegan",
    r"gluten[- ]?free|celiac|coeliac": "gluten-free",
    r"\borganic\b": "organic",
    r"\bketo\b": "keto",
    r"\bkosher\b": "kosher",
    r"sugar[- ]?free|no sugar": "sugar-free",
    r"low[- ]sodium": "low-sodium",
}


class Constraints(BaseModel):
    budget_minor: int | None = Field(default=None, ge=0, description="Subtotal cap, cents")
    exclude_allergens: list[str] = Field(default_factory=list)
    require_tags: list[str] = Field(default_factory=list)
    exclude_tags: list[str] = Field(default_factory=list)
    servings: int | None = Field(default=None, ge=1, le=50)

    def tightened(self, other: Constraints) -> Constraints:
        """Both sets of rules at once (the stricter budget). Never loosens anything."""
        budgets = [b for b in (self.budget_minor, other.budget_minor) if b is not None]
        return Constraints(
            budget_minor=min(budgets) if budgets else None,
            exclude_allergens=sorted({*self.exclude_allergens, *other.exclude_allergens}),
            require_tags=sorted({*self.require_tags, *other.require_tags}),
            exclude_tags=sorted({*self.exclude_tags, *other.exclude_tags}),
            servings=self.servings or other.servings,
        )

    def labels(self) -> list[str]:
        """Plain words for the plan card, e.g. ["Under $80.00", "No peanuts or tree nuts"]."""
        out: list[str] = []
        if self.budget_minor is not None:
            out.append(f"Under ${self.budget_minor / 100:,.2f}")
        if self.exclude_allergens:
            out.append("No " + " or ".join(self.exclude_allergens) + " (per label)")
        out += [f"Must be {t.replace('-', ' ')}" for t in self.require_tags]
        if self.servings:
            out.append(f"{self.servings} people")
        return out


_MONEY = re.compile(
    r"(?:under|below|less than|max(?:imum)?|within|no more than|budget(?: of)?|for)?\s*"
    r"\$\s*(\d{1,4}(?:[.,]\d{2})?)"
)
_SERVINGS = re.compile(
    r"\bfor\s+(\d{1,2})\s*(?:people|persons|of us|adults|kids)?\b|\bfamily of\s+(\d{1,2})\b"
)


def parse_constraints(text: str) -> Constraints:
    lowered = text.lower()
    budget = None
    if m := _MONEY.search(lowered):
        budget = round(float(m.group(1).replace(",", ".")) * 100)
    servings = None
    for m in _SERVINGS.finditer(lowered):
        n = int(m.group(1) or m.group(2))
        # "for $80" is money, not people; "for 4" is people.
        if not lowered[max(0, m.start()) : m.end()].count("$"):
            servings = n
            break
    allergens = {
        a
        for pattern, found in _ALLERGEN_WORDS.items()
        if re.search(pattern, lowered)
        for a in found
    }
    tags = {tag for pattern, tag in _TAG_WORDS.items() if re.search(pattern, lowered)}
    return Constraints(
        budget_minor=budget,
        exclude_allergens=sorted(allergens),
        require_tags=sorted(tags),
        servings=servings,
    )
