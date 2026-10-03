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

import httpx
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
# "Which has the most protein?": rank this many matching products by the nutrient, not the
# first page of a relevance search.
RANK_LIMIT = 120
NUTRIENT_SORTS = {
    "protein": "protein_g",
    "fiber": "fiber_g",
    "calories": "calories",
    "sugar": "total_sugars_g",
    "added_sugar": "added_sugars_g",
    "sodium": "sodium_mg",
    "fat": "total_fat_g",
}
SortOption = Literal[
    "relevance", "price_asc", "price_desc", "top_rated",
    "protein_desc", "protein_asc", "fiber_desc", "fiber_asc", "calories_desc", "calories_asc",
    "sugar_desc", "sugar_asc", "added_sugar_desc", "added_sugar_asc", "sodium_desc",
    "sodium_asc", "fat_desc", "fat_asc",
]  # fmt: skip


@dataclass
class ToolContext:
    """Server-side facts for one turn. Lives in the run config, never in model-visible state."""

    client: CommerceClient
    agent: str = "steph"
    first_name: str = ""
    # Jev's signals for this turn (set by the graph's route node).
    signals: dict[str, Any] | None = None
    # The customer is speaking (Xena's voice mode): short spoken answers.
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


def has_words(needle: str, text: str) -> bool:
    """``needle`` appears in ``text`` as whole words, ignoring case ("vanilla" is in
    "Unsweetened Vanilla"; "oat" isn't in "goat")."""

    def norm(s: str) -> str:
        return " ".join(re.sub(r"[-\u2010\u2011]", " ", s.casefold()).split())

    return bool(re.search(rf"(?<!\w){re.escape(norm(needle))}(?!\w)", norm(text)))


QUERY_STOPWORDS = frozenset(
    [
        "a",
        "an",
        "the",
        "for",
        "with",
        "and",
        "or",
        "of",
        "in",
        "on",
        "to",
        "my",
        "me",
        "some",
        "any",
        "that",
        "this",
        "these",
        "those",
        "please",
        "i",
        "want",
        "need",
        "find",
        "show",
        "get",
        "looking",
        "like",
        "one",
        "ones",
        "do",
        "you",
        "have",
        "is",
        "it",
        "are",
        "there",
        "what",
        "which",
    ]
)


def query_words(query: str | None) -> list[str]:
    """The words of a free-text search that a matching product should say."""
    words = re.findall(r"[a-z0-9%/.+'-]+", (query or "").casefold())
    return [
        w.strip(".'-")
        for w in words
        if w not in QUERY_STOPWORDS and (len(w) >= 3 or any(c.isdigit() for c in w))
    ]


def names_all(detail: dict[str, Any], words: list[str]) -> bool:
    """The product's brand, title, tags, or specs say every one of ``words`` (a plural or
    singular form counts: "beans" matches "Black Bean Soup")."""
    hay = " ".join(
        [
            detail.get("brand", ""),
            detail["title"],
            *(f"{t['value']} {t['label']}" for t in detail.get("tags", [])),
            *(str(v) for v in (detail.get("specs") or {}).values()),
        ]
    )

    def says(w: str) -> bool:
        forms = {w, w[:-1] if w.endswith("s") else w + "s", w[:-2] if w.endswith("es") else w}
        return any(f and has_words(f, hay) for f in forms)

    return all(says(w) for w in words)


def _variant_text(v: dict[str, Any]) -> str:
    attrs = " ".join(str(x) for x in (v.get("attributes") or {}).values())
    return f"{v['name']} {attrs}"


def _selected_variant(
    detail: dict[str, Any],
    max_price_minor: int | None = None,
    in_stock_only: bool = False,
    variant_terms: list[str] | None = None,
) -> dict[str, Any] | None:
    variants = detail.get("variants") or []
    eligible = [
        v
        for v in variants
        if (max_price_minor is None or v["price_minor"] <= max_price_minor)
        and (not in_stock_only or v.get("in_stock"))
        and all(has_words(t, _variant_text(v)) for t in variant_terms or [])
    ]
    return min(
        eligible,
        key=lambda v: (not v.get("in_stock"), v["price_minor"], v["name"]),
        default=None,
    )


def product_card(
    detail: dict[str, Any],
    highlight: list[str] | None = None,
    max_price_minor: int | None = None,
    in_stock_only: bool = False,
    variant_terms: list[str] | None = None,
) -> ProductCard:
    """A product card; tags the customer asked for (``highlight``) come first."""
    wanted = highlight or []
    tags = sorted(detail.get("tags", []), key=lambda t: t["value"] not in wanted)
    pick = _selected_variant(detail, max_price_minor, in_stock_only, variant_terms)
    return ProductCard(
        id=str(detail["id"]),
        title=detail["title"],
        brand=detail["brand"],
        product_type=detail["product_type"],
        price_minor=pick["price_minor"] if pick else detail["price_minor"],
        currency=detail.get("currency", "USD"),
        image_path=detail["image_path"],
        in_stock=bool(pick and pick.get("in_stock")),
        tags=[Tag(value=t["value"], label=t["label"]) for t in tags],
        url=f"/products/{detail['id']}",
        variant_id=str(pick["id"]) if pick else None,
        variant_name=pick["name"] if pick else None,
        facts=_facts(detail),
    )


def rating_for_model(detail: dict[str, Any]) -> dict[str, Any]:
    """The product's customer rating: average stars (one decimal) and how many reviews."""
    count = int(detail.get("rating_count") or 0)
    if not count or detail.get("rating_average") is None:
        return {"customer_rating": None, "review_count": 0}
    return {"customer_rating": detail["rating_average"], "review_count": count}


def _rated_first(details: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep the store's top-rated order, but products without reviews always come last."""
    return sorted(details, key=lambda d: not d.get("rating_count"))


def _product_for_model(
    detail: dict[str, Any],
    max_price_minor: int | None = None,
    in_stock_only: bool = False,
    variant_terms: list[str] | None = None,
) -> dict[str, Any]:
    pick = _selected_variant(detail, max_price_minor, in_stock_only, variant_terms)
    out = {
        "product_id": str(detail["id"]),
        "title": detail["title"],
        "brand": detail["brand"],
        "type": detail["product_type"],
        "price": money(pick["price_minor"] if pick else detail["price_minor"]),
        "in_stock": bool(pick and pick.get("in_stock")),
        "tags": [t["value"] for t in detail.get("tags", [])],
        **rating_for_model(detail),
    }
    if detail.get("nutrition"):
        out["nutrition_per_serving"] = detail["nutrition"]
    if detail.get("allergens") is not None:
        out["allergens"] = detail["allergens"]
    if detail.get("specs"):
        out["specs"] = detail["specs"]
    if detail.get("variants"):
        out["selected_variant"] = pick["name"] if pick else None
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
    required_specs: dict[str, str] = Field(
        default_factory=dict,
        description=(
            'Listing specifications every result must have, such as {"Flavor": "Chocolate"}, '
            '{"Style": "Greek"}, or {"Roast": "Dark"}. A value matches as whole words ("Vanilla" '
            'matches "Unsweetened Vanilla"); exact matches are preferred. Verified before showing '
            "a card."
        ),
    )
    variant_terms: list[str] = Field(
        default_factory=list,
        description=(
            'The size, count, or color the customer wants, such as "half gallon", "18", or '
            '"Sand". Only products offering such a variant are shown, with that variant\'s price.'
        ),
        max_length=3,
    )
    required_title_terms: list[str] = Field(
        default_factory=list,
        description=(
            'Words or phrases required in the product title, such as "Senior" or "SPF 50".'
        ),
        max_length=5,
    )
    exclude_allergens: list[str] = Field(
        default_factory=list,
        description=(
            'Listed major allergens to exclude, such as "tree nuts". '
            "This does not establish cross-contact safety."
        ),
        max_length=9,
    )
    max_price_dollars: float | None = Field(default=None, ge=0, le=100000)
    in_stock_only: bool = False
    sort: SortOption = Field(
        default="relevance",
        description="price_asc or price_desc for the cheapest or priciest; top_rated for the "
        'best-reviewed ("top rated", "highest rated", "best reviewed"): every matching product '
        "ranked by its customer rating, weighted by how many reviews it has, products without "
        'reviews last; a nutrient sort (e.g. "protein_desc", "sodium_asc") ranks every matching '
        'product by that nutrient per serving, for "which has the most or least" questions.',
    )


@tool("search_products", args_schema=SearchProductsArgs, response_format="content_and_artifact")
def search_products(
    config: RunnableConfig,
    query: str | None = None,
    product_types: list[str] | None = None,
    tags: list[str] | None = None,
    exclude_tags: list[str] | None = None,
    required_specs: dict[str, str] | None = None,
    variant_terms: list[str] | None = None,
    required_title_terms: list[str] | None = None,
    exclude_allergens: list[str] | None = None,
    max_price_dollars: float | None = None,
    in_stock_only: bool = False,
    sort: str = "relevance",
) -> tuple[str, list[dict[str, Any]]]:
    """Find products in the Serigan Mart catalog with exact filters (type, diet and feature tags,
    price) and optional free text. Returns the best matches with price, stock, tags, customer
    rating, and, for food, nutrition facts and allergens."""
    ctx = ctx_from(config)
    try:
        vocab = catalog_vocabulary(ctx.client)
    except CommerceError as exc:
        return _error("search_products", exc)
    known_types = {t["value"] for t in vocab["product_types"]}
    known_tags = {t["value"] for t in vocab["tags"]}
    unknown = [t for t in (product_types or []) if t not in known_types] + [
        t for t in [*(tags or []), *(exclude_tags or [])] if t not in known_tags
    ]
    if unknown:
        # An unrecognized required filter must not turn a narrow request into a broad
        # recommendation: say so, with the catalog's closest values to search with instead.
        return untrusted(
            "search_products",
            {
                "total_matches": 0,
                "results": [],
                "unsupported_filters": unknown,
                "closest_catalog_values": {u: closest_values(u, vocab) for u in unknown},
                "note": "No catalog search was run because a required filter is unknown. "
                "Search again with the closest catalog value that means what the customer "
                "asked for (for example no-salt-added for unsalted).",
            },
        ), []
    nutrient: tuple[str, bool] | None = None
    if sort not in ("relevance", "price_asc", "price_desc", "top_rated"):
        name, direction = sort.rsplit("_", 1)
        nutrient = (NUTRIENT_SORTS[name], direction == "desc")
    params: dict[str, Any] = {
        "page_size": 60 if nutrient else 24,
        "sort": "relevance" if nutrient else sort,
    }
    if query:
        params["q"] = query
    if product_types:
        params["product_type"] = [t for t in product_types if t in known_types]
    if tags:
        params["tag"] = [t for t in tags if t in known_tags]
    if exclude_tags:
        params["exclude_tag"] = [t for t in exclude_tags if t in known_tags]
    max_price_minor = round(max_price_dollars * 100) if max_price_dollars is not None else None
    if max_price_minor is not None:
        params["max_price"] = max_price_minor
    if in_stock_only:
        params["in_stock"] = True
    extra_checks = bool(
        required_specs or variant_terms or required_title_terms or exclude_allergens
    )
    try:
        page = ctx.client.get("/v1/products", params=params)
        items = list(page["items"])
        while nutrient and len(items) < min(page["total"], RANK_LIMIT):
            more = ctx.client.get(
                "/v1/products", params={**params, "page": len(items) // params["page_size"] + 1}
            )
            if not more["items"]:
                break
            items += more["items"]
        words = query_words(query)
        limit = RANK_LIMIT if nutrient else 24 if (extra_checks or words) else MAX_PRODUCTS
        candidates = [ctx.client.get(f"/v1/products/{item['id']}") for item in items[:limit]]
    except CommerceError as exc:
        return _error("search_products", exc)

    def terms_for(detail: dict[str, Any]) -> list[str]:
        """The variant terms for this product: the customer's, plus any required "spec" that is
        really a variant (a size or color isn't in the spec table). A term the product's own
        name already says ("32 oz" in "Insulated Water Bottle, 32 oz") needs no variant."""
        specs = {k.casefold() for k in detail.get("specs") or {}}
        named = f"{detail['brand']} {detail['title']}"
        wanted = [
            *(variant_terms or []),
            *(
                v
                for k, v in (required_specs or {}).items()
                if k.casefold() not in specs and k.casefold() != "brand"
            ),
        ]
        return [t for t in wanted if not has_words(t, named)]

    def verified(detail: dict[str, Any], exact: bool) -> bool:
        actual_tags = {t["value"] for t in detail.get("tags", [])}
        actual_allergens = {a.casefold() for a in detail.get("allergens") or []}
        specs = {
            key.casefold(): str(value).casefold()
            for key, value in (detail.get("specs") or {}).items()
        }

        def spec_ok(key: str, value: str) -> bool:
            actual = specs.get(key.casefold())
            if actual is None:
                if key.casefold() == "brand":
                    return has_words(value, detail["brand"])
                return True  # checked against the name and variants instead (terms_for)
            return actual == value.casefold() or (not exact and has_words(value, actual))

        return (
            (not product_types or detail["product_type"] in product_types)
            and set(tags or []) <= actual_tags
            and not (set(exclude_tags or []) & actual_tags)
            and all(spec_ok(k, v) for k, v in (required_specs or {}).items())
            and all(
                t.casefold() in f"{detail['brand']} {detail['title']}".casefold()
                for t in required_title_terms or []
            )
            and not (actual_allergens & {a.casefold() for a in exclude_allergens or []})
            and _selected_variant(detail, max_price_minor, in_stock_only, terms_for(detail))
            is not None
        )

    # Exact spec values first ("Dark" roast); whole-word matches ("Unsweetened Vanilla" for
    # "Vanilla") only when nothing matches exactly.
    details = [d for d in candidates if verified(d, exact=True)] or [
        d for d in candidates if verified(d, exact=False)
    ]
    note_type: str | None = None
    if words and not nutrient:
        # "green tea": the products that say every word come first, and near misses (a
        # chamomile tea) stay off the screen when any product says them all.
        named = [d for d in details if names_all(d, words)]
        if named:
            details = named
        elif product_types:
            # A named product searched under the wrong type ("Trailmark Nut & Seed Bar" as a
            # fruit-and-nut bar): look again without the type, and keep only products whose
            # brand the customer said.
            try:
                untyped = {k: v for k, v in params.items() if k != "product_type"}
                again = ctx.client.get("/v1/products", params=untyped)
                others = [ctx.client.get(f"/v1/products/{i['id']}") for i in again["items"][:12]]
            except CommerceError:
                others = []
            named = [
                d
                for d in others
                if names_all(d, words) and has_words(d["brand"], query or "")
                and _selected_variant(d, max_price_minor, in_stock_only, terms_for(d))
            ]  # fmt: skip
            if named:
                details = named
                note_type = named[0]["product_type"]
    if nutrient:
        field, highest_first = nutrient
        details = sorted(
            (d for d in details if d.get("nutrition")),
            key=lambda d: d["nutrition"][field],
            reverse=highest_first,
        )
    top_rated = sort == "top_rated"
    if top_rated:
        details = _rated_first(details)
    counted = extra_checks or nutrient or words
    payload: dict[str, Any] = {
        "total_matches": len(details) if counted else page["total"],
        "filters_used": {k: v for k, v in params.items() if k not in ("page_size",)},
        "results": [
            _product_for_model(d, max_price_minor, in_stock_only, terms_for(d))
            for d in details[:MAX_PRODUCTS]
        ],
    }
    if query:
        # "Nonna Lucia's Marinara Sauce" is that product, not also its low-sodium sibling.
        wanted = " ".join(query_words(query))
        exact = [
            str(d["id"])
            for d in details[:MAX_PRODUCTS]
            if " ".join(query_words(f"{d['brand']} {d['title']}")) == wanted
            or " ".join(query_words(d["title"])) == wanted
        ]
        if len(exact) == 1:
            payload["exact_name_match"] = exact[0]
    if note_type:
        payload["note_on_type"] = (
            f"The product named isn't a {', '.join(product_types or [])}; it's listed as "
            f"{note_type}, so it was found without that type filter."
        )
    if nutrient:
        payload["ranked_by"] = (
            f"{nutrient[0]} per serving, {'highest' if nutrient[1] else 'lowest'} first"
        )
        payload["ranked_among"] = len(candidates)
        payload["verification_limited"] = page["total"] > len(candidates)
    if top_rated:
        payload["ranked_by"] = (
            "customer rating, highest first, across every matching product (the store's "
            "top-rated order: the average weighted by how many reviews it has); products "
            "without reviews last"
        )
        if not any(d.get("rating_count") for d in details[:MAX_PRODUCTS]):
            payload["note_on_ratings"] = (
                "None of these products has customer reviews yet, so none is top rated."
            )
    if extra_checks:
        payload["verified_constraints"] = {
            "specs": required_specs or {},
            "variant": variant_terms or [],
            "title_terms": required_title_terms or [],
            "excluded_listed_allergens": exclude_allergens or [],
        }
        payload["candidate_matches"] = page["total"]
        payload["verification_limited"] = page["total"] > len(candidates)
    if page.get("search") and page["search"].get("semantic") != "ok":
        payload["note"] = "Meaning-based search is off; results come from keyword search."
    summary = search_summary_card(
        params,
        len(details) if counted else page["total"],
        min(len(details), MAX_PRODUCTS),
        vocab,
    )
    return untrusted("search_products", payload), [
        summary,
        *(
            product_card(d, tags, max_price_minor, in_stock_only, terms_for(d)).model_dump()
            for d in details[:MAX_PRODUCTS]
        ),
    ]


def closest_values(unknown: str, vocab: dict[str, Any]) -> list[str]:
    """Catalog types and tags whose value or label shares a word stem with ``unknown``
    ("unsalted" -> "no-salt-added"; "puppy-food" -> "dog-food")."""
    import difflib

    entries = [*vocab.get("product_types", []), *vocab.get("tags", [])]
    stems = {w[:4] for w in re.findall(r"[a-z]+", unknown.casefold()) if len(w) >= 4}
    stems |= {w[2:6] for w in re.findall(r"[a-z]+", unknown.casefold()) if w.startswith("un")}
    close = [
        e["value"]
        for e in entries
        if stems & {w[:4] for w in re.findall(r"[a-z]+", f"{e['value']} {e['label']}".casefold())}
    ]
    close += difflib.get_close_matches(unknown, [e["value"] for e in entries], n=3, cutoff=0.6)
    return list(dict.fromkeys(close))[:6]


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
    ingredients, allergens, specs, and its customer rating (average stars, review count)."""
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


MAX_REVIEWS = 5
REVIEW_EXCERPT = 300


def excerpt(text: str | None, limit: int = REVIEW_EXCERPT) -> str | None:
    """Customer-written text, whitespace collapsed and cut to ``limit`` characters."""
    if not text:
        return None
    flat = " ".join(text.split())
    return flat[:limit] + ("…" if len(flat) > limit else "")


def _review_for_model(r: dict[str, Any]) -> dict[str, Any]:
    """One review as data: stars, the reviewer's own words (short), and whether they bought it.
    No reviewer name or id: the model doesn't need to know who wrote it."""
    return {
        "rating": r["rating"],
        "title": excerpt(r.get("title"), 120),
        "text": excerpt(r.get("body")),
        "verified_purchase": r["verified_purchase"],
        "written_on": friendly_date(r["created_at"]),
        "sample_review": r.get("is_sample", False),
    }


class ProductReviewsArgs(BaseModel):
    product_id: str = Field(description="A product_id from an earlier search result")
    sort: Literal["newest", "highest", "lowest"] = Field(
        default="newest",
        description='Which reviews to read: "newest", or "highest" / "lowest" rated first '
        '(for "what do people like" or "any complaints?").',
    )
    rating: int | None = Field(
        default=None, ge=1, le=5, description="Only reviews with exactly this many stars"
    )


@tool("get_product_reviews", args_schema=ProductReviewsArgs, response_format="content_and_artifact")
def get_product_reviews(
    config: RunnableConfig, product_id: str, sort: str = "newest", rating: int | None = None
) -> tuple[str, list[dict[str, Any]]]:
    """Customer reviews for one product: the average star rating, how many reviews, how the
    stars are spread, and a few reviews in the reviewers' own words. Reviews are opinions,
    not facts about the product."""
    ctx = ctx_from(config)
    params: dict[str, Any] = {"sort": sort, "page_size": MAX_REVIEWS}
    if rating is not None:
        params["rating"] = rating
    try:
        uuid.UUID(product_id)
        detail = ctx.client.get(f"/v1/products/{product_id}")
        page = ctx.client.get(f"/v1/products/{product_id}/reviews", params=params)
    except ValueError:
        return untrusted("get_product_reviews", {"error": "not a product_id"}), []
    except CommerceError as exc:
        return _error("get_product_reviews", exc)
    summary = page["summary"]
    payload: dict[str, Any] = {
        "product_id": str(detail["id"]),
        "product": f"{detail['brand']} {detail['title']}",
        "average_rating": summary["average"],
        "review_count": summary["count"],
        "stars": {str(b["stars"]): b["count"] for b in summary.get("distribution", [])},
        "showing": f"{sort} first" + (f", {rating}-star only" if rating else ""),
        "matching_reviews": page["total"],
        "reviews": [_review_for_model(r) for r in page["items"][:MAX_REVIEWS]],
        "note": "Reviews are other customers' opinions, written by them. Summarize what they "
        "say as opinions; never present a review as a fact about the product's safety, "
        "ingredients, or specifications (the listing is the source for those).",
    }
    mine = page.get("my_review")
    if mine:
        payload["your_review"] = {
            "rating": mine["rating"],
            "title": excerpt(mine.get("title"), 120),
            "text": excerpt(mine.get("body")),
        }
    if summary["count"] == 0:
        payload["note"] = "This product has no reviews yet."
    return untrusted("get_product_reviews", payload), [product_card(detail).model_dump()]


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


_BRANDS: dict[str, str] = {}  # product_id -> brand (a product's brand doesn't change)


def with_brands(client: CommerceClient, details: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add each order line's product brand ("brand"), so "the Sonora earbuds" or "my Quillmark
    order" finds the right line: order lines keep only the product title."""
    wanted = {
        str(ln["product_id"])
        for d in details
        for ln in d.get("lines", [])
        if ln.get("product_id") and str(ln["product_id"]) not in _BRANDS
    }
    for pid in wanted:
        with contextlib.suppress(CommerceError, httpx.HTTPError):
            _BRANDS[pid] = client.get(f"/v1/products/{pid}")["brand"]
    for d in details:
        for ln in d.get("lines", []):
            brand = _BRANDS.get(str(ln.get("product_id")))
            if brand:
                ln["brand"] = brand
    return details


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
                "brand": ln.get("brand"),
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
        description="Only orders with an item whose brand and title contain these words, e.g. "
        '"otter" or "Sonora". Leave empty to see every recent order.',
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
        details = with_brands(
            ctx.client, [ctx.client.get(f"/v1/orders/{o['id']}") for o in summaries]
        )
    except CommerceError as exc:
        return _error("list_my_orders", exc)
    if contains:
        words = contains.lower().split()

        def named(ln: dict[str, Any]) -> str:
            return f"{ln.get('brand') or ''} {ln['product_title']}".lower()

        details = [
            d for d in details if any(all(w in named(ln) for w in words) for ln in d["lines"])
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
        detail = with_brands(ctx.client, [ctx.client.get(f"/v1/orders/{order_id}")])[0]
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


# "Can I return a TV?": the answer needs the item's group (section 1.4) as well as the
# sections the words match, and word matching alone often leaves it out.
ITEM_RETURN_QUESTION = re.compile(
    r"\b(?:return(?:able|ing)?|send (?:it |them )?back|return policy)\b", re.IGNORECASE
)
ITEM_TYPES_QUERY = "item types groups standard inspected perishable final sale departments"


def policy_search(client: CommerceClient, question: str, limit: int = 4) -> dict[str, Any]:
    """The approved policy sections for a question (``/v1/policies/search``), plus the item
    types section when the question is about returning some kind of item."""
    result: dict[str, Any] = client.get(
        "/v1/policies/search", params={"q": question, "limit": limit}
    )
    if ITEM_RETURN_QUESTION.search(question):
        extra = client.get("/v1/policies/search", params={"q": ITEM_TYPES_QUERY, "limit": 1})
        have = {r["cite"] for r in result["results"]}
        result["results"] += [r for r in extra["results"] if r["cite"] not in have]
    return result


class PolicyArgs(BaseModel):
    question: str = Field(description="The policy question in plain words", max_length=300)


@tool("search_policies", args_schema=PolicyArgs, response_format="content_and_artifact")
def search_policies(config: RunnableConfig, question: str) -> tuple[str, list[dict[str, Any]]]:
    """Search Serigan Mart's approved policies (returns and refunds, shipping, product labels, how
    returns are handled). Answer policy questions only from these sections and cite them."""
    ctx = ctx_from(config)
    try:
        result = policy_search(ctx.client, question)
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
    """Point the customer to Xena, the customer-support assistant on the Support page, for
    starting a return, reporting a problem with an order, or a refund. Steph can't start returns."""
    ctx_from(config)
    card = {
        "kind": "xana",
        "about": about,
        "message": "Xena handles returns and refunds, by voice or text. She finds the order, shows "
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
