"""Upload a Xena golden-set run to LangSmith as an experiment on the golden dataset.

  uv run --directory services/assistant python ../../evals/langsmith_upload.py <run.json> [--dry-run]

Needs LANGSMITH_API_KEY (and optionally LANGSMITH_ENDPOINT for a self-hosted or EU instance).
Without a key, or with --dry-run, it only prints what it would send. Nothing is sent otherwise.

- Dataset ``xana-golden`` (created once; new cases are added by id): one example per golden case,
  its customer turns as inputs and its expectations as reference outputs.
- Experiment ``xana-<channel>-<run time>`` linked to that dataset: one run per case with the
  answers, tools, cards, and quote, tagged with the model and prompt version.
- Feedback on each run: ``rule_pass`` (all rule checks), each failed check, and, when the
  sibling files exist, the LLM judge's verdict and scores (<run>.judge.json) and Ragas
  faithfulness and answer relevancy (<run>.ragas.json).

The golden customers are synthetic (alice@ and bob@example.com), so nothing personal is sent.
Tool results (``contexts``) stay local: they're large, and the scores already reflect them.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals"))
from xana_eval import SETS  # noqa: E402

DATASET = "xana-golden"
NAMESPACE = uuid.UUID("6f1c2f0e-2a36-4f4e-9d1a-58b8c1f7e0a1")  # stable example ids per case id


def golden_cases() -> dict[str, dict[str, Any]]:
    cases = {}
    for name, path in SETS.items():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                c = json.loads(line)
                cases[c["id"]] = {**c, "set": name}
    return cases


def sibling(run: Path, suffix: str) -> dict[str, Any] | None:
    path = run.with_suffix(suffix)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("run", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not args.run.exists():  # a path from the repo root (pnpm runs this from services/assistant)
        args.run = ROOT / args.run

    run = json.loads(args.run.read_text(encoding="utf-8"))
    summary = run["summary"]
    golden = golden_cases()
    judge = {(r["id"], r["turn"]): r for r in (sibling(args.run, ".judge.json") or {}).get("turns_judged", [])}
    ragas = {(r["id"], r["turn"]): r for r in (sibling(args.run, ".ragas.json") or {}).get("rows", [])}

    examples = [
        {"id": str(uuid.uuid5(NAMESPACE, cid)),
         "inputs": {"customer": c["user"], "turns": [t["user"] for t in c["turns"]]},
         "outputs": {"expect": [t["expect"] for t in c["turns"]]},
         "metadata": {"case_id": cid, "set": c["set"], "category": c["category"]}}
        for cid, c in golden.items()
    ]  # fmt: skip
    experiment = f"xana-{summary['channel']}-{args.run.stem.split('-' + summary['channel'])[0]}"
    runs, feedback = [], []
    for r in run["results"]:
        run_id = str(uuid.uuid4())
        turns = r["turns"]
        runs.append({
            "id": run_id, "name": f"xena {summary['channel']}", "run_type": "chain",
            "inputs": {"turns": [t["user"] for t in turns]},
            "outputs": {"answers": [t["answer"] for t in turns], "tools": [t["tools"] for t in turns],
                        "products": [t["products"] for t in turns], "quotes": [t["quote"] for t in turns],
                        "citations": [t["citations"] for t in turns], "error": r.get("error")},
            "reference_example_id": str(uuid.uuid5(NAMESPACE, r["id"])),
            "extra": {"metadata": {"case_id": r["id"], "set": r["set"], "category": r["category"],
                                   "model": summary.get("model"), "channel": summary["channel"]}},
            "seconds": r.get("seconds") or 0,
        })  # fmt: skip
        feedback.append((run_id, "rule_pass", float(r["passed"]), None))
        for i, t in enumerate(turns):
            for check, ok in t["checks"].items():
                if not ok:
                    feedback.append((run_id, f"check:{check}", 0.0, f"turn {i + 1}"))
            j = judge.get((r["id"], i))
            if j and "verdict" in j:
                feedback.append((run_id, "judge_verdict", {"good": 1.0, "minor": 0.5, "bad": 0.0}[j["verdict"]],
                                 j["reason"]))  # fmt: skip
                for d in ("grounded", "helpful", "clear", "tone"):
                    feedback.append((run_id, f"judge_{d}", j[d] / 5, None))
            g = ragas.get((r["id"], i))
            for k in ("faithfulness", "answer_relevancy"):
                if g and isinstance(g.get(k), float) and g[k] == g[k]:
                    feedback.append((run_id, f"ragas_{k}", g[k], f"turn {i + 1}"))

    key = os.environ.get("LANGSMITH_API_KEY")
    print(f"dataset {DATASET}: {len(examples)} examples; experiment {experiment}: {len(runs)} runs, "
          f"{len(feedback)} feedback scores (judge: {bool(judge)}, ragas: {bool(ragas)})")  # fmt: skip
    if args.dry_run or not key:
        print("dry run: nothing sent" + ("" if key else " (no LANGSMITH_API_KEY)"))
        return

    from langsmith import Client

    client = Client()
    if client.has_dataset(dataset_name=DATASET):
        dataset = client.read_dataset(dataset_name=DATASET)
        have = {str(e.id) for e in client.list_examples(dataset_id=dataset.id)}
        new = [e for e in examples if e["id"] not in have]
    else:
        dataset = client.create_dataset(DATASET, description="Xena golden set (evals/xana), synthetic customers")
        new = examples
    for i in range(0, len(new), 200):
        client.create_examples(dataset_id=dataset.id, examples=new[i : i + 200])
    client.create_project(experiment, reference_dataset_id=dataset.id, upsert=True,
                          metadata={"model": summary.get("model"), "channel": summary["channel"],
                                    "date": summary.get("date")})  # fmt: skip
    end = datetime.now(UTC)
    for r in runs:
        seconds = r.pop("seconds")
        client.create_run(project_name=experiment, start_time=end - timedelta(seconds=seconds), end_time=end, **r)
    for run_id, k, score, comment in feedback:
        client.create_feedback(run_id, k, score=score, comment=comment)
    print(f"uploaded {len(new)} new examples, {len(runs)} runs, {len(feedback)} scores to {experiment}")


if __name__ == "__main__":
    main()
