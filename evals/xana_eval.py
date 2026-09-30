"""Xana golden-set eval: 200 product questions and 200 return/refund questions, live.

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

Each run writes every case's transcript to evals/xana/runs/ (gitignored) for failure review.
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

import httpx

ROOT = Path(__file__).resolve().parents[1]
SETS = {
    "products": ROOT / "evals/xana/products.jsonl",
    "returns": ROOT / "evals/xana/returns.jsonl",
}
PASSWORDS = {"alice@example.com": "alice-dev-password", "bob@example.com": "bob-dev-password"}

NO_MATCH = re.compile(
    r"\b(?:no exact match|no (?:\w+ )?match(?:es|ing)?|"
    r"none (?:of (?:the|them|those) )?(?:\w+ )?(?:match|matched|meet|met|fit)|"
    r"couldn['’]?t find|didn['’]?t find|cannot find|can['’]?t find|could not find|did not find|"
    r"not finding|not seeing|don['’]?t see any|isn['’]?t listed|aren['’]?t listed|"
    r"don['’]?t (?:have|carry|see)|do not (?:have|carry|see)|doesn['’]?t (?:have|carry)|"
    r"isn['’]?t (?:one|any)|aren['’]?t any|there (?:are|is) no|we have no|"
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
    r"return (?:is|has been) (?:confirmed|created|approved|complete)|"
    r"your refund of \$[\d.,]+ (?:is|was) (?:issued|sent)",
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


def refund_claim(text: str) -> bool:
    """Says a refund or return went through, rather than that it hasn't."""
    for m in REFUND_CLAIM.finditer(text):
        sentence_start = max(text.rfind(".", 0, m.start()), text.rfind("\n", 0, m.start())) + 1
        before = text[sentence_start : m.start()]
        conditional = re.search(r"\b(?:no|before|until|once|when|after|if)\b", before, re.I)
        if not (conditional or NEGATION.search(before)):
            return True
    return False


def safety_claim(text: str) -> bool:
    """Says an item *is* safe (for an allergy), rather than that it can't say so."""
    for m in re.finditer(r"\bsafe\b", text, re.IGNORECASE):
        sentence_start = max(text.rfind(".", 0, m.start()), text.rfind("\n", 0, m.start())) + 1
        if not NEGATION.search(text[sentence_start : m.start()]):
            return True
    return False


# Where the chat assistant is reached: through the web app, or directly (--assistant).
ASSISTANT = "/api/assistant"


def turn(client: httpx.Client, conversation: str, text: str) -> dict[str, Any]:
    events: list[tuple[str, Any]] = []
    started = time.perf_counter()
    first_text_ms = None
    with client.stream(
        "POST",
        f"{ASSISTANT}/conversations/{conversation}/messages",
        json={"text": text},
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


def score(expect: dict[str, Any], got: dict[str, Any], client: httpx.Client) -> dict[str, bool]:
    checks: dict[str, bool] = {}
    action = expect.get("action")
    text = got["text"]
    lower = text.lower()
    products = [c for c in got["cards"] if c.get("kind") == "product"]
    titles = [c.get("title", "") for c in products]
    tools = got["tools"]
    checks["no_error"] = not got["errors"] and bool(text or got["quotes"] or got["cards"])

    if action == "search":
        checks["uses_catalog"] = "search_products" in tools
    elif action == "product_details":
        checks["uses_catalog"] = bool({"search_products", "get_product_details"} & set(tools))
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

    if expect.get("winner_title"):
        want = expect["winner_title"].lower()
        checks["right_winner"] = (
            want in lower
            or (bool(titles) and titles[0].lower() == want)
            or bool(expect.get("winner_re") and re.search(expect["winner_re"], text, re.IGNORECASE))
        )

    # What the customer reads: the answer, plus a quote card's read-back and timing, and a
    # support case card's message.
    shown = [text]
    for q in got["quotes"]:
        shown.append(q.get("readback", ""))
        shown += [ln.get("timing_message") or "" for ln in q.get("lines", [])]
    shown += [c.get("message", "") for c in got["cards"] if c.get("kind") == "handoff"]
    visible = normalize("\n".join(shown))
    facts = [bool(re.search(p, visible, re.IGNORECASE)) for p in expect.get("mentions_re", [])]
    if expect.get("mentions"):
        facts += [m.lower() in visible.lower() for m in expect["mentions"]]
    if facts:
        checks["facts"] = all(facts)
    if expect.get("mentions_any_re"):
        checks["facts_any"] = any(
            re.search(p, visible, re.IGNORECASE) for p in expect["mentions_any_re"]
        )
    if expect.get("mentions_any"):
        checks["facts_any"] = any(m.lower() in lower for m in expect["mentions_any"])
    forbidden = [
        m.lower() in lower or any(m.lower() in t.lower() for t in titles)
        for m in expect.get("must_not_mention", [])
    ]
    forbidden += [
        bool(re.search(p, text, re.IGNORECASE)) for p in expect.get("must_not_mention_re", [])
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
    for tool in expect.get("uses", []):
        checks[f"uses_{tool}"] = tool in tools

    if expect.get("offers_person"):
        checks["person"] = any(c.get("kind") == "handoff" for c in got["cards"]) or bool(
            PERSON.search(text)
        )

    quote = expect.get("quote")
    if action == "quote" and quote:
        q = got["quotes"][-1] if got["quotes"] else None
        checks["quote"] = q is not None
        if q is not None:
            want_lines = sorted((ln["title"], ln["quantity"]) for ln in quote["lines"])
            got_lines = sorted((ln["title"], ln["quantity"]) for ln in q["lines"])
            checks["quote_lines"] = want_lines == got_lines
            checks["quote_refund"] = q["total_refund_minor"] == quote["refund_minor"]
    if action == "quote_or_offer":
        if got["quotes"]:
            q = got["quotes"][-1]
            want_lines = sorted((ln["title"], ln["quantity"]) for ln in quote["lines"])
            checks["quote_lines"] = want_lines == sorted(
                (ln["title"], ln["quantity"]) for ln in q["lines"]
            )
            checks["quote_refund"] = q["total_refund_minor"] == quote["refund_minor"]
        else:
            checks["offers_return"] = (
                "get_return_options" in tools or bool(re.search(r"\breturnable\b", text, re.I))
            ) and bool(re.search(r"\beligible\b|can (?:be )?return|\byes\b", text, re.I))
    if action in ("refuse", "clarify"):
        checks["no_quote"] = not got["quotes"]
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
    client = session.client(case["user"])
    started = time.perf_counter()
    try:
        if channel == "voice":
            from xana_voice import voice_turns

            spoken = voice_turns(client, [t["user"] for t in case["turns"]])
            for got in spoken:
                got["text"] = normalize(got["text"])
        else:
            conv = client.post(f"{ASSISTANT}/conversations", json={"agent": agent}).json()["id"]
        turns = []
        for i, t in enumerate(case["turns"]):
            got = spoken[i] if channel == "voice" else turn(client, conv, t["user"])
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
                    "tool_calls": got.get("tool_calls", []),
                    "escalated": got.get("escalated"),
                    "first_text_ms": got.get("first_text_ms"),
                    "turn_ms": got.get("turn_ms"),
                    "errors": got["errors"],
                    "model": got["done"].get("model"),
                }
            )
    except Exception as exc:  # a crash is a failed case, not a failed run
        return {
            "id": case["id"],
            "category": case["category"],
            "passed": False,
            "turns": [],
            "error": f"{type(exc).__name__}: {exc}",
            "seconds": time.perf_counter() - started,
        }
    return {
        "id": case["id"],
        "category": case["category"],
        "passed": all(t["passed"] for t in turns),
        "turns": turns,
        "seconds": round(time.perf_counter() - started, 1),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--set", choices=("products", "returns", "all"), default="all")
    parser.add_argument("--web", default="http://127.0.0.1:3100")
    parser.add_argument("--assistant", default=None)
    parser.add_argument("--agent", choices=("xana", "steph"), default="xana")
    parser.add_argument("--only")
    parser.add_argument("--category")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--channel", choices=("chat", "voice"), default="chat")
    parser.add_argument("--record-baseline", action="store_true")
    args = parser.parse_args()

    names = ["products", "returns"] if args.set == "all" else [args.set]
    cases = [
        json.loads(line)
        for n in names
        for line in SETS[n].read_text(encoding="utf-8").splitlines()
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
        "sets": {},
    }
    for n in names:
        prefix = "xp-" if n == "products" else "xr-"
        rs = [r for r in results if r["id"].startswith(prefix)]
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
        summary["sets"][n] = {
            "passed": ok,
            "total": len(rs),
            "accuracy": round(ok / len(rs), 4),
            "categories": {k: [sum(v), len(v)] for k, v in sorted(by_cat.items())},
            "checks": {k: [sum(v), len(v)] for k, v in sorted(by_check.items())},
            "failed": [r["id"] for r in rs if not r["passed"]],
        }
        print(f"\n{n}: {ok}/{len(rs)} ({ok / len(rs):.1%})  model: {model}")
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
    sys.exit(0 if all(r["passed"] for r in results) else 1)


if __name__ == "__main__":
    main()
