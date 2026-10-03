"""Read-only account tools (Xena): the signed-in customer's cart, support cases, and activity.

Each reads one commerce route that the API scopes to the customer in the run's server-side
context (the model never names whose data it reads) and passes the model a whitelist of
fields: no addresses, emails, payment details, SKUs, or internal ids it doesn't need. None of
these tools changes anything; Xena can't add to the cart, close a case, or edit history.
"""

from __future__ import annotations

from typing import Any, Literal

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from assistant.commerce import CommerceError
from assistant.tools import (
    _error,
    ctx_from,
    friendly_date,
    money,
    order_number,
    store_day,
    untrusted,
)

MAX_CART_LINES = 20
MAX_CASES = 10
MAX_ACTIVITY = 20

# --- Cart -----------------------------------------------------------------------------------


@tool("get_my_cart", response_format="content_and_artifact")
def get_my_cart(config: RunnableConfig) -> tuple[str, list[dict[str, Any]]]:
    """What's in the customer's cart right now: each item with its quantity and current price,
    the subtotal, shipping, and the estimated total before tax. Read-only."""
    ctx = ctx_from(config)
    try:
        cart = ctx.client.get("/v1/cart")
    except CommerceError as exc:
        return _error("get_my_cart", exc)
    lines = cart.get("items") or []
    payload: dict[str, Any] = {
        "item_count": cart["item_count"],
        "items": [
            {
                "product_id": str(ln["product_id"]),
                "title": ln["product_title"],
                "variant": ln["variant_name"],
                "quantity": ln["quantity"],
                "price_each": money(ln["unit_price_minor"]),
                "line_total": money(ln["line_total_minor"]),
                "in_stock": ln["in_stock"],
            }
            for ln in lines[:MAX_CART_LINES]
        ],
        "subtotal": money(cart["subtotal_minor"]),
        "shipping": money(cart.get("shipping_minor", 0)),
        "estimated_total_before_tax": money(cart.get("estimated_total_minor", 0)),
        "note": "Prices are current and recalculated at checkout; tax is added at payment.",
    }
    if cart.get("free_shipping_remaining_minor"):
        payload["more_for_free_shipping"] = money(cart["free_shipping_remaining_minor"])
    if cart.get("warnings"):
        payload["warnings"] = list(cart["warnings"])
    if len(lines) > MAX_CART_LINES:
        payload["more_items_not_shown"] = len(lines) - MAX_CART_LINES
    return untrusted("get_my_cart", payload), []


# --- Support cases --------------------------------------------------------------------------

CASE_STATUS = {
    "open": "Open",
    "waiting_on_customer": "Waiting on you",
    "resolved": "Resolved",
}


@tool("list_my_support_cases", response_format="content_and_artifact")
def list_my_support_cases(config: RunnableConfig) -> tuple[str, list[dict[str, Any]]]:
    """The customer's own support cases, newest first: reference, topic, status, how it was
    opened, the order it's about, and when it was opened."""
    ctx = ctx_from(config)
    try:
        cases = ctx.client.get("/v1/support/cases")
    except CommerceError as exc:
        return _error("list_my_support_cases", exc)
    payload = {
        "count": len(cases),
        "cases": [
            {
                "reference": c["reference"],
                "topic": c["subject"],
                "status": CASE_STATUS.get(c["status"], c["status"]),
                "channel": c["channel"],
                "order_number": order_number(c["order_id"]) if c.get("order_id") else None,
                "opened_on": friendly_date(c["opened_at"]),
                "reply_within": c.get("reply_within"),
            }
            for c in cases[:MAX_CASES]
        ],
    }
    return untrusted("list_my_support_cases", payload), []


# --- Account activity -----------------------------------------------------------------------

ActivityType = Literal[
    "searched",
    "viewed_product",
    "added_to_cart",
    "placed_order",
    "order_delivered",
    "started_return",
    "refund_issued",
    "wrote_review",
    "contacted_support",
    "signed_in",
]
ACTIVITY_LABELS = {
    "signed_in": "Signed in",
    "searched": "Searched the store",
    "viewed_product": "Viewed a product",
    "added_to_cart": "Added to cart",
    "placed_order": "Placed an order",
    "order_delivered": "Order delivered",
    "started_return": "Started a return",
    "refund_issued": "Refund issued",
    "wrote_review": "Wrote a review",
    "contacted_support": "Contacted support",
}


def _activity_details(e: dict[str, Any]) -> dict[str, Any]:
    """The few event details worth reading, by name (never the raw ``data`` blob)."""
    data = e.get("data") or {}
    out: dict[str, Any] = {}
    if e["type"] == "searched" and data.get("query"):
        out["searched_for"] = str(data["query"])[:100]
    if e["type"] == "added_to_cart" and data.get("quantity"):
        out["quantity"] = data["quantity"]
    if e["type"] == "placed_order" and data.get("total_minor") is not None:
        out["order_total"] = money(int(data["total_minor"]))
    if e["type"] in ("started_return", "refund_issued") and data.get("rma"):
        out["rma_number"] = data["rma"]
    if e["type"] == "started_return" and data.get("refund_minor") is not None:
        out["refund_quoted"] = money(int(data["refund_minor"]))
    if e["type"] == "refund_issued" and data.get("amount_minor") is not None:
        out["refund_amount"] = money(int(data["amount_minor"]))
    if e["type"] == "wrote_review" and data.get("rating"):
        out["stars_given"] = data["rating"]
    if e["type"] == "contacted_support" and data.get("reference"):
        out["case_reference"] = data["reference"]
    return out


class ActivityArgs(BaseModel):
    limit: int = Field(
        default=10, ge=1, le=MAX_ACTIVITY, description="How many recent events, newest first"
    )
    types: list[ActivityType] = Field(
        default_factory=list,
        description='Only these kinds of events, e.g. ["viewed_product"] for "what was that '
        'thing I looked at?" or ["searched"]. Leave empty for everything.',
        max_length=10,
    )


@tool("get_my_account_activity", args_schema=ActivityArgs, response_format="content_and_artifact")
def get_my_account_activity(
    config: RunnableConfig, limit: int = 10, types: list[str] | None = None
) -> tuple[str, list[dict[str, Any]]]:
    """The customer's recent account activity, newest first: products they viewed, searches,
    cart adds, orders, deliveries, returns, refunds, reviews, and support contacts."""
    ctx = ctx_from(config)
    params: dict[str, Any] = {"limit": max(1, min(limit, MAX_ACTIVITY))}
    if types:
        params["type"] = list(types)
    try:
        events = ctx.client.get("/v1/activity", params=params)
    except CommerceError as exc:
        return _error("get_my_account_activity", exc)
    rows = []
    for e in events[:MAX_ACTIVITY]:
        product = e.get("product")
        row: dict[str, Any] = {
            "what": ACTIVITY_LABELS.get(e["type"], e["type"]),
            "when": store_day(e["occurred_at"]),
        }
        if product:
            row["product"] = product["title"]
            row["product_id"] = str(product["id"])
        if e.get("order_id"):
            row["order_number"] = order_number(e["order_id"])
        row.update(_activity_details(e))
        if e.get("is_sample"):
            row["sample_history"] = True
        rows.append(row)
    return untrusted("get_my_account_activity", {"events": rows, "count": len(rows)}), []
