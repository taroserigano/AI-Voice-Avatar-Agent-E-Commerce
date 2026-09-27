"""The scripted model's support flow (Xana), used when no working LLM key is configured.

A return takes several tool calls in one turn, as a real model would make them:
``list_my_orders`` (find the item) → ``get_return_options`` (is it eligible?) → ``quote_return``
(price it) → ``propose_return`` (pause for the customer's own confirmation). Each step is
decided from the previous tool's result; the answer is written only from tool results.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Sequence
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage

RETURN_WORDS = re.compile(
    r"\b(return|send (it|this|them|.+?) back|refund me|went bad|gone bad|spoiled|sour|moldy|"
    r"broken|cracked|smashed|damaged|defective|stopped working|(doesn't|don't) work|wrong (item|size|color))\b"
)
REFUND_STATUS_WORDS = re.compile(
    r"\b(where('s| is) my refund|refund status|status of my (return|refund)|(haven't|didn't) (got|gotten|get|received) my refund|my returns?)\b"
)
# An order number as the site shows it (tools.order_number): 8 hex characters, uppercase.
# After the word "order" any case is accepted ("order #e2ea6bc6"); on its own it must look like
# the site's form (uppercase, with a digit and a letter), so ordinary words and dates never match.
ORDER_NUMBER = re.compile(
    r"\border\s*(?:number|no\.?|#)?\s*#?\s*([0-9a-fA-F]{8})\b"
    r"|\b((?=[0-9A-F]*[0-9])(?=[0-9A-F]*[A-F])[0-9A-F]{8})\b"
)
CASE_REFERENCE = re.compile(r"\b(CS-\d{3,})\b")
NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "a": 1, "an": 1}
STOP = {
    "the",
    "my",
    "a",
    "an",
    "these",
    "those",
    "this",
    "that",
    "it",
    "them",
    "from",
    "order",
    "please",
    "want",
    "return",
    "to",
    "i",
    "some",
    "of",
    "all",
    "both",
    "back",
    "send",
    "refund",
    "for",
    "and",
    "last",
    "week",
    "yesterday",
    "got",
    "get",
}


def _call(name: str, args: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "args": args, "id": f"call_{uuid.uuid4().hex[:12]}", "type": "tool_call"}


def _stem(word: str) -> str:
    return word[:-1] if word.endswith("s") and len(word) > 3 else word


def item_words(text: str) -> list[str]:
    """The item the customer names: 'I want to return my earbuds' -> ['earbud']."""
    t = text.lower()
    m = re.search(
        r"\b(?:return|send back|refund for)\s+(?:all\s+|both\s+|\d+\s+|one\s+|two\s+|three\s+)?(?:of\s+)?(?:my|the|these|those|this|that)?\s*(.+?)(?:\s+(?:from|because|since|please|in my|that|which)\b|[.,!?]|$)",
        t,
    )
    if not m:
        m = re.search(
            r"\b(?:the|my)\s+(.+?)\s+(?:from|went|was|were|is|are|arrived|came|stopped|doesn't|don't|won't)\b",
            t,
        )
    phrase = m.group(1) if m else ""
    return [_stem(w) for w in re.findall(r"[a-z]+", phrase) if w not in STOP]


def quantity(text: str, returnable: int) -> int:
    t = text.lower()
    if re.search(r"\b(all|both|every|everything)\b", t):
        return returnable
    m = re.search(r"\b(\d+)\b", t)
    if m:
        return max(1, min(int(m.group(1)), returnable))
    for word, n in NUMBER_WORDS.items():
        if re.search(rf"\b{word}\s+(of\s+)?(the|my)\b", t) and n > 1:
            return min(n, returnable)
    return 1


def _payload(m: ToolMessage) -> dict[str, Any]:
    from assistant.scripted import read_payload

    return read_payload(str(m.content))


def _latest(results: Sequence[ToolMessage], name: str) -> dict[str, Any] | None:
    for m in reversed(results):
        if m.name == name:
            return _payload(m)
    return None


def matching_lines(orders: dict[str, Any], words: list[str]) -> list[dict[str, Any]]:
    out = []
    for order in orders.get("orders", []):
        for item in order.get("items", []):
            title = {_stem(w) for w in re.findall(r"[a-z]+", item["title"].lower())}
            if words and all(w in title for w in words):
                out.append(
                    {
                        **item,
                        "order_id": order["order_id"],
                        "order_number": order["order_number"],
                        "delivered_at": order.get("delivered_at"),
                        "status": order.get("status"),
                    }
                )
    return out


def wants_return(text: str, signals: dict[str, Any]) -> bool:
    intent = signals.get("intent") or {}
    if intent.get("act") and intent.get("value") == "start_return":
        return True
    return bool(RETURN_WORDS.search(text.lower())) and not re.search(
        r"\b(how long|policy|can i return a|do i get|what if)\b", text.lower()
    )


def named_order_number(text: str) -> str | None:
    """The order number the customer names ("about order E2EA6BC6"), uppercase, or None."""
    m = ORDER_NUMBER.search(text)
    return (m.group(1) or m.group(2)).upper() if m else None


def plan_support(text: str, signals: dict[str, Any]) -> list[dict[str, Any]] | None:
    """The first tool call for a support request, or None to use the general plan."""
    t = text.lower()
    if REFUND_STATUS_WORDS.search(t):
        return [_call("get_refund_status", {})]
    if wants_return(text, signals):
        words = item_words(text)
        return [_call("list_my_orders", {"contains": " ".join(words)} if words else {})]
    if number := named_order_number(text):
        # "Where's order E2EA6BC6?" is about that order, not the recent ones. The tool finds it
        # among this customer's own orders (the number is resolved server-side).
        return [_call("get_order_status", {"order_number": number})]
    return None


def describe_order_status(data: dict[str, Any]) -> str:
    """One order's status and delivery in plain words, only from get_order_status's output."""
    number = data.get("order_number", "")
    items = data.get("items") or []
    what = ""
    if items:
        what = f" ({items[0]['title']}" + (f" and {len(items) - 1} more" if len(items) > 1 else "")
        what += ")"
    head = f"Order #{number}{what}"
    low = f"order #{number}{what}"
    d = data.get("delivery") or {}
    status = data.get("status")
    carrier = f"{d['carrier']} {d['service']}".strip() if d.get("carrier") else ""
    tracking = f" Tracking number {d['tracking_number']}." if d.get("tracking_number") else ""
    latest = f" Latest update: {d['latest_update']}." if d.get("latest_update") else ""
    arriving = d.get("arriving_by") or data.get("arriving_by")
    if status == "Canceled":
        return f"{head} was canceled, so nothing will ship."
    delivered = d.get("delivered_on") or data.get("delivered_on")
    if status == "Delivered" or d.get("status") == "Delivered":
        via = f" by {d['carrier']}" if d.get("carrier") else ""
        return f"{head} was delivered{via}" + (f" on {delivered}." if delivered else ".")
    if d.get("status") == "Delivery problem":
        return (
            f"There's a problem with the delivery of {low}"
            + (f": {d['latest_update']}." if d.get("latest_update") else ".")
            + f"{tracking} I can open a case for our team if you'd like."
        )
    if d.get("status") == "Out for delivery":
        eta = f" and should arrive by {arriving}" if arriving else ""
        return f"{head} is out for delivery with {carrier}{eta}.{tracking}"
    if d.get("status") == "In transit":
        eta = f" and should arrive by {arriving}" if arriving else ""
        return f"{head} is on its way with {carrier}{eta}.{latest}{tracking}"
    eta = f" It's estimated to arrive {arriving}." if arriving else ""
    ship = (
        f" {carrier} has the label; it hasn't been picked up yet."
        if carrier
        else " We'll share tracking as soon as it ships."
    )
    return f"We're getting {low} ready.{eta}{ship}"


def next_support_step(
    text: str, results: Sequence[ToolMessage], signals: dict[str, Any]
) -> list[dict[str, Any]] | None:
    """After tool results in a return flow, the next tool call, or None to answer."""
    if not wants_return(text, signals) or not results:
        return None
    last = results[-1]
    words = item_words(text)
    if last.name == "list_my_orders":
        lines = matching_lines(_payload(last), words)
        if len({ln["line_id"] for ln in lines}) == 1:
            return [_call("get_return_options", {"order_id": lines[0]["order_id"]})]
        return None  # none or several: ask
    if last.name == "get_return_options":
        opts = _payload(last)
        orders = _latest(results, "list_my_orders") or {}
        wanted = {ln["line_id"] for ln in matching_lines(orders, words)}
        line = next((ln for ln in opts.get("lines", []) if ln["order_line_id"] in wanted), None)
        if line and line["eligible"]:
            qty = quantity(text, int(line["returnable_quantity"]))
            return [
                _call(
                    "quote_return",
                    {
                        "order_id": opts["order_id"],
                        "lines": [{"order_line_id": line["order_line_id"], "quantity": qty}],
                    },
                )
            ]
        return None
    if last.name == "quote_return":
        quote = _payload(last)
        if quote.get("quote_id"):
            return [_call("propose_return", {"quote_id": quote["quote_id"]})]
    return None


def compose_support(results: Sequence[ToolMessage], text: str) -> str | None:
    """Answers for the support tools, or None when another composer should answer."""
    if not results:
        return None
    last = results[-1]
    data = _payload(last)
    words = item_words(text)
    if last.name == "list_my_orders" and wants_return(text, {}):
        lines = matching_lines(data, words)
        if not lines:
            what = " ".join(words) or "that"
            return (
                f"I couldn't find {what} in your recent orders. Which order is it from? "
                "You can pick one from the cards."
            )
        if len({ln["line_id"] for ln in lines}) > 1:
            options = "; ".join(
                f"{ln['title']} from order {ln['order_number']}" for ln in lines[:4]
            )
            return f"I found more than one: {options}. Which one do you want to return?"
    if last.name == "get_return_options":
        orders = _latest(results, "list_my_orders") or {}
        wanted = {ln["line_id"] for ln in matching_lines(orders, words)}
        line = next((ln for ln in data.get("lines", []) if ln["order_line_id"] in wanted), None)
        if line and not line["eligible"]:
            return f"I'm sorry, the {line['title']} can't be returned. {line['explanation']}"
    if last.name == "quote_return" and "error" in data:
        problems = data.get("problems") or []
        if problems and problems[0]["reason"] == "perishable_reason":
            return (
                "I can refund fresh food when there's a problem with it. What was wrong: was it "
                "damaged, spoiled, or past its date?"
            )
        if problems:
            return f"I can't return that as asked. {problems[0]['explanation']}"
        return "I couldn't price that return just now. Please try again."
    if last.name == "propose_return":
        outcome = data.get("outcome")
        if outcome == "confirmed":
            ship = (
                " Your return label is on the screen; drop the package with the carrier or at "
                "any Larkspur store."
                if data.get("needs_shipping")
                else " There's nothing to send back."
            )
            return (
                f"Done. Return {data.get('rma_number')} is confirmed, and {data.get('refund')} "
                f"goes back to {data.get('refund_to')}.{ship}"
            )
        if outcome == "declined":
            return "No problem, nothing was returned. Is there anything you'd like to change?"
        if outcome == "expired":
            return "That quote expired before it was confirmed. Want me to price it again?"
        if outcome == "superseded":
            return ""
        if "error" in data:
            return "I couldn't show that quote just now. Please try again."
    if last.name == "get_order_status":
        case = CASE_REFERENCE.search(text)
        about = f"About your request {case.group(1)}: " if case else ""
        if "error" in data:
            number = named_order_number(text)
            if data.get("status") == 404 and number:
                return (
                    f"{about}I couldn't find order {number} on your account. Please check the "
                    "number on your Orders page, or ask me about your recent orders."
                )
            return None  # the general "couldn't get that" answer
        return about + describe_order_status(data)
    if last.name == "get_refund_status":
        returns = data.get("returns", [])
        if not returns:
            return "You don't have any returns yet."
        parts = []
        for r in returns[:3]:
            refund = r.get("refund")
            money_part = (
                f"refund {refund['status']} ({refund['amount']})"
                if refund
                else "refund not issued yet"
            )
            parts.append(
                f"Return {r['rma_number']} ({', '.join(r['items'][:2])}) is {r['status'].replace('_', ' ')}, {money_part}."
            )
        return " ".join(parts)
    return None


def last_human_text(messages: Sequence[BaseMessage]) -> str:
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            return str(m.content)
    return ""
