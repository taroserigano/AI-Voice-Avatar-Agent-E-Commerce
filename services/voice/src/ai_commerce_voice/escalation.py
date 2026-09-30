"""When a voice turn moves from gpt-6-luna to gpt-6-sol (decision 26: code decides, never the
model). Plan: docs/features/09-xana-voice-v2/PLAN.md, "Luna → Sol escalation".

Luna answers most turns fast. Sol answers a turn when any of these hold:

- ``dispute``: something arrived damaged, wrong, or missing, a refund is missing, or a charge
  is in question.
- ``repeat``: the customer says the last answer was wrong, or asks the same thing again.
- ``tool_errors``: two tools failed in this turn (decided in the agent node, mid-turn).

Measured and left out (evals/xana, 2026-09-30): escalating every return, refund, or policy
question (185 of 413 golden-set turns) scored the same as Luna alone (voice returns 188/198
both ways, products 198 vs 197 of 200) at the same speed (median first words 2.29 s vs 2.32 s),
and Sol costs more. Sol fixed some of Luna's misses and made others. The plan's
more-than-two-items rule isn't built: the item count isn't known until the model has quoted.
"""

from __future__ import annotations

import difflib
import re

from langchain_core.messages import AnyMessage, HumanMessage, ToolMessage

DISPUTE = re.compile(
    r"\b(?:damaged|broken|cracked|leak(?:ing|ed)?|defective|wrong (?:item|size|color|one)|"
    r"missing|never (?:arrived|came|got)|didn['’]?t (?:arrive|come|get)|not here|stolen|"
    r"(?:double|over)[- ]?charged|charged (?:twice|me)|charge on my|dispute|chargeback|"
    r"where(?:['’]s| is) my refund|no refund|"
    r"haven['’]?t (?:got|gotten|received) (?:my|the) refund)\b",
    re.IGNORECASE,
)
WRONG = re.compile(
    r"\b(?:that['’]?s (?:not right|wrong|incorrect)|you['’]?re wrong|that isn['’]?t right|"
    r"not what I (?:asked|said|meant)|I (?:already|just) (?:said|told you|asked)|"
    r"no,? I (?:said|meant|asked)|you (?:didn['’]?t|did not) (?:answer|listen))\b",
    re.IGNORECASE,
)
TOOL_ERRORS = 2


def _customer_turns(messages: list[AnyMessage]) -> list[str]:
    return [str(m.content) for m in messages if isinstance(m, HumanMessage)]


def escalation_reason(text: str, history: list[AnyMessage]) -> str | None:
    """Why this customer turn goes to the stronger model, or None."""
    if WRONG.search(text):
        return "repeat"
    earlier = _customer_turns(history)
    if earlier and difflib.SequenceMatcher(None, earlier[-1].lower(), text.lower()).ratio() > 0.85:
        return "repeat"
    if DISPUTE.search(text):
        return "dispute"
    return None


def tool_errors_this_turn(messages: list[AnyMessage]) -> int:
    """Failed tool results since the customer's latest message."""
    count = 0
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            break
        if isinstance(m, ToolMessage) and (
            m.status == "error" or '"error":' in str(m.content)[:400]
        ):
            count += 1
    return count
