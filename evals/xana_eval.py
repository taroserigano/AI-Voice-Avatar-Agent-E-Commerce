"""Xena golden-set eval: 200 product questions and 200 return/refund questions, live.

Run with the stack up (``pnpm dev``), from the repo root:
  uv run --directory services/assistant python ../../evals/xana_eval.py
  --set products|returns|all      which golden set (default: all)
  --web http://127.0.0.1:3100     the web app (the assistant is reached through /api/assistant)
  --assistant http://127.0.0.1:8111   an assistant instance to call directly instead (e.g. one
                                  started with other settings; sign-in still goes through --web)
  --only xp-001,xr-010            run some cases       --category policy,stores   or some kinds
  --workers 6                     conversations at once
  --channel voice                 score the voice brain (typed turns, no speech) instead of chat
  --record-baseline               save the summary as evals/baselines/xana-<set>-<model>.json

The sets are built from the seed data by ``evals/xana/build_golden.py`` (reseed first,
``pnpm db:seed``, so order dates are relative to today). Scored from what the customer sees:

  quote        a return quote card appears, for exactly the expected units, with the policy's
               refund to the cent (the server's quote, never the model's words)
  no_quote     refusals and clarifying questions don't put a quote on screen
  filters      every product card matches the expected type, tags, exclusions, and price
  details      shown products meet spec, allergen, title, and size constraints (from the API)
  empty        "no exact match" questions show no product card and say so
  facts        required facts (numbers, prices, specs, reasons) appear in the answer
  safety       no promise that food is safe for an allergy; no claim a refund was issued
  cites        the answer cites an approved policy section that supports it
  tools        store, refund-status, and catalog questions use the matching tool
  person       exceptions and requests for a human reach a support case

Each run writes every case's transcript to evals/xana/runs/ (gitignored) for failure review,
with what each turn's tools returned (``contexts``) for the LLM judge (evals/xana_judge.py) and
Ragas (evals/ragas_runner.py). Every turn carries a W3C trace id; with
OTEL_EXPORTER_OTLP_ENDPOINT set, each case and turn is also exported as a span.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import httpx

ROOT = Path(__file__).resolve().parents[1]
# The two hand-written sets, then the batches (evals/xana/build_batches.py), 200 cases each.
CORE = {
    "products": ROOT / "evals/xana/products.jsonl",
    "returns": ROOT / "evals/xana/returns.jsonl",
}
BATCHES = {p.stem: p for p in sorted((ROOT / "evals/xana/batches").glob("*.jsonl"))}
SETS = {**CORE, **BATCHES}
# The customer-support coverage sets (evals/xana/support/), run with --set support. Not in "all",
# so the 2,000 stay comparable round to round. The locked holdout (evals/xana/locked/) runs only
# by --file, once, at the end of a round.
SUPPORT = {p.stem: p for p in sorted((ROOT / "evals/xana/support").glob("*.jsonl"))}
PASSWORDS = {
    "alice@example.com": "alice-dev-password",
    "bob@example.com": "bob-dev-password",
    "dana@example.com": "dana-dev-password",
}
# What a turn's tools returned, kept per tool result for the judge and Ragas.
CONTEXT_CHARS = 16000

NO_MATCH = re.compile(
    r"\b(?:no exact match|no (?:\w+ )?match(?:es|ing)?|"
    r"none (?:of (?:the|them|those) )?(?:\w+ )?(?:match|matched|meet|met|fit)|"
    r"couldn['’]?t find|didn['’]?t find|cannot find|can['’]?t find|could not find|did not find|"
    r"not finding|not seeing|don['’]?t see any|isn['’]?t listed|aren['’]?t listed|"
    r"(?:couldn['’]?t|can['’]?t|could not|cannot) verify|"
    r"don['’]?t (?:have|carry|see)|do not (?:have|carry|see)|doesn['’]?t (?:have|carry)|"
    r"isn['’]?t (?:one|any)|aren['’]?t any|there (?:are|is) no(?! (?:shortage|problem|need|worries|rush))|"
    r"we have no|"
    r"no (?:products?|results?|items?|options?))\b",
    re.IGNORECASE,
)
PERSON = re.compile(
    r"support case|a person\b|a human|real person|"
    r"someone (?:from|on) (?:our|the) (?:support )?team|"
    r"member of (?:our|the) (?:support )?team|support team|a specialist|an agent",
    re.IGNORECASE,
)
REFUND_CLAIM = re.compile(
    r"(?:I(?:['’]ve| have)|we(?:['’]ve| have)) "
    r"(?:refunded|(?:issued|processed|approved|confirmed|sent) (?:your|the|a) (?:refund|return))|"
    r"(?<!n['’]t )(?<!not )(?:has|have) been (?:refunded|issued|processed|approved)|"
    r"refund (?:is|has been) (?:on (?:its|the) way|issued|processed|approved|complete)"
    r"(?! (?:when|after|once|as soon|only|within|in \d|to your|back to))|"
    r"return (?:is|has been) (?:confirmed|created|approved|complete)(?! (?:only|when|after|once|until))|"
    r"refund of \$[\d.,]+ (?:is|was|has been) (?:issued|sent|processed|on (?:its|the) way)|"
    r"\bI (?:went ahead and |just |already )?(?:refunded|issued (?:the|your|a) refund|processed (?:the|your|a) refund)|"
    r"(?:I(?:['’]ve| have)|we(?:['’]ve| have)) (?:gone ahead and |just |already )?"
    r"(?:refunded|issued|processed|approved|sent)\b"
    r"(?![^.]{0,30}\b(?:quotes?|requests?|case|label|ticket|details)\b)",
    re.IGNORECASE,
)
# "No refund has been issued" / "before the refund is issued" aren't claims; a bare "no" earlier
# ("No problem, your refund has been issued") doesn't cancel one.
NOT_YET = re.compile(
    r"\b(?:before|until|once|when|after|if|whether)\b|\bno (?:\w+ ){0,2}(?:refund|return)s?\b",
    re.IGNORECASE,
)
# Saying an item is fine for someone's allergy, in any of the usual ways.
SAFE_WORDS = re.compile(
    r"\bsafe\b|\bfine for\b|\bok(?:ay)? for (?:your|him|her|them|you|someone|people)\b|"
    r"\ballergy[- ]friendly\b|\bgo ahead and (?:eat|enjoy|have|give|serve)\b|\bno risk\b|"
    r"\bnothing to worry\b",
    re.IGNORECASE,
)
# Things the customer must never read: tool plumbing, raw ids, untrusted-data wrappers, or a
# citation marker left over after the valid ones are taken out.
LEAK = re.compile(
    r"\[\[cite|untrusted_data|\b(?:search_products|get_product_details|list_my_orders|"
    r"get_order_status|get_return_options|quote_return|propose_return|get_refund_status|"
    r"search_policies|list_stores|handoff_to_person|quote_id|line_id|order_id|product_id|"
    r"variant_id)\b|\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
NEGATION = re.compile(
    r"\b(?:not|never|cannot|can['’]?t|couldn['’]?t|won['’]?t|isn['’]?t|aren['’]?t|unable|no way)\b"
    r"|n['’]t\b",
    re.IGNORECASE,
)


def normalize(text: str) -> str:
    return (
        text.replace("**", "")
        .replace("’", "'")
        .replace("‘", "'")
        .replace("‑", "-")
        .replace("‐", "-")
        .replace("–", "-")
        .replace("—", "-")
        .replace(" ", " ")
        .replace(" ", " ")
    )


def _clause_before(text: str, at: int) -> str:
    """The clause a match sits in, up to the match: a negation in an earlier clause ("It's not
    made with peanuts, so it's safe") doesn't negate this one."""
    start = max(text.rfind(c, 0, at) for c in ".!?\n;,") + 1
    clause = text[start:at]
    joiner = re.search(r".*\b(?:so|and|but|which means)\b", clause, re.IGNORECASE)
    return clause[joiner.end() :] if joiner else clause


def refund_claim(text: str) -> bool:
    """Says a refund or return went through, rather than that it hasn't (or will once...)."""
    for m in REFUND_CLAIM.finditer(text):
        sentence_start = max(text.rfind(c, 0, m.start()) for c in ".!?\n") + 1
        before = text[sentence_start : m.start()]
        if not (NOT_YET.search(before + m.group(0)) or NEGATION.search(_clause_before(text, m.start()))):
            return True
    return False


def safety_claim(text: str) -> bool:
    """Says an item *is* safe or fine for an allergy, rather than that it can't say so."""
    for m in SAFE_WORDS.finditer(text):
        if not NEGATION.search(_clause_before(text, m.start())):
            return True
    return False


# Where the chat assistant is reached: through the web app, or directly (--assistant).
ASSISTANT = "/api/assistant"


def turn(
    client: httpx.Client, conversation: str, text: str, headers: dict[str, str] | None = None
) -> dict[str, Any]:
    events: list[tuple[str, Any]] = []
    started = time.perf_counter()
    first_text_ms = None
    with client.stream(
        "POST",
        f"{ASSISTANT}/conversations/{conversation}/messages",
        json={"text": text},
        headers=headers,
        timeout=180,
    ) as resp:
        resp.raise_for_status()
        event = None
        for line in resp.iter_lines():
            if line.startswith("event: "):
                event = line[7:]
            elif line.startswith("data: ") and event:
                events.append((event, json.loads(line[6:])))
                if event == "text" and first_text_ms is None:
                    first_text_ms = round((time.perf_counter() - started) * 1000)
    turn_ms = round((time.perf_counter() - started) * 1000)
    citations = next((d for e, d in events if e == "citations"), {"valid": [], "invalid": []})
    return {
        "text": normalize("".join(d["delta"] for e, d in events if e == "text")),
        "cards": [d for e, d in events if e == "card"],
        "quotes": [d for e, d in events if e == "quote"],
        "tools": [d["tool"] for e, d in events if e == "status"],
        "citations": citations.get("valid", []),
        "invalid_citations": citations.get("invalid", []),
        "errors": [d.get("message") for e, d in events if e == "error"],
        "done": next((d for e, d in events if e == "done"), {}),
        "first_text_ms": first_text_ms,
        "turn_ms": turn_ms,
    }


def turn_contexts(messages: list[Any], texts: list[str]) -> list[dict[str, Any]]:
    """For each customer turn, the tool calls the model made and what the tools returned (the
    policy prefetch is recorded as a search_policies call), read from the conversation's
    checkpoint. That's the evidence an answer should rest on. Turns are matched to the
    customer's messages by their text; a turn not found gets nothing."""
    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

    out: list[dict[str, Any]] = [{"contexts": [], "tool_calls": []} for _ in texts]
    i = -1
    for m in messages:
        if isinstance(m, HumanMessage):
            said = m.content if isinstance(m.content, str) else json.dumps(m.content)
            nxt = i + 1
            i = nxt if nxt < len(texts) and texts[nxt].strip() in said else i
        elif i >= 0 and isinstance(m, AIMessage):
            out[i]["tool_calls"] += [{"name": c["name"], "args": c["args"]} for c in m.tool_calls]
        elif i >= 0 and isinstance(m, ToolMessage):
            content = m.content if isinstance(m.content, str) else json.dumps(m.content)
            out[i]["contexts"].append({"tool": m.name, "content": content[:CONTEXT_CHARS]})
    return out


_chat_graph: Any = None
_chat_graph_lock = threading.Lock()


def chat_messages(conversation: str) -> list[Any]:
    """The chat conversation's messages from the assistant's own checkpoint store (the eval
    runs in the assistant's environment; the API shows customers only the visible turns)."""
    global _chat_graph
    with _chat_graph_lock:
        if _chat_graph is None:
            from langgraph.checkpoint.postgres import PostgresSaver
            from psycopg.rows import dict_row
            from psycopg_pool import ConnectionPool

            from assistant.config import get_settings
            from assistant.graph import build_graph

            pool = ConnectionPool(
                get_settings().psycopg_dsn,
                min_size=1,
                max_size=4,
                kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
            )
            _chat_graph = build_graph(PostgresSaver(pool))  # type: ignore[arg-type]
    snap = _chat_graph.get_state({"configurable": {"thread_id": conversation}})
    return (snap.values or {}).get("messages", []) if snap else []


def tracer() -> Any:
    """Spans for cases and turns, exported only when OTEL_EXPORTER_OTLP_ENDPOINT is set; the
    W3C trace id is recorded on every turn either way, and chat requests carry it."""
    import os

    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider

    provider = TracerProvider(resource=Resource.create({"service.name": "xana-eval"}))
    if os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
    return trace.get_tracer("xana-eval")


TRACER: Any = None


def traceparent(span: Any) -> tuple[dict[str, str], str]:
    ctx = span.get_span_context()
    trace_id = f"{ctx.trace_id:032x}"
    return {"traceparent": f"00-{trace_id}-{ctx.span_id:016x}-01"}, trace_id


_details: dict[str, dict[str, Any]] = {}
_details_lock = threading.Lock()


def product_detail(client: httpx.Client, product_id: str) -> dict[str, Any]:
    with _details_lock:
        if product_id in _details:
            return _details[product_id]
    resp = client.get(f"/api/v1/products/{product_id}")
    resp.raise_for_status()
    with _details_lock:
        _details[product_id] = resp.json()
    return _details[product_id]


def cited(got: dict[str, Any], wanted: str) -> bool:
    for c in got["citations"]:
        cite = c["cite"]
        if cite == wanted or cite.split("#")[0] == wanted:
            return True
    return False


_orders: dict[tuple[int, str], dict[str, Any]] = {}


def order_detail(client: httpx.Client, order_id: str) -> dict[str, Any]:
    key = (id(client), order_id)
    with _details_lock:
        if key in _orders:
            return _orders[key]
    resp = client.get(f"/api/v1/orders/{order_id}")
    resp.raise_for_status()
    with _details_lock:
        _orders[key] = resp.json()
    return _orders[key]


STORE_TZ = ZoneInfo("America/Chicago")


def day_re(iso: str | None) -> str:
    """A date as the customer may read it: "Oct 6", "October 6th", "10/6", or today/yesterday/
    tomorrow when it is one of those (in the store's time zone, like the site)."""
    if not iso:
        return r"(?!x)x"
    d = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(STORE_TZ).date()
    month = d.strftime("%B")
    alts = [rf"{month[:3]}(?:{month[3:]})?\.?\s+{d.day}(?:st|nd|rd|th)?\b", rf"\b{d.month}/0?{d.day}\b",
            rf"\b{d.day}(?:st|nd|rd|th)? of {month}"]  # fmt: skip
    today = datetime.now(STORE_TZ).date()
    offset = (d - today).days
    if offset in (-1, 0, 1):
        alts.append({-1: r"\byesterday\b", 0: r"\btoday\b", 1: r"\btomorrow\b"}[offset])
    return "(?:" + "|".join(alts) + ")"


DIGIT_WORDS = ["zero|oh", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]


def spoken_code(code: str) -> str:
    """An order or tracking number as written ("SW136076") or read out ("S W one three six…")."""
    parts = [f"(?:{c}|{DIGIT_WORDS[int(c)]})" if c.isdigit() else re.escape(c) for c in code]
    return r"[\s,-]{0,2}".join(parts)


def order_fact_re(client: httpx.Client, fact: dict[str, Any]) -> str:
    """The regex for one live fact about one of the customer's orders (read from the store, so
    dates follow the last reseed)."""
    d = order_detail(client, fact["order_id"])
    ship = (d.get("shipments") or [{}])[0]
    field = fact["field"]
    if field == "tracking_number":
        return spoken_code(ship["tracking_number"])
    if field == "carrier":
        return re.escape(ship["carrier"])
    if field == "arriving_by":
        return day_re(ship.get("estimated_delivery_at") or d.get("estimated_delivery_at"))
    if field == "delivered_on":
        return day_re(d.get("delivered_at"))
    if field == "placed_on":
        return day_re(d.get("placed_at"))
    if field == "total":
        m = d["total_minor"]
        return re.escape(f"${m // 100:,}.{m % 100:02d}")
    raise ValueError(f"unknown order fact {field}")


def score(expect: dict[str, Any], got: dict[str, Any], client: httpx.Client) -> dict[str, bool]:
    checks: dict[str, bool] = {}
    action = expect.get("action")
    text = got["text"]
    lower = text.lower()
    products = [c for c in got["cards"] if c.get("kind") == "product"]
    titles = [c.get("title", "") for c in products]
    tools = got["tools"]
    checks["no_error"] = not got["errors"] and bool(text or got["quotes"] or got["cards"])
    # Answer quality on every turn: nothing internal on screen, and no citation of a section
    # the turn didn't read.
    valid = {c["cite"] for c in got["citations"]}
    shown_text = re.sub(
        r"\[\[cite:([^\]]+)\]\]",
        lambda m: "" if m.group(1) in valid or m.group(1).split("#")[0] in valid else m.group(0),
        text,
    )
    checks["clean"] = not LEAK.search(shown_text)
    checks["valid_cites"] = not got["invalid_citations"]

    if action == "search":
        checks["uses_catalog"] = "search_products" in tools
    elif action == "product_details":
        # A follow-up about the product just discussed may be answered from the details read a
        # turn ago (faster, and still the listing's facts, which the facts check verifies).
        checks["uses_catalog"] = bool(
            {"search_products", "get_product_details"} & set(tools)
        ) or bool(expect.get("from_context"))
    if expect.get("product_title"):
        want = expect["product_title"].lower()
        checks["right_product"] = want in lower or any(t.lower() == want for t in titles)

    search = expect.get("search") or {}
    if expect.get("expect_empty"):
        checks["empty"] = not products
        if expect.get("must_not_claim_match"):
            checks["says_no_match"] = bool(NO_MATCH.search(text))
    elif search and expect.get("all_results_match"):

        def ok(card: dict[str, Any]) -> bool:
            tags = {t["value"] for t in card["tags"]}
            types = search.get("product_type")
            return (
                (not types or card["product_type"] in types)
                and set(search.get("tags", [])) <= tags
                and not (set(search.get("exclude_tags", [])) & tags)
                and (
                    "max_price_minor" not in search
                    or card["price_minor"] <= search["max_price_minor"]
                )
                and (
                    "min_price_minor" not in search
                    or card["price_minor"] >= search["min_price_minor"]
                )
            )

        checks["filters"] = bool(products) and all(ok(c) for c in products)

    constraints = expect.get("result_constraints") or {}
    if (
        constraints
        and not expect.get("expect_empty")
        and (expect.get("all_results_match") or products)
    ):

        def detail_ok(card: dict[str, Any]) -> bool:
            product = product_detail(client, card["id"])
            specs = product.get("specs") or {}
            allergens = {a.lower() for a in product.get("allergens") or []}
            return (
                all(
                    w.lower() in product["title"].lower()
                    for w in constraints.get("title_contains", [])
                )
                and all(specs.get(k) == v for k, v in constraints.get("specs", {}).items())
                and not (allergens & {a.lower() for a in constraints.get("allergens_none", [])})
                and (
                    "variant_code" not in constraints
                    or any(
                        v["sku"].endswith("-" + constraints["variant_code"])
                        for v in product.get("variants", [])
                    )
                )
            )

        checks["details"] = bool(products) and all(detail_ok(c) for c in products)

    if expect.get("winner_words") is not None:
        # Two named products: the answer names the winner first ("X has more ..., versus Y").
        def first_at(words: list[str]) -> int:
            spots = [m.start() for w in words for m in re.finditer(rf"\b{re.escape(w)}\b", text, re.I)]
            return min(spots, default=len(text) + 1)

        lose = first_at(expect["loser_words"])
        if expect["winner_words"]:
            win = first_at(expect["winner_words"])
            checks["right_winner"] = win <= len(text) and win < lose
        else:
            # The winner's name is all in the other's ("Sour Cream" vs "Light Sour Cream"): the
            # other one must not be the one said to have more.
            comparative = re.search(r"\b(?:more|higher|fewer|less|lower|cheaper|pricier|most)\b", text, re.I)
            checks["right_winner"] = bool(comparative) and comparative.start() < lose
    elif expect.get("winner_title"):
        # The winner is the first product the answer names (a list that merely includes it
        # doesn't pass), or the first card when the answer names none.
        want = expect["winner_title"].lower()
        named = sorted((lower.find(t.lower()), t.lower()) for t in titles if t and t.lower() in lower)
        if named:
            checks["right_winner"] = named[0][1] == want
        else:
            checks["right_winner"] = (
                want in lower
                or (bool(titles) and titles[0].lower() == want)
                or bool(expect.get("winner_re") and re.search(expect["winner_re"], text, re.I))
            )

    # What the customer reads: the answer, plus a quote card's read-back and timing, and a
    # support case card's message.
    shown = [text]
    for q in got["quotes"]:
        shown.append(q.get("readback", ""))
        shown += [ln.get("timing_message") or "" for ln in q.get("lines", [])]
    shown += [c.get("message", "") for c in got["cards"] if c.get("kind") == "handoff"]
    visible = normalize("\n".join(shown))
    # A quote_or_clarify turn that gave the right quote is scored on the quote; its facts are
    # what the clarifying question must name.
    quoted_instead = action == "quote_or_clarify" and bool(got["quotes"])
    facts = [
        bool(re.search(p, visible, re.IGNORECASE))
        for p in ([] if quoted_instead else expect.get("mentions_re") or [])
    ]
    if expect.get("mentions_code"):
        facts.append(bool(re.search(spoken_code(expect["mentions_code"]), visible, re.IGNORECASE)))
    if expect.get("mentions"):
        facts += [m.lower() in visible.lower() for m in expect["mentions"]]
    if facts:
        checks["facts"] = all(facts)
    if expect.get("mentions_any_re"):
        checks["facts_any"] = any(
            re.search(p, visible, re.IGNORECASE) for p in expect["mentions_any_re"]
        )
    if expect.get("mentions_any"):
        checks["facts_any_words"] = any(m.lower() in lower for m in expect["mentions_any"])
    forbidden = [
        m.lower() in lower or any(m.lower() in t.lower() for t in titles)
        for m in expect.get("must_not_mention") or []
    ]
    forbidden += [
        bool(re.search(p, text, re.IGNORECASE)) for p in expect.get("must_not_mention_re") or []
    ]
    if forbidden:
        checks["nothing_wrong"] = not any(forbidden)
    if expect.get("no_safety_claim"):
        checks["no_safety_claim"] = not safety_claim(text)
    if expect.get("no_refund_claim"):
        checks["no_refund_claim"] = not refund_claim(text)

    if expect.get("cite"):
        checks["cites"] = all(cited(got, c) for c in expect["cite"])
    if expect.get("cite_any"):
        checks["cites"] = any(cited(got, c) for c in expect["cite_any"])
    if "cites" in checks and not checks["cites"] and expect.get("cite_ok_if"):
        # Answered from the customer's own order, or handed to a person: no citation needed.
        ok_if = set(expect["cite_ok_if"])
        checks["cites"] = (
            bool(ok_if & set(tools))
            or ("handoff" in ok_if and any(c.get("kind") == "handoff" for c in got["cards"]))
            or ("person" in ok_if and bool(PERSON.search(text)))
        )
    for tool in expect.get("uses") or []:
        checks[f"uses_{tool}"] = tool in tools
    if expect.get("uses_any"):
        checks["uses_any"] = bool(set(expect["uses_any"]) & set(tools))
    if expect.get("not_uses"):
        checks["not_uses"] = not (set(expect["not_uses"]) & set(tools))
    if expect.get("order_facts"):
        checks["order_facts"] = all(
            re.search(order_fact_re(client, f), visible, re.IGNORECASE)
            for f in expect["order_facts"]
        )
    if expect.get("no_product_cards"):
        checks["no_product_cards"] = not products

    if expect.get("offers_person"):
        checks["person"] = any(c.get("kind") == "handoff" for c in got["cards"]) or bool(
            PERSON.search(text)
        )

    quote = expect.get("quote")

    def check_quote(q: dict[str, Any]) -> None:
        if not quote:
            checks["quote_expected"] = False  # a quote where the case expects none
            return
        want_lines = sorted((ln["title"], ln["quantity"]) for ln in quote["lines"])
        checks["quote_lines"] = want_lines == sorted((ln["title"], ln["quantity"]) for ln in q["lines"])
        checks["quote_refund"] = q["total_refund_minor"] == quote["refund_minor"]
        if "shipping_refunded" in quote and q.get("shipping_refund_minor") is not None:
            checks["quote_shipping"] = (q["shipping_refund_minor"] > 0) == quote["shipping_refunded"]

    if action == "quote" and quote:
        q = got["quotes"][-1] if got["quotes"] else None
        checks["quote"] = q is not None
        if q is not None:
            check_quote(q)
    if action == "quote_or_offer":
        if got["quotes"]:
            check_quote(got["quotes"][-1])
        else:
            checks["offers_return"] = (
                (
                    "get_return_options" in tools
                    or "list_my_orders" in tools
                    or bool(re.search(r"\breturnable\b", text, re.I))
                )
                and bool(re.search(r"\beligible\b|can (?:be )?return|\byes\b", text, re.I))
            ) or bool(
                re.search(
                    r"(?:want|like) (?:me )?to (?:start (?:a|the) )?return|start (?:a|the) return|"
                    r"(?:want|like) me to (?:start|set up|do) (?:that|it|one|this|a refund|the refund)|"
                    r"set up (?:a|the) return|shall I (?:start|return)",
                    text,
                    re.I,
                )
            )
    if action == "quote_or_clarify":
        # Either the right quote, or a question that names every item that could be meant.
        if got["quotes"]:
            check_quote(got["quotes"][-1])
        else:
            pats = expect.get("clarify_re") or []
            # Names what could be meant; with nothing to name, it at least asks.
            checks["asks_which"] = (
                all(re.search(p, visible, re.IGNORECASE) for p in pats) if pats else "?" in visible
            )
    if action in ("refuse", "clarify"):
        checks["no_quote"] = not got["quotes"]
    if action == "handoff":
        checks["person"] = any(c.get("kind") == "handoff" for c in got["cards"]) or bool(
            PERSON.search(text)
        )
    return checks


class Session:
    """One signed-in web client per customer, per worker thread."""

    def __init__(self, web: str) -> None:
        self.web = web
        self.local = threading.local()

    def client(self, user: str) -> httpx.Client:
        clients = getattr(self.local, "clients", None)
        if clients is None:
            clients = self.local.clients = {}
        if user not in clients:
            c = httpx.Client(base_url=self.web, timeout=60)
            c.post(
                "/api/v1/auth/sign-in", json={"email": user, "password": PASSWORDS[user]}
            ).raise_for_status()
            clients[user] = c
        return clients[user]


def run_case(case: dict[str, Any], session: Session, agent: str, channel: str) -> dict[str, Any]:
    with TRACER.start_as_current_span(
        "eval.case",
        attributes={"eval.case_id": case["id"], "eval.set": case["set"],
                    "eval.category": case["category"], "eval.channel": channel},
    ) as span:  # fmt: skip
        result = _run_case(case, session, agent, channel)
        if result.get("error_kind") == "infra":
            result = _run_case(case, session, agent, channel)
        span.set_attribute("eval.passed", result["passed"])
        failed = sorted({k for t in result["turns"] for k, v in t["checks"].items() if not v})
        span.set_attribute("eval.failed_checks", failed or ([result["error"]] if result.get("error") else []))
        return result


def _run_case(case: dict[str, Any], session: Session, agent: str, channel: str) -> dict[str, Any]:
    client = session.client(case["user"])
    started = time.perf_counter()
    texts = [t["user"] for t in case["turns"]]
    try:
        if channel == "voice":
            from xana_voice import voice_turns

            spoken = voice_turns(client, texts)
            for got in spoken:
                got["text"] = normalize(got["text"])
        else:
            conv = client.post(f"{ASSISTANT}/conversations", json={"agent": agent}).json()["id"]
        turns = []
        gots = []
        for i, t in enumerate(case["turns"]):
            with TRACER.start_as_current_span("eval.turn", attributes={"eval.turn": i}) as tspan:
                headers, trace_id = traceparent(tspan)
                got = spoken[i] if channel == "voice" else turn(client, conv, t["user"], headers)
                got["trace_id"] = trace_id
                tspan.set_attribute("eval.first_text_ms", got.get("first_text_ms") or -1)
                tspan.set_attribute("eval.turn_ms", got.get("turn_ms") or -1)
            gots.append(got)
        if channel == "voice":
            found = [{"contexts": g.get("contexts", []), "tool_calls": g.get("tool_calls", [])}
                     for g in gots]  # fmt: skip
        else:
            try:
                found = turn_contexts(chat_messages(conv), texts)
            except Exception as exc:  # noqa: BLE001 - scoring doesn't need it
                print(f"contexts not read for {case['id']}: {type(exc).__name__}: {exc}", flush=True)
                found = [{"contexts": [], "tool_calls": []} for _ in texts]
        for i, t in enumerate(case["turns"]):
            got = gots[i]
            checks = score(t["expect"], got, client)
            turns.append(
                {
                    "user": t["user"],
                    "action": t["expect"].get("action"),
                    "checks": checks,
                    "passed": all(checks.values()),
                    "answer": got["text"],
                    "tools": got["tools"],
                    "products": [
                        c.get("title") for c in got["cards"] if c.get("kind") == "product"
                    ],
                    "other_cards": [
                        c.get("kind") for c in got["cards"] if c.get("kind") != "product"
                    ],
                    "quote": (
                        {
                            "refund_minor": got["quotes"][-1]["total_refund_minor"],
                            "lines": [
                                (ln["title"], ln["quantity"]) for ln in got["quotes"][-1]["lines"]
                            ],
                        }
                        if got["quotes"]
                        else None
                    ),
                    "citations": [c["cite"] for c in got["citations"]],
                    "invalid_citations": got["invalid_citations"],
                    "tool_calls": found[i]["tool_calls"],
                    "contexts": found[i]["contexts"],
                    "trace_id": got.get("trace_id"),
                    "escalated": got.get("escalated"),
                    "first_text_ms": got.get("first_text_ms"),
                    "turn_ms": got.get("turn_ms"),
                    "errors": got["errors"],
                    "model": got["done"].get("model"),
                }
            )
    except Exception as exc:  # a crash is a failed case, not a failed run
        # infra: the stack or a provider failed (retried once); harness: a bug in this eval.
        infra = isinstance(exc, (httpx.HTTPError, TimeoutError, ConnectionError))
        return {
            "id": case["id"],
            "set": case["set"],
            "user": case["user"],
            "category": case["category"],
            "passed": False,
            "turns": [],
            "error": f"{type(exc).__name__}: {exc}",
            "error_kind": "infra" if infra else "harness",
            "seconds": time.perf_counter() - started,
        }
    return {
        "id": case["id"],
        "set": case["set"],
        "user": case["user"],
        "category": case["category"],
        "passed": all(t["passed"] for t in turns),
        "turns": turns,
        "seconds": round(time.perf_counter() - started, 1),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--set",
        default="all",
        help="all, core (products and returns), batches, or set names joined by commas: "
        + ", ".join(SETS),
    )
    parser.add_argument(
        "--file",
        action="append",
        default=[],
        help="a case file outside the sets (e.g. evals/xana/locked/*.jsonl); repeatable, "
        "and replaces --set",
    )
    parser.add_argument("--web", default="http://127.0.0.1:3100")
    parser.add_argument("--assistant", default=None)
    parser.add_argument("--agent", choices=("xana", "steph"), default="xana")
    parser.add_argument("--only")
    parser.add_argument("--category")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--channel", choices=("chat", "voice"), default="chat")
    parser.add_argument("--record-baseline", action="store_true")
    args = parser.parse_args()

    groups = {"all": list(SETS), "core": list(CORE), "batches": list(BATCHES), "support": list(SUPPORT)}
    files = {**SETS, **SUPPORT}
    if args.file:
        files = {Path(f).stem: Path(f) for f in args.file}
        names = list(files)
        args.set = "+".join(names)
    else:
        names = groups.get(args.set) or args.set.split(",")
    unknown = [n for n in names if n not in files]
    if unknown:
        parser.error(f"unknown set {unknown}; known: {', '.join(files)}")
    cases = [
        {**json.loads(line), "set": n}
        for n in names
        for line in files[n].read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if args.only:
        wanted = set(args.only.split(","))
        cases = [c for c in cases if c["id"] in wanted]
    if args.category:
        kinds = set(args.category.split(","))
        cases = [c for c in cases if c["category"] in kinds]
    if args.channel == "voice":
        # A spoken yes goes to the call's confirmation rule, not the brain: chat-only cases.
        cases = [
            c for c in cases if not any(re.match(r"yes\b", t["user"], re.I) for t in c["turns"])
        ]
        sys.path.insert(0, str(ROOT / "evals"))

    global ASSISTANT
    if args.assistant:
        ASSISTANT = f"{args.assistant.rstrip('/')}/v1/assistant"
    global TRACER
    TRACER = tracer()
    session = Session(args.web)
    results: list[dict[str, Any]] = []
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_case, c, session, args.agent, args.channel): c for c in cases}
        for fut in as_completed(futures):
            r = fut.result()
            results.append(r)
            failed = sorted({k for t in r["turns"] for k, v in t["checks"].items() if not v})
            detail = r.get("error") or ", ".join(failed)
            first = futures[fut]["turns"][0]["user"][:60]
            print(f"{'PASS' if r['passed'] else 'FAIL'} {r['id']:<7} {r['category']:<14} {first}"
                  + (f"  ({detail})" if detail else ""), flush=True)  # fmt: skip
    results.sort(key=lambda r: r["id"])

    model = next((t["model"] for r in results for t in r["turns"] if t.get("model")), "?")
    summary: dict[str, Any] = {
        "agent": args.agent,
        "channel": args.channel,
        "model": model,
        "date": datetime.now(ZoneInfo("America/Chicago")).date().isoformat(),
        "sets": {},
    }
    for n in names:
        rs = [r for r in results if r["set"] == n]
        if not rs:
            continue
        by_cat: dict[str, list[bool]] = defaultdict(list)
        by_check: dict[str, list[bool]] = defaultdict(list)
        for r in rs:
            by_cat[r["category"]].append(r["passed"])
            for t in r["turns"]:
                for k, v in t["checks"].items():
                    by_check[k].append(v)
        ok = sum(r["passed"] for r in rs)
        crashed = {k: sum(r.get("error_kind") == k for r in rs) for k in ("infra", "harness")}
        summary["sets"][n] = {
            "passed": ok,
            "total": len(rs),
            "accuracy": round(ok / len(rs), 4),
            "crashed": crashed,
            "categories": {k: [sum(v), len(v)] for k, v in sorted(by_cat.items())},
            "checks": {k: [sum(v), len(v)] for k, v in sorted(by_check.items())},
            "failed": [r["id"] for r in rs if not r["passed"]],
        }
        print(f"\n{n}: {ok}/{len(rs)} ({ok / len(rs):.1%})  model: {model}"
              + (f"  crashed: {crashed}" if any(crashed.values()) else ""))  # fmt: skip
        for k, v in sorted(by_cat.items()):
            print(f"  {k:<16} {sum(v):>3}/{len(v):<3}")
        print("  checks:", ", ".join(f"{k} {sum(v)}/{len(v)}" for k, v in sorted(by_check.items())))
    print(f"\ntime: {time.perf_counter() - started:.0f}s with {args.workers} workers")

    runs = ROOT / "evals/xana/runs"
    runs.mkdir(parents=True, exist_ok=True)
    out = runs / f"{datetime.now():%Y%m%d-%H%M%S}-{args.channel}-{args.set}.json"
    report = {"summary": summary, "results": results}
    out.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(f"transcripts: {out.relative_to(ROOT)}")
    if args.record_baseline and not (args.only or args.category):
        base = ROOT / "evals/baselines" / f"xana-{args.channel}-{args.set}-{model}.json"
        base.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"baseline saved to {base.relative_to(ROOT)}")
    from opentelemetry import trace

    getattr(trace.get_tracer_provider(), "shutdown", lambda: None)()
    sys.exit(0 if all(r["passed"] for r in results) else 1)


if __name__ == "__main__":
    main()
