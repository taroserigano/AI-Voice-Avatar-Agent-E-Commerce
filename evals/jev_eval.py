"""Jev routing eval: Jev (or its local simulator) against labeled customer turns.

Run from the repo root: ``uv run --directory services/assistant python ../../evals/jev_eval.py``
  --model jev|simulator   which decision model to score (default: jev when TYPESAFE_API_KEY is
                           set, else the simulator)
  --record-baseline       save this run as evals/baselines/jev-<model>.json

For each question (intent, return_reason, target_line, wants_person, policy_bypass):
  accuracy        answer matches the label (over the turns labeled for it)
  act rate        share of turns where confidence cleared the threshold, so code acted on it
  acted accuracy  accuracy on just those turns (this is the one that must stay high)
Plus p50/p95 latency and the input-token cost at Jev 1.13's price ($0.042 per million).

The labeled set is evals/assistant/jev_routing.jsonl. Compare the two runs to decide whether
Jev earns its place on each question, as the plan asks.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any

from assistant.config import get_settings
from assistant.jev.client import DecisionModel, JevClient
from assistant.jev.decisions import THRESHOLDS, decide
from assistant.jev.questions import turn_questions
from assistant.jev.simulator import JevSimulator

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "evals" / "assistant" / "jev_routing.jsonl"
PRICE_PER_TOKEN = 0.042 / 1_000_000
CHOICES = ("intent", "return_reason", "target_line")
NOULS = ("wants_person", "policy_bypass")


def load_cases() -> list[dict[str, Any]]:
    return [
        json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def run(model: DecisionModel) -> dict[str, Any]:
    stats: dict[str, dict[str, int]] = {
        q: {"n": 0, "right": 0, "acted": 0, "acted_right": 0} for q in (*CHOICES, *NOULS)
    }
    latencies: list[float] = []
    tokens = 0
    misses: list[str] = []
    for case in load_cases():
        lines = (case.get("context") or {}).get("candidate_lines", [])
        state = {
            "conversation": [{"role": "customer", "text": case["text"]}],
            "candidate_order_lines": lines,
        }
        result = model.ask(state, turn_questions(lines))
        signals = decide(result)
        latencies.append(result.latency_ms)
        tokens += result.usage.input_tokens
        expect = case["expect"]
        for q in CHOICES:
            if q not in expect:
                continue
            pick = getattr(signals, q)
            got = pick.value if pick else None
            s = stats[q]
            s["n"] += 1
            s["right"] += got == expect[q]
            if pick and (pick.act or expect[q] == "unclear"):
                s["acted"] += 1
                s["acted_right"] += got == expect[q]
            if got != expect[q]:
                misses.append(f"{case['id']} {q}: expected {expect[q]}, got {got}")
        for q in NOULS:
            if q not in expect:
                continue
            p = getattr(signals, q) or 0.0
            said_yes = p >= THRESHOLDS[q]
            s = stats[q]
            s["n"] += 1
            s["right"] += said_yes == expect[q]
            s["acted"] += 1
            s["acted_right"] += said_yes == expect[q]
            if said_yes != expect[q]:
                misses.append(f"{case['id']} {q}: expected {expect[q]}, got p={p:.2f}")
        if (
            "frustration_at_least" in expect
            and (signals.frustration or 0) < expect["frustration_at_least"]
        ):
            misses.append(f"{case['id']} frustration: expected >= {expect['frustration_at_least']}")
    per_question = {
        q: {
            "labeled": s["n"],
            "accuracy": round(s["right"] / s["n"], 3) if s["n"] else None,
            "act_rate": round(s["acted"] / s["n"], 3) if s["n"] else None,
            "acted_accuracy": round(s["acted_right"] / s["acted"], 3) if s["acted"] else None,
        }
        for q, s in stats.items()
    }
    ordered = sorted(latencies)
    return {
        "model": "jev-simulator" if model.simulated else getattr(model, "model", "jev"),
        "cases": len(latencies),
        "questions": per_question,
        "latency_ms": {
            "p50": round(statistics.median(ordered), 1) if ordered else 0,
            "p95": round(ordered[int(len(ordered) * 0.95) - 1], 1) if ordered else 0,
        },
        "input_tokens": tokens,
        "cost_usd": round(tokens * PRICE_PER_TOKEN, 6),
        "misses": misses,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", choices=["jev", "simulator"])
    parser.add_argument("--record-baseline", action="store_true")
    args = parser.parse_args()
    settings = get_settings()
    use_jev = args.model == "jev" or (args.model is None and settings.typesafe_api_key)
    if use_jev and not settings.typesafe_api_key:
        sys.exit("TYPESAFE_API_KEY isn't set; run with --model simulator")
    model: DecisionModel = (
        JevClient(settings.typesafe_api_key or "", model=settings.jev_model, timeout_s=10)
        if use_jev
        else JevSimulator()
    )
    report = run(model)
    print(f"model: {report['model']}  cases: {report['cases']}")
    print(f"{'question':<16}{'labeled':>8}{'accuracy':>10}{'act rate':>10}{'acted acc':>11}")
    for q, s in report["questions"].items():
        print(
            f"{q:<16}{s['labeled']:>8}{s['accuracy']!s:>10}{s['act_rate']!s:>10}{s['acted_accuracy']!s:>11}"
        )
    print(
        f"latency p50/p95: {report['latency_ms']['p50']}/{report['latency_ms']['p95']} ms  "
        f"input tokens: {report['input_tokens']}  cost: ${report['cost_usd']}"
    )
    for miss in report["misses"]:
        print("  miss:", miss)
    if args.record_baseline:
        name = "jev-simulator" if model.simulated else "jev"
        out = ROOT / "evals" / "baselines" / f"{name}.json"
        out.write_text(
            json.dumps({k: v for k, v in report.items() if k != "misses"}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"baseline saved to {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
