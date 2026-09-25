"""Search quality eval (layer 3): score product search on labeled queries.

Run from the repo root with the stack up: ``pnpm eval:search``
  --record-baseline   save this run as evals/baselines/search.json
  --split dev|test|all  which queries to score (default all; tune only on dev)

Metrics per query (graded relevance: 2 = what the shopper wants, 1 = fair alternative):
  nDCG@10    ranking quality, rewarding the best items near the top
  Recall@10  share of relevant items that appear in the top 10
  MRR        1 / rank of the first grade-2 item
The gate: no metric may drop more than ``TOLERANCE`` below the recorded baseline.
It calls the same service code as GET /v1/products, so it measures what shoppers get,
including which backends (OpenSearch, Pinecone) were actually available.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select

from commerce.catalog.models import Product
from commerce.catalog.schemas import SortOrder
from commerce.catalog.service import ProductFilters, list_products
from commerce.db import get_sessionmaker

EVALS = Path(__file__).resolve().parent
QUERIES = EVALS / "search_queries.jsonl"
BASELINE = EVALS / "baselines" / "search.json"
K = 10
TOLERANCE = 0.02


def dcg(grades: list[int]) -> float:
    return sum((2**g - 1) / math.log2(i + 2) for i, g in enumerate(grades))


def score(ranked: list[str], relevant: dict[str, int]) -> dict[str, float]:
    top = ranked[:K]
    ideal = dcg(sorted(relevant.values(), reverse=True)[:K])
    ndcg = dcg([relevant.get(s, 0) for s in top]) / ideal if ideal else 0.0
    recall = sum(1 for s in top if s in relevant) / len(relevant) if relevant else 0.0
    best = [s for s, g in relevant.items() if g == max(relevant.values())]
    mrr = next((1 / (i + 1) for i, s in enumerate(top) if s in best), 0.0)
    return {"ndcg@10": ndcg, "recall@10": recall, "mrr": mrr}


def run(split: str) -> dict:  # type: ignore[type-arg]
    rows = [json.loads(line) for line in QUERIES.read_text(encoding="utf-8").splitlines() if line]
    if split != "all":
        rows = [r for r in rows if r["split"] == split]
    per_query = []
    legs: dict[str, int] = defaultdict(int)
    with get_sessionmaker()() as db:
        slug_by_id = {str(i): s for i, s in db.execute(select(Product.id, Product.slug))}
        for row in rows:
            page = list_products(
                db,
                query=row["query"],
                filters=ProductFilters(),
                sort=SortOrder.RELEVANCE,
                page=1,
                page_size=K,
            )
            ranked = [slug_by_id.get(str(item.id), "?") for item in page.items]
            if page.search:
                legs[f"keyword={page.search.keyword.value}"] += 1
                legs[f"semantic={page.search.semantic.value}"] += 1
            per_query.append(
                {
                    "id": row["id"],
                    "type": row["type"],
                    "query": row["query"],
                    "top": ranked[:5],
                    **score(ranked, row["relevant"]),
                }
            )

    def mean(items: list[dict], key: str) -> float:  # type: ignore[type-arg]
        return round(sum(q[key] for q in items) / len(items), 4) if items else 0.0

    metrics = ("ndcg@10", "recall@10", "mrr")
    by_type = {
        t: {m: mean([q for q in per_query if q["type"] == t], m) for m in metrics}
        for t in sorted({q["type"] for q in per_query})
    }
    return {
        "ran_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "split": split,
        "queries": len(per_query),
        "backends_seen": dict(legs),
        "overall": {m: mean(per_query, m) for m in metrics},
        "by_type": by_type,
        "worst": sorted(per_query, key=lambda q: q["ndcg@10"])[:8],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record-baseline", action="store_true")
    parser.add_argument("--split", choices=["dev", "test", "all"], default="all")
    args = parser.parse_args()

    report = run(args.split)
    print(json.dumps({k: v for k, v in report.items() if k != "worst"}, indent=2))
    print("\nLowest-scoring queries:")
    for q in report["worst"]:
        print(f"  {q['ndcg@10']:.2f}  [{q['type']}] {q['query']!r} -> {q['top']}")

    if args.record_baseline:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"\nRecorded baseline: {BASELINE.relative_to(EVALS.parent)}")
        return 0

    if not BASELINE.exists():
        print("\nNo baseline yet; run with --record-baseline.")
        return 0
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    if baseline.get("split") != report["split"]:
        print(f"\nBaseline split is {baseline.get('split')!r}; compare like with like.")
        return 0
    failures = [
        f"{m}: {report['overall'][m]:.4f} < baseline {baseline['overall'][m]:.4f} - {TOLERANCE}"
        for m in report["overall"]
        if report["overall"][m] < baseline["overall"][m] - TOLERANCE
    ]
    if baseline.get("backends_seen") != report["backends_seen"]:
        print(
            f"\nNote: backends differ from the baseline run ({baseline.get('backends_seen')} "
            f"vs {report['backends_seen']}); scores aren't directly comparable."
        )
    if failures:
        print("\nFAIL: search quality dropped below the baseline:\n  " + "\n  ".join(failures))
        return 1
    print("\nPASS: no metric dropped below the baseline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
