"""Assistant conversation eval: run labeled product Q&A through a live assistant.

Run with the stack up (``pnpm dev``), from the repo root:
  uv run --directory services/assistant python ../../evals/assistant_eval.py
  --web http://localhost:3000     the web app (the assistant is reached through /api/assistant)
  --agent xana                   score Xena's product answers (default: Steph)
  --only qa-001,qa-002            run some scripts
  --record-baseline               save as evals/baselines/assistant-<model>.json

Scored from what the customer sees, not from the model's text alone:
  filters      every product card matches the expected type and tags (and none of the excluded tags)
  details      shown products meet labeled specification, allergen, title, and option constraints
  tool use     product searches and detail questions call the corresponding catalog tool
  empty        when a script expects no exact match, no product card is shown
  mentions     required words appear in the answer; forbidden ones don't
  cites        the expected policy documents are among the answer's valid citations
Signs in as each script's user with the development password.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "evals" / "assistant" / "product_qa.jsonl"
PASSWORDS = {"alice@example.com": "alice-dev-password", "bob@example.com": "bob-dev-password"}


def turn(client: httpx.Client, conversation: str, text: str) -> dict[str, Any]:
    events: list[tuple[str, Any]] = []
    with client.stream(
        "POST",
        f"/api/assistant/conversations/{conversation}/messages",
        json={"text": text},
        timeout=120,
    ) as resp:
        resp.raise_for_status()
        event = None
        for line in resp.iter_lines():
            if line.startswith("event: "):
                event = line[7:]
            elif line.startswith("data: ") and event:
                events.append((event, json.loads(line[6:])))
    return {
        "text": "".join(d["delta"] for e, d in events if e == "text"),
        "cards": [d for e, d in events if e == "card"],
        "tools": [d["tool"] for e, d in events if e == "status"],
        "citations": next((d["valid"] for e, d in events if e == "citations"), []),
        "done": next((d for e, d in events if e == "done"), {}),
    }


def score(expect: dict[str, Any], got: dict[str, Any], client: httpx.Client) -> dict[str, bool]:
    checks: dict[str, bool] = {}
    products = [c for c in got["cards"] if c["kind"] == "product"]
    search = expect.get("search") or {}
    tools = got["tools"]
    if expect.get("action") == "search":
        checks["uses_catalog"] = "search_products" in tools
    elif expect.get("action") == "product_details":
        checks["uses_details"] = "get_product_details" in tools
    if expect.get("expect_empty"):
        checks["empty"] = not products
        if expect.get("must_not_claim_match"):
            checks["acknowledges_no_match"] = bool(
                re.search(
                    r"\b(?:no exact match|no matching|none (?:of the .+ )?matched|"
                    r"couldn['’]?t find|didn['’]?t find|cannot find|can['’]?t find)\b",
                    got["text"],
                    re.IGNORECASE,
                )
            )
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
    if constraints and not expect.get("expect_empty"):

        def detail_ok(card: dict[str, Any]) -> bool:
            detail = client.get(f"/api/v1/products/{card['id']}")
            detail.raise_for_status()
            product = detail.json()
            specs = product.get("specs") or {}
            allergens = {a.lower() for a in product.get("allergens") or []}
            return (
                all(
                    word.lower() in product["title"].lower()
                    for word in constraints.get("title_contains", [])
                )
                and all(
                    specs.get(key) == value for key, value in constraints.get("specs", {}).items()
                )
                and not (allergens & {a.lower() for a in constraints.get("allergens_none", [])})
                and (
                    "variant_code" not in constraints
                    or any(
                        variant["sku"].endswith("-" + constraints["variant_code"])
                        for variant in product.get("variants", [])
                    )
                )
            )

        checks["result_constraints"] = bool(products) and all(detail_ok(c) for c in products)
    text = got["text"].lower()
    if expect.get("mentions"):
        checks["mentions"] = all(m.lower() in text for m in expect["mentions"])
    if expect.get("mentions_any"):
        checks["mentions"] = any(m.lower() in text for m in expect["mentions_any"])
    if expect.get("must_not_mention"):
        titles = " ".join(c.get("title", "") for c in products).lower()
        checks["must_not_mention"] = not any(
            m.lower() in text or m.lower() in titles for m in expect["must_not_mention"]
        )
    if expect.get("cite"):
        cited = {c["cite"].split("#")[0] for c in got["citations"]} | {
            c["cite"] for c in got["citations"]
        }
        checks["cites"] = all(c in cited or c.split("#")[0] in cited for c in expect["cite"])
    return checks


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--web", default="http://localhost:3000")
    parser.add_argument("--agent", choices=("steph", "xana"), default="steph")
    parser.add_argument("--only")
    parser.add_argument("--record-baseline", action="store_true")
    args = parser.parse_args()
    scripts = [
        json.loads(line)
        for line in SCRIPTS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if args.only:
        wanted = set(args.only.split(","))
        scripts = [s for s in scripts if s["id"] in wanted]
    elif args.agent == "xana":
        # Xena answers product questions but deliberately cannot add to the cart.
        scripts = [
            script
            for script in scripts
            if all(turn["expect"].get("action") != "add_to_cart" for turn in script["turns"])
        ]
    clients: dict[str, httpx.Client] = {}
    results = []
    model = "?"
    started = time.perf_counter()
    for script in scripts:
        user = script["user"]
        if user not in clients:
            c = httpx.Client(base_url=args.web, timeout=60)
            c.post(
                "/api/v1/auth/sign-in", json={"email": user, "password": PASSWORDS[user]}
            ).raise_for_status()
            clients[user] = c
        client = clients[user]
        conv = client.post("/api/assistant/conversations", json={"agent": args.agent}).json()["id"]
        turn_results = []
        for t in script["turns"]:
            got = turn(client, conv, t["user"])
            model = got["done"].get("model", model)
            checks = score(t["expect"], got, client)
            turn_results.append(
                {"user": t["user"], "checks": checks, "passed": all(checks.values())}
            )
        passed = all(r["passed"] for r in turn_results)
        results.append({"id": script["id"], "passed": passed, "turns": turn_results})
        mark = "PASS" if passed else "FAIL"
        failed = [k for r in turn_results for k, v in r["checks"].items() if not v]
        print(
            f"{mark} {script['id']}  {script['turns'][0]['user'][:60]}"
            + (f"  ({', '.join(failed)})" if failed else "")
        )
    total = len(results)
    ok = sum(r["passed"] for r in results)
    by_check: dict[str, list[bool]] = {}
    for r in results:
        for t in r["turns"]:
            for k, v in t["checks"].items():
                by_check.setdefault(k, []).append(v)
    print(
        f"\nmodel: {model}  scripts passed: {ok}/{total} ({ok / max(total, 1):.0%})  "
        f"time: {time.perf_counter() - started:.0f}s"
    )
    for k, vals in sorted(by_check.items()):
        print(f"  {k:<18} {sum(vals)}/{len(vals)}")
    if args.record_baseline:
        label = f"{args.agent}-" if args.agent != "steph" else ""
        out = ROOT / "evals" / "baselines" / f"assistant-{label}{model}.json"
        summary = {
            "agent": args.agent,
            "model": model,
            "passed": ok,
            "total": total,
            "checks": {k: [sum(v), len(v)] for k, v in by_check.items()},
            "failed": [r["id"] for r in results if not r["passed"]],
        }
        out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(f"baseline saved to {out.relative_to(ROOT)}")
    sys.exit(0 if ok == total else 1)


if __name__ == "__main__":
    main()
