"""Return and refund tools (Xana): eligibility, a priced quote, and a paused proposal.

The model can look up what's returnable and ask the commerce API to price a return. It can
then *propose* the quote: ``propose_return`` pauses the conversation (LangGraph ``interrupt``)
and the customer's browser shows the quote with a Confirm button. Only the browser (or the
app's voice-confirmation step) confirms, directly with the commerce API, using a single-use
token the assistant never sees. The conversation resumes with the outcome, which this tool
verifies with the commerce API rather than trusting the resume message.

There is no tool that confirms, refunds, or cancels.
"""

from __future__ import annotations

import uuid
from typing import Any, Literal

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.types import interrupt
from pydantic import BaseModel, Field

from assistant.commerce import CommerceError
from assistant.tools import ctx_from, money, untrusted

TIMING_WORDS = {
    "instant": "as soon as the carrier or a Larkspur store scans your package",
    "after_receipt": "once our warehouse receives it",
    "after_inspection": "after our warehouse inspects it, usually 3 to 5 business days "
    "after it arrives",
    "no_return_needed": "right away, with nothing to send back",
}
REASONS = Literal[
    "damaged",
    "defective",
    "wrong_item",
    "not_as_described",
    "spoiled_or_expired",
    "missing_parts",
    "no_longer_needed",
    "better_price",
    "arrived_late",
    "other",
]


def _error(source: str, exc: CommerceError) -> tuple[str, list[dict[str, Any]]]:
    payload: dict[str, Any] = {"error": exc.detail, "status": exc.status}
    if exc.problems:
        payload["problems"] = [
            {"reason": p["reason"], "explanation": p["message"]} for p in exc.problems
        ]
    return untrusted(source, payload), []


def destination_words(dest: dict[str, Any] | None) -> str:
    if not dest:
        return "your original payment method"
    brand = (dest.get("card_brand") or "card").title()
    last4 = dest.get("card_last4")
    return f"your {brand} ending in {last4}" if last4 else "your original payment method"


def readback(quote: dict[str, Any]) -> str:
    """The exact words read to the customer before they confirm. Built by code from the quote,
    never by the model, so what's read is what's confirmed."""
    items = "; ".join(
        f"{ln['quantity']} × {ln['product_title']}"
        + (f" ({ln['variant_name']})" if ln["variant_name"] else "")
        for ln in quote["lines"]
    )
    timings = {ln["refund_timing"] for ln in quote["lines"]}
    when = TIMING_WORDS[timings.pop()] if len(timings) == 1 else "as each item reaches its step"
    shipping = (
        f", including {money(quote['shipping_refund_minor'])} shipping"
        if quote["shipping_refund_minor"]
        else ""
    )
    return (
        f"Here's your return: {items}. "
        f"You'll get {money(quote['total_refund_minor'])} back{shipping}, "
        f"to {destination_words(quote.get('refund_destination'))}, {when}. "
        "Do you want me to confirm this return?"
    )


def quote_card(quote: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "return_quote",
        "quote_id": quote["id"],
        "order_id": quote["order_id"],
        "status": quote["status"],
        "lines": [
            {
                "order_line_id": ln["order_line_id"],
                "title": ln["product_title"],
                "variant_name": ln["variant_name"],
                "image_path": ln["image_path"],
                "quantity": ln["quantity"],
                "refund_minor": ln["refund_minor"],
                "refund_timing": ln["refund_timing"],
                "timing_message": ln["timing_message"],
            }
            for ln in quote["lines"]
        ],
        "items_refund_minor": quote["items_refund_minor"],
        "shipping_refund_minor": quote["shipping_refund_minor"],
        "total_refund_minor": quote["total_refund_minor"],
        "currency": quote["currency"],
        "refund_destination": destination_words(quote.get("refund_destination")),
        "needs_shipping": quote["needs_shipping"],
        "expires_at": quote["expires_at"],
        "policy_version": quote["policy_version"],
        "readback": readback(quote),
    }


class OrderIdArgs(BaseModel):
    order_id: str = Field(description="An order_id from list_my_orders")


@tool("get_return_options", args_schema=OrderIdArgs, response_format="content_and_artifact")
def get_return_options(config: RunnableConfig, order_id: str) -> tuple[str, list[dict[str, Any]]]:
    """What each item in one of the customer's orders can return right now: eligible or not
    (with the policy reason), how many units, and the most it would refund. Read-only."""
    ctx = ctx_from(config)
    try:
        uuid.UUID(order_id)
        opts = ctx.client.get(f"/v1/orders/{order_id}/return-options")
    except ValueError:
        return untrusted("get_return_options", {"error": "not an order_id"}), []
    except CommerceError as exc:
        return _error("get_return_options", exc)
    payload = {
        "order_id": opts["order_id"],
        "policy_version": opts["policy_version"],
        "refund_destination": destination_words(opts.get("refund_destination")),
        "whole_order_shipping_refund": money(opts["whole_order_shipping_refund_minor"]),
        "lines": [
            {
                "order_line_id": ln["order_line_id"],
                "title": ln["product_title"],
                "variant": ln["variant_name"],
                "eligible": ln["eligible"],
                "reason": ln["reason"],
                "returnable_quantity": ln["returnable_quantity"],
                "already_returned": ln["returned_quantity"],
                "max_refund": money(ln["max_refund_minor"]),
                "refund_timing": ln["refund_timing"],
                "explanation": ln["message"],
            }
            for ln in opts["lines"]
        ],
    }
    card = {
        "kind": "return_options",
        "order_id": opts["order_id"],
        "lines": [
            {
                "order_line_id": ln["order_line_id"],
                "title": ln["product_title"],
                "variant_name": ln["variant_name"],
                "image_path": ln["image_path"],
                "eligible": ln["eligible"],
                "returnable_quantity": ln["returnable_quantity"],
                "max_refund_minor": ln["max_refund_minor"],
                "message": ln["message"],
            }
            for ln in opts["lines"]
        ],
    }
    return untrusted("get_return_options", payload), [card]


class QuoteLine(BaseModel):
    order_line_id: str = Field(description="From get_return_options")
    quantity: int = Field(ge=1, le=100)


class QuoteReturnArgs(BaseModel):
    order_id: str
    lines: list[QuoteLine] = Field(min_length=1, max_length=20)
    reason: REASONS | None = Field(
        default=None,
        description="Why the customer is returning it, if they said. Leave empty to use the "
        "reason the decision model read from the conversation.",
    )


@tool("quote_return", args_schema=QuoteReturnArgs, response_format="content_and_artifact")
def quote_return(
    config: RunnableConfig, order_id: str, lines: list[Any], reason: str | None = None
) -> tuple[str, list[dict[str, Any]]]:
    """Ask the store to price a return of specific units. The store checks eligibility and
    computes the exact refund; nothing is returned yet. Then call propose_return with the
    quote_id so the customer can confirm it."""
    ctx = ctx_from(config)
    signals = ctx.signals or {}
    jev_reason = signals.get("return_reason") or {}
    chosen = reason or (jev_reason.get("value") if jev_reason.get("act") else None) or "other"
    body = {
        "order_id": order_id,
        "lines": [
            {
                "order_line_id": ln["order_line_id"] if isinstance(ln, dict) else ln.order_line_id,
                "quantity": ln["quantity"] if isinstance(ln, dict) else ln.quantity,
            }
            for ln in lines
        ],
        "reason": chosen,
    }
    try:
        quote = ctx.client.post("/v1/returns/quote", body)
    except CommerceError as exc:
        return _error("quote_return", exc)
    payload = {
        "quote_id": quote["id"],
        "reason_used": chosen,
        "total_refund": money(quote["total_refund_minor"]),
        "shipping_refund": money(quote["shipping_refund_minor"]),
        "refund_to": destination_words(quote.get("refund_destination")),
        "needs_shipping": quote["needs_shipping"],
        "valid_until": quote["expires_at"],
        "lines": [
            {
                "title": ln["product_title"],
                "quantity": ln["quantity"],
                "refund": money(ln["refund_minor"]),
                "timing": ln["refund_timing"],
            }
            for ln in quote["lines"]
        ],
        "next_step": "Call propose_return with this quote_id. Don't state the refund as final "
        "until the customer confirms.",
    }
    return untrusted("quote_return", payload), []


class ProposeArgs(BaseModel):
    quote_id: str = Field(description="From quote_return")


@tool("propose_return", args_schema=ProposeArgs, response_format="content_and_artifact")
def propose_return(config: RunnableConfig, quote_id: str) -> tuple[str, list[dict[str, Any]]]:
    """Show the customer the quote and wait for them to confirm or decline it themselves. The
    conversation pauses here; you'll get the outcome when it resumes."""
    ctx = ctx_from(config)
    try:
        uuid.UUID(quote_id)
        quote = ctx.client.get(f"/v1/returns/quotes/{quote_id}")
    except ValueError:
        return untrusted("propose_return", {"error": "not a quote_id"}), []
    except CommerceError as exc:
        return _error("propose_return", exc)
    # LangGraph runs this tool again from the top when the conversation resumes, so the quote
    # may already be confirmed here; only an expired quote stops before the pause.
    if quote["status"] == "expired":
        payload: dict[str, Any] = {
            "outcome": "expired",
            "next_step": "The quote expired. Offer to price it again.",
        }
        return untrusted("propose_return", payload), [
            {"kind": "return_status", "outcome": "expired"}
        ]

    # Pause. The browser shows the card; the customer confirms or declines with the store.
    outcome = interrupt(quote_card(quote))

    # Resumed: check with the store what actually happened (never trust the resume message).
    try:
        latest = ctx.client.get(f"/v1/returns/quotes/{quote_id}")
    except CommerceError as exc:
        return _error("propose_return", exc)
    said = (outcome or {}).get("outcome") if isinstance(outcome, dict) else None
    if latest["status"] == "confirmed" and latest.get("return_id"):
        returns = ctx.client.get("/v1/returns")
        ret = next((r for r in returns if r["id"] == latest["return_id"]), None)
        payload = {
            "outcome": "confirmed",
            "rma_number": ret["rma_number"] if ret else None,
            "return_status": ret["status"] if ret else None,
            "refund": money(latest["total_refund_minor"]),
            "refund_to": destination_words(latest.get("refund_destination")),
            "needs_shipping": latest["needs_shipping"],
            "next_step": "Tell the customer it's confirmed, how the refund is timed, and, if "
            "something must be sent back, that the label is on the screen and any Larkspur "
            "store takes drop-offs.",
        }
        card = {
            "kind": "return_status",
            "outcome": "confirmed",
            "rma_number": payload["rma_number"],
            "status": payload["return_status"],
            "refund_minor": latest["total_refund_minor"],
            "needs_shipping": latest["needs_shipping"],
            "return_id": latest["return_id"],
        }
        return untrusted("propose_return", payload), [card]
    status = (
        "expired"
        if latest["status"] == "expired"
        else ("superseded" if said == "superseded" else "declined")
    )
    payload = {
        "outcome": status,
        "next_step": {
            "declined": "The customer didn't confirm. Nothing was returned. Ask if they want to "
            "change anything.",
            "expired": "The quote expired before it was confirmed. Offer to price it again.",
            "superseded": "The customer moved on without confirming. Nothing was returned.",
        }[status],
    }
    return untrusted("propose_return", payload), [{"kind": "return_status", "outcome": status}]


@tool("get_refund_status", response_format="content_and_artifact")
def get_refund_status(config: RunnableConfig) -> tuple[str, list[dict[str, Any]]]:
    """The customer's returns and their refund status, newest first."""
    ctx = ctx_from(config)
    try:
        returns = ctx.client.get("/v1/returns")
    except CommerceError as exc:
        return _error("get_refund_status", exc)
    payload = {
        "returns": [
            {
                "rma_number": r["rma_number"],
                "status": r["status"],
                "created_at": r["created_at"],
                "items": [f"{i['quantity']} × {i['product_title']}" for i in r["items"]],
                "refund": (
                    {
                        "status": r["refund"]["status"],
                        "amount": money(r["refund"]["amount_minor"]),
                        "settled_at": r["refund"]["settled_at"],
                    }
                    if r.get("refund")
                    else None
                ),
                "sample_history": r.get("is_sample", False),
            }
            for r in returns[:10]
        ]
    }
    cards = [
        {
            "kind": "return_status",
            "outcome": "existing",
            "rma_number": r["rma_number"],
            "status": r["status"],
            "refund_minor": (r.get("refund") or {}).get("amount_minor"),
            "refund_status": (r.get("refund") or {}).get("status"),
            "return_id": r["id"],
            "items": [f"{i['quantity']} × {i['product_title']}" for i in r["items"]],
        }
        for r in returns[:3]
    ]
    return untrusted("get_refund_status", payload), cards
