"""Short spoken fillers ("Let me think…") for when an answer needs a moment.

A filler plays when no answer audio is ready ``filler_after_ms`` after the customer stops
talking; when she's started a tool call by then, the line says what she's doing. Each is
pre-synthesized when the service starts, so it plays with no speech-engine delay. The choice
is random, never the same line twice in a row, and at most one per turn so Xena doesn't stall
with filler after filler.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

# Upbeat, but safe before bad news too: a filler is picked before the answer is known, so
# nothing here jokes or celebrates ("Great question!" would jar before "it arrived broken").
GENERIC = (
    "One moment!",
    "Sure thing, one sec.",
    "On it!",
    "Let me take a look.",
    "Let me see.",
    "Just a sec!",
    "Happy to check, one moment.",
)

# A filler that says what Xena is doing reads as competence, not stalling.
BY_TOOL: dict[str, tuple[str, ...]] = {
    "list_my_orders": (
        "Sure, pulling up your orders!",
        "Let me pull up your orders.",
        "On it, checking your orders.",
    ),
    "get_order_status": (
        "Let me check on that order!",
        "Let me look that order up.",
        "One sec, checking that order.",
    ),
    "get_return_options": ("Let me see what can go back.", "Let me check the return options."),
    "quote_return": ("Let me price that return.", "Working out your refund now."),
    "propose_return": ("Here's what I've got.",),
    "get_refund_status": ("Let me check your refunds.", "Let me look at your refunds."),
    "search_policies": ("Let me check our policy.", "Let me look that up in our policies."),
    "list_stores": ("Let me find a store for you!",),
    "get_product_details": ("Let me check that item!",),
    "get_product_reviews": ("Let me see what reviewers say.", "Let me check the reviews!"),
    "get_my_cart": ("Let me peek at your cart.", "Let me check your cart."),
    "list_my_support_cases": ("Let me pull up your cases.", "Let me check your support cases."),
    "get_my_account_activity": ("Let me check your recent activity.",),
    "handoff_to_person": ("Let me get a person to help.",),
}


def all_phrases() -> list[str]:
    seen: dict[str, None] = dict.fromkeys(GENERIC)
    for phrases in BY_TOOL.values():
        seen.update(dict.fromkeys(phrases))
    return list(seen)


@dataclass
class FillerPicker:
    rng: random.Random = field(default_factory=random.Random)
    last: str | None = None

    def pick(self, tool: str | None = None) -> str:
        options = [p for p in BY_TOOL.get(tool or "", GENERIC) if p != self.last] or list(GENERIC)
        choice = self.rng.choice(options)
        self.last = choice
        return choice
