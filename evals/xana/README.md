# Xena golden sets

2,000 questions in ten sets of 200, scored against the live assistant (chat) and the voice brain:

| Set | What it covers |
|---|---|
| `products.jsonl` | Filtered searches (type, tags, exclusions, price), spec and size searches, honest "no match", facts about one named product (nutrition, specs, variant price, stock, options, ingredients), allergy questions, label meanings, "which has the most" and comparisons, multi-turn refinement. |
| `returns.jsonl` | Return quotes with the exact refund in cents, ineligible returns (window, perishables, final sale, not delivered, canceled, already returned), items not on the account, clarifying questions, return and shipping policy with citations, return rules for kinds of items, refund status, safety (another customer's order, prompt injection, typed "yes", card numbers, exceptions), stores and drop-offs. |
| `batches/b03-catalog` | Product facts, specs, variant prices, stock by size, ingredients, allergies, worded the way customers ask. |
| `batches/b04-returns-wide` | Return rules for 60 kinds of items, quotes, refusals, not found, which-item questions, policy, refund status, stores. |
| `batches/b05-orders` | Where's my order, carrier, tracking, delivery and order dates, totals, order numbers, account history. |
| `batches/b06-noisy` | Questions from the other sets with typos, all caps, chatty openers, and speech-to-text style (lowercase, fillers). |
| `batches/b07-multiturn` | Follow-ups, refinements, corrections, topic switches, return flows over several turns. |
| `batches/b08-safety` | Prompt injection, other customers' data, card numbers, off-topic, health advice, typed confirmations, made-up amounts, things that don't exist. |
| `batches/b09-compare` | "Which has the most", two-product comparisons, price comparisons, counts, budgets. |
| `batches/b10-holdout` | A mix built from other seeds plus new cases. Not a true holdout: it ran every round (see "How much to trust the scores"). |

Two more files cover what a customer-support representative is asked beyond those 2,000 (added
2026-10-08, when Taro asked that Xena handle every product, policy, and order-history question a
support rep would):

| File | What it covers |
|---|---|
| `support/support.jsonl` (204) | The development half: how the site works (account, checkout, payment, promo codes, gift cards, cart, receipts, order changes, reviews, stores, contacting us; the help center), shipping, every return-policy section, catalog-wide questions (brands, counts, cheapest and priciest, price ranges, things we don't sell), order amounts (subtotal, discount, tax, shipping), a third customer (Dana) with different orders, multi-part, long, and other-language messages, escalation. Run it, read the failures, fix. |
| `locked/holdout.jsonl` (223) | The locked half, same kinds of questions. Never read its failures or tune on it: run it once at the end of a round (`--file`) and report it separately. |

Each question goes to one file or the other by a fixed hash of its text, so adding questions
never moves an existing one across.

`build_golden.py` (the two core sets, hand-written), `build_batches.py` (b03-b10, from the
seed data with fixed seeds), and `build_support.py` (the support and locked files) write the files. Every expected fact is read from the seed data
(catalog, orders, returns, stores, policy sections), so a golden answer can't be a typo.
`services/commerce/tests/unit/test_xana_golden.py` checks the files against the seed data on
every test run (5,604 checks), and fails when an expectation holds a null or when a reply that
answers nothing ("Sure! I can help with orders and returns.") would pass a case's only content
check. Rebuild after changing the seed data or the questions:

```
pnpm eval:xana:build
uv run --directory services/assistant python ../../evals/xana/build_batches.py
uv run --directory services/assistant python ../../evals/xana/build_support.py
```

## Running

Reseed first (`pnpm db:seed`) so order dates are relative to today, start the stack
(`pnpm dev`), then:

```
pnpm eval:xana                     # chat (Xena on /support), all 2,000
pnpm eval:xana:voice               # the voice brain, typed turns, no speech synthesized
pnpm eval:xana -- --set b05-orders,b07-multiturn --workers 6
pnpm eval:xana -- --only xr-001,xr-010
pnpm eval:xana -- --set support                       # the customer-support development half
pnpm eval:xana -- --file evals/xana/locked/holdout.jsonl   # the locked half: once a round
pnpm eval:xana -- --assistant http://127.0.0.1:8111   # an assistant started with other settings
```

`all` is still the 2,000 golden questions, so rounds stay comparable; the support files run only
when named.

Each run writes every case's transcript to `evals/xana/runs/` (gitignored): the answer, tools,
cards, quote, citations, timings, a W3C trace id, and what each turn's tools returned
(`contexts`, read from the conversation's checkpoint; voice also has its orders snapshot). With
`OTEL_EXPORTER_OTLP_ENDPOINT` set, each case and turn is also exported as an OpenTelemetry span
(`xana-eval`), and chat requests carry the trace header so the services' spans join it.

After a run, on its transcript file:

```
pnpm eval:xana:judge evals/xana/runs/<run>.json              # LLM judge, every turn
pnpm eval:xana:judge evals/xana/runs/<run>.json --calibrate 60   # also a sample for a person to label
pnpm eval:xana:ragas evals/xana/runs/<run>.json              # Ragas, policy turns
pnpm eval:xana:langsmith evals/xana/runs/<run>.json --dry-run    # LangSmith experiment (needs LANGSMITH_API_KEY)
```

## How a case is scored

### Rule checks (pass/fail; the headline score)

From what the customer sees, not from the model's words alone. A quote must be the server's own
quote for exactly the expected units, refund, and shipping refund. Product cards must match the
filters and the listing facts, read back from the product API. Order facts (dates, carrier,
tracking, total) are compared with the live order. Facts are regular expressions that accept
natural phrasings ("one-year" for "1-year", codes read character by character). Every turn is
checked for leaked tool names or ids and for citations of sections the conversation never
retrieved. Claim detectors ("your refund has been issued", "it's safe for your allergy") are
tested on labeled sentences in `evals/test_xana_detectors.py`. A crash is reported as `infra`
(the stack or provider; retried once) or `harness` (a bug in the eval), apart from wrong answers.

When a check fails on a correct answer, fix the check and say why. Don't loosen it to hide a
wrong answer. Safety checks stay rule-based (docs/handoff/ACCEPTANCE_AND_EVALS.md).

### LLM judge (`evals/xana_judge.py`; quality, a soft signal)

gpt-6.1-sol (a newer model than the chat assistant's gpt-6-sol, so it isn't grading its own
answers) scores each turn 1-5 on grounded, helpful, clear, and tone, with a good/minor/bad verdict
and the unsupported claims it found. It sees what Xena had: the tool results for the
conversation so far, and what Xena's instructions give her (the customer's name, the catalog
counts and tag meanings, and the store's operating rules: returns open after delivery, refunds
to the original payment method, ask which item when two could match, a person can be brought
in). Without those it marked correct answers as invented. It prints where it disagrees with the
rule checks: rule-passed but judged bad (a check may be missing) and rule-failed but judged good
(a check may be too strict). `--calibrate N` writes a stratified sample with an empty
`human_verdict` to label; record the agreement here before any judge score becomes a gate.

### Ragas (`evals/ragas_runner.py`; policy answers)

Ragas 0.4.3 `Faithfulness` and `AnswerRelevancy`, judged by gpt-6.1-sol, embeddings
text-embedding-3-small. Ragas pins an older langchain-community than the services, so it runs
in a throwaway environment (`uv run --no-project --with ragas==0.4.3 ...`; no lockfile change).
Two adaptations, both measured: the customer's own words count as evidence, and statements
about the assistant's own acts ("the assistant asks which item") are dropped before scoring. Out
of the box a fully grounded clarifying answer scored 0.33; with them, 1.0 on repeated runs.
`AnswerRelevancy` sits near 0.5-0.6 for conversational answers and is only useful relative to an
earlier run.

## Results

### 2026-10-08/09 (rounds 8 and 9: support-rep coverage, locked holdout)

| Set | Chat, gpt-6-sol | Voice, gpt-6-luna |
|---|---|---|
| 2,000 golden, round 8 (3 runs) | mean 99.8% (1,995-1,996) | mean 98.8% (1,963-1,980) |
| 2,000 golden, round 9 | 1,996 (99.8%) | 1,985 (99.4%) |
| Support dev (204), round 9 | 203 (99.5%) | 201 (98.5%) |
| Locked holdout (223), rounds 8 and 9 | 218, 217 (97.6%) | 214, 213 (95.7%) |

LLM judge on round 8 (run 3, after the judge fixes): chat 98.9% good, 0.3% bad, 99.4% agreement
with the rule checks; voice 94.4% good, 3.1% bad, 96.8% agreement. gpt-6-astra on chat (round
9 code): 1,986/2,000, holdout 218/223, slower than gpt-6-sol. Details and the list of fixes are in
`HANDOFF.md`.

### 2026-10-03 (round 6: stricter checks, full 2,000)

| Channel | Model | Passed | Notes |
|---|---|---|---|
| Chat | gpt-6-sol | 1,989/2,000 (99.45%) | b05, b06, b09, b10 at 200/200 |
| Voice | gpt-6-luna | 1,920/1,997 (96.1%) | ~25 failures were OpenAI read timeouts under load (now retried); 6 were checks requiring a tool voice no longer needs |

LLM judge on the chat run (before its evidence fixes): 2,177 good, 79 minor, 75 bad of 2,331
turns; grounded 4.91, helpful 4.87, clear 4.96, tone 4.95; agreement with the rule checks 96.6%.
Of the 72 turns it judged bad that the rules passed, about 60 were the judge missing evidence
(catalog counts, the customer's name, store rules, a deduplication bug); the rest led to fixes
(a quote announced as "I'll get a quote" while on screen, asking "which order" with only one).

Fixes after round 6, checked on a focused run (all round-6 failures plus every 10th case; see
the handoff file for the numbers): every product variant listed (only 6 were, so diapers in
size 6 read as "not offered"), cards from the search the answer is about, a named product first
under a nutrient sort, "4-pack" matching "4 x 5.3 oz cups", the perishable policy retrieved for
food that went bad, the voice orders snapshot with returned units and each return's status and
RMA, one retry when the voice model stalls before speaking, prompts xana.v6 and xana.voice.v7.

Earlier: 2026-09-30, chat 200/200 and 199-200/200 on the two core sets, voice 195-199 and
187-190.

## How much to trust the scores

An audit on 2026-10-03 found, and these were fixed: 128 turns whose only content check a reply
answering nothing could pass (catch-all alternatives like `|products|orders|` or `|only|`); claim
detectors that missed most phrasings; null expectations that crashed three cases; checks that
were never scored (shipping refunds, handoffs). Still true:

- Prompts were tuned on the 2,000 and the support dev set, so those are dev-set scores. The
  locked holdout (`locked/holdout.jsonl`: new templates, three customers, order changes,
  payment, multi-intent, long and non-English messages) is the honest number, and it runs 2-4
  points lower.
- 1,930 of the 2,000 cases are one customer (Alice), with 14 orders.
- One run's 95% interval at ~99% is about ±0.4 points (±8 cases); between runs 5-14 cases flip.
  Differences smaller than about 10-15 cases between rounds are noise; run 3 times to compare.

## Latency

The full runs above time every turn under load (6 conversations at once per channel): chat
first words 4.0-4.3 s median, 6.6-7.4 s slowest 10%; voice 1.9-2.3 s and 3.2-6.0 s. For a fair
measurement, time a fixed sample with `--workers 1`, as below.

### 2026-10-09, one at a time

200 cases (every 10th). Voice gpt-6-luna: first words 2.0 s median, 3.1 s slowest 10%. Chat
gpt-6-sol: 3.9 s and 6.6 s. Chat gpt-6-astra: 5.7 s and 8.8 s.

### 2026-09-30, one at a time

58 cases (every 7th of each set). Voice is typed turns, so speech-to-text and speech aren't
included; voice plays a filler after 0.9 s when no answer is ready.

| Setup | First words, median | First words, slowest 10% | Whole turn, median |
|---|---|---|---|
| Voice, gpt-6-luna (low effort, priority tier) | 1.8 s | 3.0 s | 2.3 s |
| Chat before: the web app's proxy held the stream back | 4.8 s | 8.3 s | 4.8 s |
| Chat, gpt-6-sol medium effort, policy prefetch | 3.5 s | 7.6 s | 4.4 s |
| Same, priority tier (`ASSISTANT_OPENAI_SERVICE_TIER=priority`) | 3.3 s | 5.7 s | 4.0 s |
| Same, low effort (`ASSISTANT_OPENAI_REASONING=low`) | 3.7 s | 5.7 s | 4.5 s |

Low effort wasn't faster at the median and scored 197/200 on returns, so chat stays at medium.
The priority tier cuts the slow tail and costs more per token; it's off by default.

Escalating every return, refund, or policy turn to gpt-6-sol was measured and left out. It
scored the same as Luna alone, at the same speed (see
`services/voice/src/ai_commerce_voice/escalation.py`). Only disputes, "that's wrong", repeated
questions, and repeated tool failures escalate.
