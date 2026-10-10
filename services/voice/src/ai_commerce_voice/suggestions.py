"""Questions the customer can tap next, refreshed after every answer.

Built by rules from what's on the call, never by the model: the customer's own orders (an item
on its way, one they can still return) and what the last answer was about (products, an order,
a return quote, a policy, a store). Rules add no model call, so no delay and no cost, and a
suggestion can't promise something Xena can't do. Tapping one sends it as a typed question.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

SHOWN = 3

GENERAL = (
    "Do you have any oat milk?",
    "What's your return policy?",
    "Do you ship to Canada?",
    "How much is shipping?",
    "What are your customer service hours?",
    "Where's the nearest store?",
)

# What to ask next, by what the last answer used (first match wins).
AFTER_TOOL: tuple[tuple[frozenset[str], tuple[str, ...]], ...] = (
    (
        frozenset({"propose_return", "quote_return"}),
        (
            "Where can I drop it off?",
            "When will I get my refund?",
            "Do I need the original box?",
        ),
    ),
    (
        frozenset({"get_refund_status"}),
        (
            "When will the money show up?",
            "Where does the refund go?",
        ),
    ),
    (
        frozenset({"get_return_options"}),
        (
            "Start the return for me",
            "Where can I drop it off?",
        ),
    ),
    (
        frozenset({"get_order_status", "list_my_orders"}),
        (
            "What's the tracking number?",
            "Can I return it?",
        ),
    ),
    (
        frozenset({"get_product_reviews"}),
        (
            "Is it in stock?",
            "Is there a cheaper one?",
        ),
    ),
    (
        frozenset({"search_products", "get_product_details"}),
        (
            "Which one is the cheapest?",
            "What do reviewers say about it?",
            "Is it in stock?",
        ),
    ),
    (
        frozenset({"list_stores"}),
        (
            "What time does it close?",
            "Can I drop off a return there?",
        ),
    ),
    (
        frozenset({"search_policies"}),
        (
            "How do I start a return?",
            "How long do refunds take?",
        ),
    ),
    (frozenset({"handoff_to_person"}), ("When will they get back to me?",)),
)

# "1 × Tempo Athletics Grip Yoga Mat, $34.99 each (returnable now, until …) [carrier …]"
_ITEM = re.compile(r"^\d+\s*×\s*(?P<title>[^,(\[]+)")
_PERISHABLE = "quality problem"


def short_name(item: str) -> str | None:
    """'1 × Tempo Athletics Grip Yoga Mat, $34.99 each …' -> 'yoga mat': the last two words of
    the title, which name the kind of thing more often than the brand words before them."""
    m = _ITEM.match(item)
    if not m:
        return None
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", m.group("title"))
    if not words:
        return None
    return " ".join(words[-2:]).lower()


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", text.lower()).strip()


@dataclass
class Suggester:
    """Suggestions for one call. ``snapshot`` is the orders snapshot the prompt shows."""

    snapshot: list[dict[str, Any]] | None = None
    asked: set[str] = field(default_factory=set)
    _general_at: int = 0

    def _personal(self) -> list[str]:
        out: list[str] = []
        coming: str | None = None
        returnable: str | None = None
        for order in self.snapshot or []:
            for item in order.get("items") or []:
                name = short_name(str(item))
                if not name:
                    continue
                if coming is None and order.get("status") in ("In progress", "Preparing"):
                    coming = name
                if (
                    returnable is None
                    and order.get("status") == "Delivered"
                    and "returnable now" in str(item)
                    and _PERISHABLE not in str(item)
                ):
                    returnable = name
        if coming:
            out.append(f"When's my {coming} arriving?")
        if returnable:
            out.append(f"Can I return my {returnable}?")
        return out

    def _pick(self, *pools: Iterable[str]) -> list[str]:
        picked: list[str] = []
        seen: set[str] = set()
        for pool in pools:
            for q in pool:
                key = _norm(q)
                if key in self.asked or key in seen:
                    continue
                seen.add(key)
                picked.append(q)
                if len(picked) == SHOWN:
                    return picked
        return picked

    def _general(self) -> list[str]:
        # Rotate, so the general ones change from answer to answer.
        n = len(GENERAL)
        start = self._general_at % n
        self._general_at += 1
        return [GENERAL[(start + i) % n] for i in range(n)]

    def initial(self) -> list[str]:
        return self._pick(self._personal(), self._general())

    def after(self, question: str | None, tools: Iterable[str]) -> list[str]:
        """Suggestions once an answer is done: follow-ups for what it covered, then the
        customer's own orders, then general questions; never one they've already asked."""
        if question:
            self.asked.add(_norm(question))
        used = set(tools)
        follow: tuple[str, ...] = ()
        for names, questions in AFTER_TOOL:
            if used & names:
                follow = questions
                break
        return self._pick(follow[:2], self._personal(), self._general())
