"""The assistant's tools: narrow, typed calls to the commerce API for one signed-in customer.

Every tool returns ``(content, cards)``. The content goes to the model as JSON wrapped in
``<untrusted_data>`` (product text, policy text, and tool output are data, never instructions);
the cards go to the browser. The customer's identity is in the :class:`ToolContext` the server
puts in the run config, never in a tool argument, so the model can't choose whose data it reads.

There is deliberately no tool that confirms a return, pays, or refunds.
"""

from __future__ import annotations

import contextlib
import json
import re
import uuid
from dataclasses import dataclass
from typing import Any, Literal

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field

from assistant.commerce import CommerceClient, CommerceError, catalog_vocabulary
from assistant.schemas import (
    CartCard,
    CitationCard,
    HandoffCard,
    OrderCard,
    OrderLineBrief,
    ProductCard,
    StoreCard,
    Tag,
)

MAX_PRODUCTS = 6
MAX_ORDERS = 12


@dataclass
class ToolContext:
    """Server-side facts for one turn. Lives in the run config, never in model-visible state."""

    client: CommerceClient
    agent: str = "steph"
    first_name: str = ""
    # Jev's signals for this turn (set by the graph's route node).
    signals: dict[str, Any] | None = None
    # The customer is speaking (Xana's voice mode): short spoken answers.
    voice: bool = False
    conversation_id: str | None = None


def ctx_from(config: RunnableConfig) -> ToolContext:
    ctx = (config.get("configurable") or {}).get("ctx")
    if not isinstance(ctx, ToolContext):
        raise RuntimeError("tool called without a server-side context")
    return ctx


def untrusted(source: str, payload: Any) -> str:
    """Tool output for the model: data to read, never instructions to follow."""
    body = json.dumps(payload, ensure_ascii=False, default=str)
    return f'<untrusted_data source="{source}">\n{body}\n</untrusted_data>'


def money(minor: int) -> str:
    return f"${minor / 100:,.2f}"


def _clock(hhmm: str | None) -> str:
    if not hhmm:
        return ""
    h, m = (int(x) for x in hhmm.split(":"))
    suffix = "AM" if h < 12 else "PM"
    return f"{(h % 12) or 12}:{m:02d} {suffix}"


def _error(source: str, exc: CommerceError) -> tuple[str, list[dict[str, Any]]]:
    return untrusted(source, {"error": exc.detail, "status": exc.status}), []


# --- Products -------------------------------------------------------------------------------


def _facts(detail: dict[str, Any]) -> list[str]:
    facts: list[str] = []
    n = detail.get("nutrition")
    if n:
        facts.append(f"{n['calories']} cal, {n['protein_g']:g} g protein per {n['serving_size']}")
        facts.append(f"{n['total_fat_g']:g} g fat, {n['added_sugars_g']:g} g added sugar")
    for key, value in list((detail.get("specs") or {}).items())[:3]:
        facts.append(f"{key}: {value}")
    return facts


def product_card(detail: dict[str, Any], highlight: list[str] | None = None) -> ProductCard:
    """A product card; tags the customer asked for (``highlight``) come first."""
    variants = detail.get("variants") or []
    wanted = highlight or []
    tags = sorted(detail.get("tags", []), key=lambda t: t["value"] not in wanted)
    pick = next((v for v in variants if v.get("in_stock")), variants[0] if variants else None)
    return ProductCard(
        id=str(detail["id"]),
        title=detail["title"],
        brand=detail["brand"],
        product_type=detail["product_type"],
        price_minor=detail["price_minor"],
        currency=detail.get("currency", "USD"),
        image_path=detail["image_path"],
        in_stock=detail["in_stock"],
        tags=[Tag(value=t["value"], label=t["label"]) for t in tags],
        url=f"/products/{detail['id']}",
        variant_id=str(pick["id"]) if pick else None,
        variant_name=pick["name"] if pick else None,
        facts=_facts(detail),
    )


def _product_for_model(detail: dict[str, Any]) -> dict[str, Any]:
    out = {
        "product_id": str(detail["id"]),
        "title": detail["title"],
        "brand": detail["brand"],
        "type": detail["product_type"],
        "price": money(detail["price_minor"]),
        "in_stock": detail["in_stock"],
        "tags": [t["value"] for t in detail.get("tags", [])],
    }
    if detail.get("nutrition"):
        out["nutrition_per_serving"] = detail["nutrition"]
    if detail.get("allergens") is not None:
        out["allergens"] = detail["allergens"]
    if detail.get("specs"):
        out["specs"] = detail["specs"]
    if detail.get("variants"):
        out["variants"] = [
            {
                "variant_id": str(v["id"]),
                "name": v["name"],
                "price": money(v["price_minor"]),
                "in_stock": v["in_stock"],
            }
            for v in detail["variants"][:6]
        ]
    return out


class SearchProductsArgs(BaseModel):
    query: str | None = Field(
        default=None,
        description="Free-text words that aren't covered by the filters (a brand, a flavor, "
        "a style). Leave empty when product_types and tags already say it all.",
        max_length=200,
    )
    product_types: list[str] = Field(
        default_factory=list,
        description='Product types, any of (e.g. ["milk"]). Use values from the catalog '
        "vocabulary in the system prompt.",
        max_length=5,
    )
    tags: list[str] = Field(
        default_factory=list,
        description='Tags every result must have (e.g. ["organic", "fat-free"]).',
        max_length=8,
    )
    exclude_tags: list[str] = Field(
        default_factory=list,
        description='Tags no result may have (e.g. ["whole-milk"]).',
        max_length=8,
    )
    max_price_dollars: float | None = Field(default=None, ge=0, le=100000)
    in_stock_only: bool = False
    sort: Literal["relevance", "price_asc", "price_desc"] = "relevance"


@tool("search_products", args_schema=SearchProductsArgs, response_format="content_and_artifact")
def search_products(
    config: RunnableConfig,
    query: str | None = None,
    product_types: list[str] | None = None,
    tags: list[str] | None = None,
    exclude_tags: list[str] | None = None,
    max_price_dollars: float | None = None,
    in_stock_only: bool = False,
    sort: str = "relevance",
) -> tuple[str, list[dict[str, Any]]]:
    """Find products in the Serigan Mart catalog with exact filters (type, diet and feature tags,
    price) and optional free text. Returns the best matches with price, stock, tags, and, for
    food, nutrition facts and allergens."""
    ctx = ctx_from(config)
    vocab = catalog_vocabulary(ctx.client)
    known_types = {t["value"] for t in vocab["product_types"]}
    known_tags = {t["value"] for t in vocab["tags"]}
    unknown = [t for t in (product_types or []) if t not in known_types] + [
        t for t in [*(tags or []), *(exclude_tags or [])] if t not in known_tags
    ]
    params: dict[str, Any] = {"page_size": 24, "sort": sort}
    if query:
        params["q"] = query
    if product_types:
        params["product_type"] = [t for t in product_types if t in known_types]
    if tags:
        params["tag"] = [t for t in tags if t in known_tags]
    if exclude_tags:
        params["exclude_tag"] = [t for t in exclude_tags if t in known_tags]
    if max_price_dollars is not None:
        params["max_price"] = round(max_price_dollars * 100)
    if in_stock_only:
        params["in_stock"] = True
    try:
        page = ctx.client.get("/v1/products", params=params)
        details = [
            ctx.client.get(f"/v1/products/{item['id']}") for item in page["items"][:MAX_PRODUCTS]
        ]
    except CommerceError as exc:
        return _error("search_products", exc)
    payload: dict[str, Any] = {
        "total_matches": page["total"],
        "filters_used": {k: v for k, v in params.items() if k not in ("page_size",)},
        "results": [_product_for_model(d) for d in details],
    }
    if unknown:
        payload["ignored_unknown_filters"] = unknown
    if page.get("search") and page["search"].get("semantic") != "ok":
        payload["note"] = "Meaning-based search is off; results come from keyword search."
    summary = search_summary_card(params, page["total"], len(details), vocab)
    return untrusted("search_products", payload), [
        summary,
        *(product_card(d, tags).model_dump() for d in details),
    ]


def search_summary_card(
    params: dict[str, Any], total: int, shown: int, vocab: dict[str, Any]
) -> dict[str, Any]:
    """What was searched, as chips, with a link to the full results on the site."""
    from urllib.parse import urlencode

    type_labels = {t["value"]: t["label"] for t in vocab.get("product_types", [])}
    tag_labels = {t["value"]: t["label"] for t in vocab.get("tags", [])}
    chips = [type_labels.get(t, t) for t in params.get("product_type", [])]
    chips += [tag_labels.get(t, t) for t in params.get("tag", [])]
    chips += [f"Not {tag_labels.get(t, t).lower()}" for t in params.get("exclude_tag", [])]
    if "max_price" in params:
        chips.append(f"Under {money(params['max_price'])}")
    if params.get("q"):
        chips.append(f"\u201c{params['q']}\u201d")
    query: list[tuple[str, Any]] = []
    for key in ("q", "product_type", "tag", "exclude_tag", "max_price", "sort"):
        value = params.get(key)
        if value in (None, "", "relevance"):
            continue
        for v in value if isinstance(value, list) else [value]:
            query.append((key, v))
    return {
        "kind": "search",
        "total": total,
        "shown": shown,
        "chips": chips,
        "url": "/search?" + urlencode(query) if query else "/search",
    }


class ProductIdArgs(BaseModel):
    product_id: str = Field(description="A product_id from an earlier search result")


@tool("get_product_details", args_schema=ProductIdArgs, response_format="content_and_artifact")
def get_product_details(
    config: RunnableConfig, product_id: str
) -> tuple[str, list[dict[str, Any]]]:
    """Full details for one product: every variant with price and stock, nutrition facts,
    ingredients, allergens, and specs."""
    ctx = ctx_from(config)
    try:
        uuid.UUID(product_id)
        detail = ctx.client.get(f"/v1/products/{product_id}")
    except ValueError:
        return untrusted("get_product_details", {"error": "not a product_id"}), []
    except CommerceError as exc:
        return _error("get_product_details", exc)
    payload = _product_for_model(detail)
    payload["description"] = detail.get("description", "")
    payload["ingredients"] = detail.get("ingredients")
    payload["category"] = detail["category"]["name"]
    payload["return_policy_class"] = detail["category"]["policy_class"]
    return untrusted("get_product_details", payload), [product_card(detail).model_dump()]


# --- Cart -----------------------------------------------------------------------------------


class AddToCartArgs(BaseModel):
    variant_id: str = Field(description="A variant_id from a search result or product details")
    quantity: int = Field(default=1, ge=1, le=10, description="How many to add")


@tool("add_to_cart", args_schema=AddToCartArgs, response_format="content_and_artifact")
def add_to_cart(
    config: RunnableConfig, variant_id: str, quantity: int = 1
) -> tuple[str, list[dict[str, Any]]]:
    """Add a product variant to the customer's cart. Only when the customer asked for it."""
    ctx = ctx_from(config)
    try:
        uuid.UUID(variant_id)
        cart = ctx.client.get("/v1/cart")
        current = next((i for i in cart["items"] if i["variant_id"] == variant_id), None)
        new_qty = (current["quantity"] if current else 0) + quantity
        cart = ctx.client.put("/v1/cart/items", {"variant_id": variant_id, "quantity": new_qty})
    except ValueError:
        return untrusted("add_to_cart", {"error": "not a variant_id"}), []
    except CommerceError as exc:
        return _error("add_to_cart", exc)
    line = next(i for i in cart["items"] if i["variant_id"] == variant_id)
    card = CartCard(
        added_title=line["product_title"],
        added_variant=line["variant_name"],
        quantity=quantity,
        item_count=cart["item_count"],
        subtotal_minor=cart["subtotal_minor"],
    )
    payload = {
        "added": f"{quantity} × {line['product_title']} ({line['variant_name']})",
        "now_in_cart": line["quantity"],
        "cart_items": cart["item_count"],
        "cart_subtotal": money(cart["subtotal_minor"]),
    }
    return untrusted("add_to_cart", payload), [card.model_dump()]


# --- Orders ---------------------------------------------------------------------------------


# Same as the website (apps/web/lib/orders.ts): the last 8 characters of the id, uppercase.
def order_number(order_id: str) -> str:
    return str(order_id).replace("-", "")[-8:].upper()


STATUS_LABELS = {
    "paid": "Order placed",
    "fulfilling": "In progress",
    "delivered": "Delivered",
    "canceled": "Canceled",
}


def friendly_date(iso: str | None) -> str | None:
    """'2026-09-24T15:00:00+00:00' -> 'Sep 24'."""
    if not iso:
        return None
    try:
        from datetime import datetime

        d = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
    except ValueError:
        return str(iso)[:10]
    return f"{d:%b} {d.day}"


STORE_TIME_ZONE = "America/Chicago"  # same as the website's dates (apps/web/lib/orders.ts)


def store_day(iso: str | None) -> str | None:
    """'2026-09-29T17:22:51-05:00' -> 'Tue, Sep 29', in the store's time zone like the site."""
    if not iso:
        return None
    from datetime import datetime
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

    try:
        d = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
    except ValueError:
        return str(iso)[:10]
    # Without a tz database on this machine, the timestamp keeps its own offset.
    with contextlib.suppress(ZoneInfoNotFoundError):
        d = d.astimezone(ZoneInfo(STORE_TIME_ZONE)) if d.tzinfo else d
    return f"{d:%a}, {d:%b} {d.day}"


SHIPMENT_LABELS = {
    "label_created": "Label created",
    "in_transit": "In transit",
    "out_for_delivery": "Out for delivery",
    "delivered": "Delivered",
    "exception": "Delivery problem",
}
# Same choice as the website's primaryShipment: a problem first, else what's still coming.
_SHIPMENT_RANK = {
    "exception": 0,
    "label_created": 1,
    "in_transit": 2,
    "out_for_delivery": 3,
    "delivered": 4,
}


def _delivery_for_model(detail: dict[str, Any]) -> dict[str, Any] | None:
    """Delivery and tracking facts only: carrier, service, tracking number, dates, and the
    carrier's latest status line. Never the address, event locations, or payment."""
    shipments = sorted(
        detail.get("shipments") or [], key=lambda s: _SHIPMENT_RANK.get(s.get("status"), 0)
    )
    if not shipments:
        return None
    s = shipments[0]
    events = s.get("events") or []
    latest = max(events, key=lambda e: str(e.get("occurred_at", "")), default=None)
    return {
        "status": SHIPMENT_LABELS.get(s["status"], s["status"]),
        "carrier": s["carrier"],
        "service": s["service"],
        "tracking_number": s["tracking_number"],
        "shipped_on": store_day(s.get("shipped_at")),
        "arriving_by": store_day(s.get("estimated_delivery_at")),
        "delivered_on": store_day(s.get("delivered_at")),
        "latest_update": latest.get("description") if latest else None,
        "simulated_tracking": bool(s.get("is_simulated")),
        "parcels": len(shipments),
    }


def order_card(detail: dict[str, Any]) -> OrderCard:
    return OrderCard(
        id=str(detail["id"]),
        number=order_number(detail["id"]),
        status=detail["status"],
        placed_at=detail["placed_at"],
        delivered_at=detail.get("delivered_at"),
        total_minor=detail["total_minor"],
        item_count=detail["item_count"],
        lines=[
            OrderLineBrief(
                id=str(ln["id"]),
                title=ln["product_title"],
                variant_name=ln["variant_name"],
                quantity=ln["quantity"],
                image_path=ln["image_path"],
            )
            for ln in detail.get("lines", [])
        ],
        url=f"/orders/{detail['id']}",
    )


def _order_for_model(detail: dict[str, Any]) -> dict[str, Any]:
    """What the model may read about an order: a whitelist. No address and no payment card."""
    return {
        "order_id": str(detail["id"]),
        "order_number": order_number(detail["id"]),
        "status": STATUS_LABELS.get(detail["status"], detail["status"]),
        "placed_on": friendly_date(detail["placed_at"]),
        "delivered_on": friendly_date(detail.get("delivered_at")),
        "arriving_by": store_day(detail.get("estimated_delivery_at")),
        "delivery": _delivery_for_model(detail),
        "total": money(detail["total_minor"]),
        "shipping": money(detail.get("shipping_minor", 0)),
        "items": [
            {
                "line_id": str(ln["id"]),
                "title": ln["product_title"],
                "variant": ln["variant_name"],
                "quantity": ln["quantity"],
                "paid_per_unit": money(ln["unit_price_minor"]),
            }
            for ln in detail.get("lines", [])
        ],
    }


class ListOrdersArgs(BaseModel):
    contains: str | None = Field(
        default=None,
        description='Only orders with an item whose title contains these words, e.g. "otter"',
        max_length=80,
    )


@tool("list_my_orders", args_schema=ListOrdersArgs, response_format="content_and_artifact")
def list_my_orders(
    config: RunnableConfig, contains: str | None = None
) -> tuple[str, list[dict[str, Any]]]:
    """The signed-in customer's recent orders, newest first, with their items, status, and
    delivery date."""
    ctx = ctx_from(config)
    try:
        summaries = ctx.client.get("/v1/orders")[:MAX_ORDERS]
        details = [ctx.client.get(f"/v1/orders/{o['id']}") for o in summaries]
    except CommerceError as exc:
        return _error("list_my_orders", exc)
    if contains:
        words = contains.lower().split()
        details = [
            d
            for d in details
            if any(all(w in ln["product_title"].lower() for w in words) for ln in d["lines"])
        ]
    payload = {"orders": [_order_for_model(d) for d in details], "count": len(details)}
    return untrusted("list_my_orders", payload), [order_card(d).model_dump() for d in details[:5]]


class OrderStatusArgs(BaseModel):
    order_id: str | None = Field(default=None, description="An order_id from list_my_orders")
    order_number: str | None = Field(
        default=None,
        description="The 8-character order number the customer names or the site shows, e.g. "
        '"E2EA6BC6". Use this when the customer refers to an order by its number.',
        max_length=20,
    )


ORDER_NUMBER_RE = re.compile(r"#?\s*([0-9A-Fa-f]{8})")


def _resolve_order_number(client: CommerceClient, number: str) -> str | None:
    """The customer's own order with this number, from their order list (so it's owned)."""
    m = ORDER_NUMBER_RE.fullmatch(number.strip())
    if not m:
        return None
    wanted = m.group(1).upper()
    return next(
        (str(o["id"]) for o in client.get("/v1/orders") if order_number(o["id"]) == wanted),
        None,
    )


@tool("get_order_status", args_schema=OrderStatusArgs, response_format="content_and_artifact")
def get_order_status(
    config: RunnableConfig, order_id: str | None = None, order_number: str | None = None
) -> tuple[str, list[dict[str, Any]]]:
    """One of the customer's orders in full: status, items, amounts, and delivery (carrier,
    tracking number, arriving-by or delivered date, latest carrier update). Pass the order_id,
    or the order_number when the customer names one."""
    ctx = ctx_from(config)
    try:
        if not order_id and order_number:
            order_id = _resolve_order_number(ctx.client, order_number)
            if order_id is None:
                return untrusted(
                    "get_order_status",
                    {"error": "no order with that number on this account", "status": 404},
                ), []
        if not order_id:
            return untrusted("get_order_status", {"error": "give an order_id or order_number"}), []
        uuid.UUID(order_id)
        detail = ctx.client.get(f"/v1/orders/{order_id}")
    except ValueError:
        return untrusted("get_order_status", {"error": "not an order_id"}), []
    except CommerceError as exc:
        return _error("get_order_status", exc)
    return untrusted("get_order_status", _order_for_model(detail)), [
        order_card(detail).model_dump()
    ]


# --- Stores ---------------------------------------------------------------------------------


def store_card(s: dict[str, Any]) -> StoreCard:
    today = s["today_hours"]
    hours = (
        f"{_clock(today['opens'])} – {_clock(today['closes'])}"
        if today["opens"]
        else "Closed today"
    )
    address = f"{s['address_line1']}, {s['city']}, {s['state']} {s['postal_code']}"
    return StoreCard(
        code=s["code"],
        name=s["name"],
        address=address,
        phone=s["phone"],
        open_now=s["open_now"],
        today_hours=hours,
        services=s.get("services", []),
        directions_url="https://www.google.com/maps/dir/?api=1&destination="
        + f"{s['latitude']},{s['longitude']}",
    )


class ListStoresArgs(BaseModel):
    city: str | None = Field(default=None, description='Only stores in this city, e.g. "Plano"')


@tool("list_stores", args_schema=ListStoresArgs, response_format="content_and_artifact")
def list_stores(
    config: RunnableConfig, city: str | None = None
) -> tuple[str, list[dict[str, Any]]]:
    """Serigan Mart stores around Dallas–Fort Worth: address, phone, today's hours, open now, and
    services (such as the return drop-off counter)."""
    ctx = ctx_from(config)
    try:
        stores = ctx.client.get("/v1/stores")
    except CommerceError as exc:
        return _error("list_stores", exc)
    if city:
        stores = [s for s in stores if city.lower() in s["city"].lower()] or stores
    cards = [store_card(s) for s in stores]
    payload = {
        "stores": [
            {
                "name": c.name,
                "address": c.address,
                "phone": c.phone,
                "open_now": c.open_now,
                "today": c.today_hours,
                "services": c.services,
                "week_hours": {h["day"]: [h["opens"], h["closes"]] for h in s["hours"]},
            }
            for c, s in zip(cards, stores, strict=True)
        ]
    }
    return untrusted("list_stores", payload), [c.model_dump() for c in cards[:4]]


# --- Policies -------------------------------------------------------------------------------


def citation_card(r: dict[str, Any]) -> CitationCard:
    excerpt = " ".join(r["body"].split())
    return CitationCard(
        cite=r["cite"],
        doc_title=r["doc_title"],
        number=r["number"],
        title=r["title"],
        version=r["version"],
        url=r["url"],
        excerpt=excerpt[:280] + ("…" if len(excerpt) > 280 else ""),
    )


class PolicyArgs(BaseModel):
    question: str = Field(description="The policy question in plain words", max_length=300)


@tool("search_policies", args_schema=PolicyArgs, response_format="content_and_artifact")
def search_policies(config: RunnableConfig, question: str) -> tuple[str, list[dict[str, Any]]]:
    """Search Serigan Mart's approved policies (returns and refunds, shipping, product labels, how
    returns are handled). Answer policy questions only from these sections and cite them."""
    ctx = ctx_from(config)
    try:
        result = ctx.client.get("/v1/policies/search", params={"q": question, "limit": 4})
    except CommerceError as exc:
        return _error("search_policies", exc)
    payload = {
        "sections": [
            {
                "cite": r["cite"],
                "title": f"{r['doc_title']} §{r['number']} {r['title']}".strip(),
                "version": r["version"],
                "text": r["body"],
            }
            for r in result["results"]
        ]
    }
    # These cards make the sections citable; the browser shows only the ones the answer cites.
    return untrusted("search_policies", payload), [
        citation_card(r).model_dump() for r in result["results"]
    ]


# --- Handoff --------------------------------------------------------------------------------


class HandoffArgs(BaseModel):
    reason: str = Field(description="Why a person is needed, in a few words", max_length=200)
    order_id: str | None = Field(default=None, description="The order it's about, if any")


@tool("handoff_to_person", args_schema=HandoffArgs, response_format="content_and_artifact")
def handoff_to_person(
    config: RunnableConfig, reason: str, order_id: str | None = None
) -> tuple[str, list[dict[str, Any]]]:
    """Open a support case so a person takes over, when the customer asks for one or you can't
    help from the approved information. The conversation is attached to the case."""
    ctx = ctx_from(config)
    body: dict[str, Any] = {
        "subject": reason[:200] or "Customer asked for a person",
        "summary": f"Opened from a conversation with {ctx.agent.title()}"
        + (f" (conversation {ctx.conversation_id})" if ctx.conversation_id else "")
        + f". Reason: {reason}",
        "channel": "voice" if ctx.voice else "chat",
    }
    if order_id:
        body["order_id"] = order_id
    try:
        case = ctx.client.post("/v1/support/cases", body)
    except CommerceError as exc:
        return _error("handoff_to_person", exc)
    card = HandoffCard(
        reason=reason,
        message=f"Case {case['reference']} is open. A member of our support team will reply "
        f"within {case['reply_within']}, with this conversation in hand.",
    )
    payload = {"case_reference": case["reference"], "reply_within": case["reply_within"]}
    return untrusted("handoff_to_person", payload), [card.model_dump()]


class SuggestXanaArgs(BaseModel):
    about: str = Field(
        description="What the customer wants help with, in a few words", max_length=200
    )


@tool("suggest_xana", args_schema=SuggestXanaArgs, response_format="content_and_artifact")
def suggest_xana(config: RunnableConfig, about: str) -> tuple[str, list[dict[str, Any]]]:
    """Point the customer to Xana, the customer-support assistant on the Support page, for
    starting a return, reporting a problem with an order, or a refund. Steph can't start returns."""
    ctx_from(config)
    card = {
        "kind": "xana",
        "about": about,
        "message": "Xana handles returns and refunds, by voice or text. She finds the order, shows "
        "your exact refund, and starts the return when you confirm.",
        "url": "/support",
    }
    return untrusted("suggest_xana", {"suggested": True}), [card]


STEPH_TOOLS: list[BaseTool] = [
    search_products,
    get_product_details,
    add_to_cart,
    list_my_orders,
    get_order_status,
    list_stores,
    search_policies,
    suggest_xana,
    handoff_to_person,
]
