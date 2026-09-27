"""Short spoken fillers ("Let me think…") for when an answer needs a moment.

A filler plays when no answer audio is ready ``filler_after_ms`` after the customer stops
talking, or when Xana starts a tool call before saying anything (looking up an order takes a
round trip). Each is pre-synthesized when the service starts, so it plays with no speech-engine
delay. The choice is random, never the same line twice in a row, and at most one per turn so
Xana doesn't stall with filler after filler.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

GENERIC = (
    "Let me think.",
    "Hmm, let me think.",
    "One moment.",
    "Just a sec.",
    "Let me see.",
    "Okay, give me a second.",
    "Good question, one moment.",
)

# A filler that says what Xana is doing reads as competence, not stalling.
BY_TOOL: dict[str, tuple[str, ...]] = {
    "list_my_orders": (
        "Let me pull up your orders.",
        "Let me look at your orders.",
        "Checking your orders now.",
    ),
    "get_order_status": (
        "Let me check on that order.",
        "Let me look that order up.",
        "One sec, checking that order.",
    ),
    "get_return_options": ("Let me see what can be returned.", "Let me check the return options."),
    "quote_return": ("Let me price that return.", "Working out your refund now."),
    "propose_return": ("Here's what I've got.",),
    "get_refund_status": ("Let me check your refunds.", "Let me look at your refunds."),
    "search_policies": ("Let me check our policy.", "Let me look that up in our policies."),
    "list_stores": ("Let me find a store for you.",),
    "get_product_details": ("Let me check that item.",),
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
