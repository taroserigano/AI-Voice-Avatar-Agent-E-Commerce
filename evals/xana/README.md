# Xana golden sets

Two sets of 200 questions each, scored against the live assistant:

| File | What it covers |
|---|---|
| `products.jsonl` | Filtered searches (type, tags, exclusions, price), spec and size searches, honest "no match", facts about one named product (nutrition, specs, variant price, stock, options, ingredients), allergy questions, label meanings, "which has the most" and comparisons, multi-turn refinement. |
| `returns.jsonl` | Return quotes with the exact refund in cents, ineligible returns (window, perishables, final sale, not delivered, canceled, already returned), items not on the account, clarifying questions, return and shipping policy with citations, return rules for kinds of items, refund status, safety (another customer's order, prompt injection, typed "yes", card numbers, exceptions), stores and drop-offs. |

The questions are written by hand in `build_golden.py`. Every expected fact is read from the
seed data (catalog, orders, stores, policy sections), so a golden answer can't be a typo.
`services/commerce/tests/unit/test_xana_golden.py` checks the written files against the seed
data on every test run. Rebuild after changing the seed data or the questions:

```
pnpm eval:xana:build
```

## Running

Reseed first (`pnpm db:seed`) so order dates are relative to today, start the stack
(`pnpm dev`), then:

```
pnpm eval:xana                     # chat (Xana on /support), both sets
pnpm eval:xana:voice               # the voice brain, typed turns, no speech synthesized
pnpm eval:xana -- --set returns --only xr-001,xr-010 --workers 8
pnpm eval:xana -- --record-baseline   # evals/baselines/xana-<channel>-<set>-<model>.json
pnpm eval:xana -- --assistant http://127.0.0.1:8111   # an assistant started with other settings
```

Every turn records `first_text_ms` (when the first words arrive) and `turn_ms`. Time with
`--workers 1`: parallel conversations slow each other down.

Each run writes every case's transcript (answer, tools, cards, quote, citations, and for voice
the tool arguments) to `evals/xana/runs/`, which is gitignored. Use it to review failures.

## How a case is scored

From what the customer sees, not from the model's words alone. A quote must be the server's own
quote for exactly the expected units and refund. Product cards must match the filters and the
listing facts, read back from the product API. Facts are regular expressions that accept
natural phrasings ("one-year" for "1-year", "1,000" for "1000"). A citation must be a section
retrieved in the same turn. A case passes only if every check on every turn passes.

When a check fails on a correct answer, fix the check in `build_golden.py` or
`evals/xana_eval.py` and say why. Don't loosen it to hide a wrong answer.

## Results (2026-09-30)

| Channel | Model | Products | Returns |
|---|---|---|---|
| Chat | gpt-6-sol | 200/200 | 199–200/200 |
| Voice | gpt-6-luna, gpt-6-sol on escalated turns | 195–199/200 | 187–190/198 (2 typed-"yes" cases are chat-only) |

Ranges are over the last runs; the models don't answer the same way every time. The
baselines in `evals/baselines/` are the latest run. The first runs on the new sets scored
chat 188/200 and 174/200, and voice 161/200 and 177/200.

Most voice misses left are short policy answers: a citation left off, or a detail missing. An
upstream model error sometimes fails a case (`no_error`).

Escalating every return, refund, or policy turn to gpt-6-sol was measured and left out. It
scored the same as Luna alone, at the same speed (see
`services/voice/src/ai_commerce_voice/escalation.py`). Only disputes, "that's wrong", repeated
questions, and repeated tool failures escalate.

## Latency (2026-09-30)

58 cases (every 7th of each set), one at a time. Voice is typed turns, so speech-to-text and
speech aren't included; voice plays a filler after 0.9 s when no answer is ready.

| Setup | First words, median | First words, slowest 10% | Whole turn, median |
|---|---|---|---|
| Voice, gpt-6-luna (low effort, priority tier) | 1.8 s | 3.0 s | 2.3 s |
| Chat before: the web app's proxy held the stream back | 4.8 s | 8.3 s | 4.8 s |
| Chat, gpt-6-sol medium effort, policy prefetch | 3.5 s | 7.6 s | 4.4 s |
| Same, priority tier (`ASSISTANT_OPENAI_SERVICE_TIER=priority`) | 3.3 s | 5.7 s | 4.0 s |
| Same, low effort (`ASSISTANT_OPENAI_REASONING=low`) | 3.7 s | 5.7 s | 4.5 s |

Low effort wasn't faster at the median and scored 197/200 on returns, so chat stays at medium.
The priority tier cuts the slow tail and costs more per token; it's off by default.
