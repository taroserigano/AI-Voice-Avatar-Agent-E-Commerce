"""Ragas scores for Xena golden-set runs: are policy and product answers faithful to what was
retrieved, and do they answer the question?

Ragas pins an older langchain-community than the services use, so it runs in its own throwaway
environment (no lockfile change), from the repo root:

  uv run --no-project --python 3.12 --with "ragas==0.4.3" --with "langchain-community<0.4" \\
      python evals/ragas_runner.py evals/xana/runs/<run>.json
  --scope policy|products|all   which turns (default policy: turns that searched the policies)
  --sample 3                    every 3rd matching turn       --workers 8
  --model gpt-6.1-sol           the Ragas judge model

Metrics (ragas.metrics.collections, the 0.4 API; docs/handoff/ACCEPTANCE_AND_EVALS.md section B):
  faithfulness      share of the answer's claims supported by the turn's retrieved evidence
  answer_relevancy  how well the answer addresses the question (questions regenerated from the
                    answer, compared by embedding with the real one; text-embedding-3-small)

The evidence is the tool results evals/xana_eval.py saved for the turn and the turns before it
(``contexts``); citation markers are taken out of the answer. A clarifying question has no
claims, so its faithfulness is undefined and it's left out of that average. The OpenAI key is
read from .env (OPEN_AI_API or OPENAI_API_KEY). Writes <run>.ragas.json beside the run.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTEXT_CHARS = 16000
EVIDENCE_CHARS = 60000
POLICY_TOOLS = {"search_policies"}
# Ragas statements about the assistant's own conversational acts, not facts.
SELF_ACTS = re.compile(
    r"^\s*(?:the |an? )?(?:(?:customer[- ]|virtual |support |ai )?(?:assistant|agent|representative|rep)|xena|ai|"
    r"speaker|responder|response|reply|answer|chatbot|bot|I)\b"
    r"(?! (?:can't|cannot|can not|is unable|isn't able|doesn't have access))",
    re.IGNORECASE,
)
PRODUCT_TOOLS = {"search_products", "get_product_details"}


def api_key() -> str:
    for env in (ROOT / ".env", ROOT.parents[2] / ".env"):
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                m = re.match(r"\s*(OPEN_AI_API|OPENAI_API_KEY)\s*=\s*(.+?)\s*$", line)
                if m:
                    return m.group(2).strip("'\"")
    key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPEN_AI_API")
    if not key:
        sys.exit("no OpenAI key in .env (OPEN_AI_API) or the environment")
    return key


def contexts_for(turns: list[dict[str, Any]], upto: int) -> list[str]:
    # What the customer said is evidence too ("it arrived broken"); without it Ragas counts an
    # answer that repeats the customer's words as unfaithful.
    said = " / ".join(t["user"] for t in turns[: upto + 1])
    out: list[str] = [
        f"[the customer said] {said}",
        "[about the assistant] The assistant may apologize, ask the customer questions, and offer to "
        "check things or help start a return; those are its own actions, not claims about the store.",
    ]
    total = sum(len(x) for x in out)
    for i in range(upto, -1, -1):
        for c in turns[i].get("contexts") or []:
            text = f"[{c['tool']}] {c['content'][:CONTEXT_CHARS]}"
            if text in out or total + len(text) > EVIDENCE_CHARS:
                continue
            out.append(text)
            total += len(text)
    return out


def wanted(t: dict[str, Any], scope: str) -> bool:
    tools = {c["tool"] for c in t.get("contexts") or []}
    if not t.get("answer", "").strip():
        return False
    if scope == "policy":
        return bool(tools & POLICY_TOOLS)
    if scope == "products":
        return bool(tools & PRODUCT_TOOLS)
    return bool(tools)


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("run", type=Path)
    parser.add_argument("--scope", choices=("policy", "products", "all"), default="policy")
    parser.add_argument("--sample", type=int, default=1)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--model", default="gpt-6.1-sol")
    args = parser.parse_args()

    from openai import AsyncOpenAI
    from ragas.embeddings import embedding_factory
    from ragas.llms import llm_factory
    from ragas.metrics.collections import AnswerRelevancy, Faithfulness

    client = AsyncOpenAI(api_key=api_key(), max_retries=4, timeout=180)
    # Ragas maps max_tokens for reasoning models by name ("gpt-6"), and "gpt-6.1-sol" doesn't
    # parse: send what these models take (max_completion_tokens, temperature 1, no top_p).
    create = client.chat.completions.create

    async def reasoning_create(*a: Any, **kw: Any) -> Any:
        if "max_tokens" in kw:
            kw["max_completion_tokens"] = kw.pop("max_tokens")
        kw.pop("top_p", None)
        kw["temperature"] = 1.0
        return await create(*a, **kw)

    client.chat.completions.create = reasoning_create  # type: ignore[method-assign]
    llm = llm_factory(args.model, client=client, max_tokens=8192)
    embeddings = embedding_factory("openai", model="text-embedding-3-small", client=client)
    class StoreFaithfulness(Faithfulness):  # type: ignore[misc]
        """Faithfulness over the answer's facts only. Ragas turns every sentence into a statement,
        so "The assistant asks which item" and "will help start the return" counted as
        unsupported claims and a fully grounded clarifying answer scored 0.33 (xr-117,
        2026-10-03). Statements about what the assistant itself does are dropped; the facts
        about products, orders, and policies are scored as Ragas does."""

        async def _create_statements(self, question: str, response: str) -> list[str]:
            statements = await super()._create_statements(question, response)
            return [s for s in statements if not SELF_ACTS.match(s)]

    faithfulness = StoreFaithfulness(llm=llm)
    relevancy = AnswerRelevancy(llm=llm, embeddings=embeddings)

    run = json.loads(args.run.read_text(encoding="utf-8"))
    items = [
        (c, i)
        for c in run["results"]
        for i, t in enumerate(c["turns"])
        if wanted(t, args.scope)
    ][:: args.sample]
    if not items:
        sys.exit("no turns with saved tool results in scope: run evals/xana_eval.py again first")
    gate = asyncio.Semaphore(args.workers)
    started = time.perf_counter()

    async def score(c: dict[str, Any], i: int) -> dict[str, Any]:
        t = c["turns"][i]
        answer = re.sub(r"\s*\[\[cite:[^\]]+\]\]", "", t["answer"]).strip()
        row: dict[str, Any] = {"id": c["id"], "set": c["set"], "category": c["category"], "turn": i,
                               "rule_passed": t["passed"], "user": t["user"]}  # fmt: skip
        async with gate:
            try:
                f = await faithfulness.ascore(
                    user_input=t["user"], response=answer, retrieved_contexts=contexts_for(c["turns"], i)
                )
                row["faithfulness"] = f.value
            except Exception as exc:  # noqa: BLE001 - e.g. an answer with no claims
                row["faithfulness_error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
            try:
                r = await relevancy.ascore(user_input=t["user"], response=answer)
                row["answer_relevancy"] = r.value
            except Exception as exc:  # noqa: BLE001
                row["answer_relevancy_error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
        return row

    rows = await asyncio.gather(*(score(c, i) for c, i in items))

    def avg(rs: list[dict[str, Any]], k: str) -> float | None:
        xs = [r[k] for r in rs if isinstance(r.get(k), (int, float)) and r[k] == r[k]]  # drop NaN
        return round(sum(xs) / len(xs), 3) if xs else None

    by_set: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_set[r["set"]].append(r)
    report: dict[str, Any] = {"run": args.run.name, "scope": args.scope, "model": args.model,
                              "turns": len(rows), "sets": {}}  # fmt: skip
    print(f"\nragas on {args.run.name} ({run['summary']['channel']}, {args.scope} turns, judge {args.model})")
    print(f"{'set':<18}{'turns':>6}{'faithfulness':>14}{'relevancy':>11}")
    for name, rs in sorted(by_set.items()) + [("ALL", rows)]:
        f, r = avg(rs, "faithfulness"), avg(rs, "answer_relevancy")
        report["sets"][name] = {"turns": len(rs), "faithfulness": f, "answer_relevancy": r}
        print(f"{name:<18}{len(rs):>6}{(f if f is not None else float('nan')):>14.3f}"
              f"{(r if r is not None else float('nan')):>11.3f}")  # fmt: skip
    low = sorted((r for r in rows if isinstance(r.get("faithfulness"), float) and r["faithfulness"] < 0.7),
                 key=lambda r: r["faithfulness"])  # fmt: skip
    report["low_faithfulness"] = [{k: r[k] for k in ("id", "turn", "faithfulness", "user")} for r in low]
    print(f"\nfaithfulness below 0.7 ({len(low)}):")
    for r in low[:20]:
        print(f"  {r['id']} t{r['turn'] + 1} {r['faithfulness']:.2f}  {r['user'][:80]}")
    errors = sum(1 for r in rows if "faithfulness_error" in r)
    print(f"\n{time.perf_counter() - started:.0f}s; {errors} turns without a faithfulness score (no claims or an error)")
    dest = args.run.with_suffix(".ragas.json")
    dest.write_text(json.dumps({**report, "rows": rows}, indent=1, ensure_ascii=False), encoding="utf-8",
                    newline="\n")  # fmt: skip
    print(f"scores: {dest.name}")


if __name__ == "__main__":
    asyncio.run(main())
