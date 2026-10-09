# Xena eval and quality work: handoff (2026-10-09)

For whoever picks this up next (a person or an agent). It says where the work stands, how to
run it, what's left, and the traps. `evals/xana/README.md` explains the eval itself.

## Where it stands

- **What Xena covers:** product questions, return and refund policy, order history and what was
  in each order (amounts, discounts, tax, tracking), returns (quotes the customer confirms),
  and the customer-support questions a help desk gets: account, checkout and payment, promo
  codes, gift cards, receipts, shipping, stores, contact details, privacy
  (`content/policies/help-center.md`, `shipping-and-delivery.md`).
- **Eval sets:**
  - the 2,000 golden questions (`evals/xana/*.jsonl`, `evals/xana/batches/`), used for tuning;
  - the customer-support questions from `build_support.py`: 204 dev (`support/support.jsonl`)
    and 223 locked (`locked/holdout.jsonl`), split by a hash of the question. Three customers
    (Alice, Bob, and Dana, a new seeded shopper with 7 orders).
  - All checked by `services/commerce/tests/unit/test_xana_golden.py` (6,089 checks).
- **Models:** chat gpt-6-sol with prompt `xana.v8`; voice gpt-6-luna with `xana.voice.v9`;
  judge gpt-6.1-sol.
- **Branch:** committed on `integration` (worktree `.claude/worktrees/integration`) up to
  d42c2ef. Nothing is merged to `main`; that needs Taro's OK.

## Latest results

Rule checks (the headline). Rounds 8 and 9 are 2026-10-08/09.

| Run | Chat (gpt-6-sol) | Voice (gpt-6-luna) |
|---|---|---|
| Round 8, 3 runs (2,000) | 1,995 / 1,996 / 1,995: mean 99.8%, spread 1 | 1,963 / 1,980 / 1,974: mean 98.8% (run 3 had 6 OpenAI errors) |
| Round 9 (2,000) | 1,996 (99.8%) | 1,985 (99.4%), no OpenAI errors |
| Support dev, round 8 / 9 | 200 / 203 of 204 | 201 / 201 of 204 |
| **Locked holdout**, round 8 / 9 | **218 / 217 of 223 (97.6%)** | **214 / 213 of 223 (95.7%)** |

- **The locked holdout is the honest number.** It runs once per round and nobody has read its
  failures. It sits 2-4 points under the dev sets, which were tuned on.
- **Judge on round 8 run 3** (after the judge fixes below):

  | Channel | Good | Minor | Bad | Agrees with rule checks |
  |---|---|---|---|---|
  | Chat | 98.9% | 0.7% | 0.3% | 99.4% |
  | Voice | 94.4% | 2.5% | 3.1% | 96.8% |

  The voice "bad" turns that the rules passed led to most of round 9's prompt changes. A judge
  pass costs about 14M input tokens (chat) and 18M (voice).
- **Judge calibration:** 60 turns (40 chat, 20 voice, stratified by the judge's verdict) are on
  a labeling page: https://claude.ai/artifact/Ds7rB3BcpdvDxXV4iwHJwG (private to Taro). Labels
  are kept in the page's `labels` collection. Until a person labels them, the judge is advisory.
- **Astra A/B (chat, round 9 code):** gpt-6-astra scored 1,986/2,000 (99.3%), locked holdout
  218/223, support 202/204: no better than gpt-6-sol, and slower under the same load (first
  words 6.7 s median against 4.2 s). Recommendation: keep gpt-6-sol.
- **Latency, one conversation at a time** (the same 200 cases, every 10th, 2026-10-09; voice is
  typed turns, so speech-to-text isn't included):

  | Setup | Passed | First words, median | Slowest 10% | Whole turn, median |
  |---|---|---|---|---|
  | Voice, gpt-6-luna | 197/200 | 2.0 s | 3.1 s | 2.5 s |
  | Chat, gpt-6-sol | 198/200 | 3.9 s | 6.6 s | 4.7 s |
  | Chat, gpt-6-astra | 197/200 | 5.7 s | 8.8 s | 6.8 s |

## Fixed in rounds 8 and 9

Each has a regression test.

- **Support-rep coverage:** a help-center policy, shipping sections, order amounts (subtotal,
  discount, tax, total, each line's discount), whether every order was listed, a price floor,
  every brand of a kind with counts, multi-question messages answered in one reply.
- **Amounts worked out on the server:** the spending total (`total_spent_on_orders_not_canceled`)
  for chat and voice; both models added totals themselves and were off by $1-$5.
- **Dates carry the weekday** in the store's time zone; voice guessed weekdays wrong.
- **Voice tracking and carrier:** each item line in the voice orders snapshot ends with its own
  order's carrier and tracking number. Told to call a tool instead, voice said "I'll check" and
  stopped, and once named a product's brand as its carrier.
- **Policy prefetch:** refund questions bring the return window; disputes over a damage decision
  bring inspection outcomes and review; food someone doesn't want bring the perishable
  change-of-mind rule; another country brings "US only"; "banned for returns" brings fair use.
- **Prompts (chat v8, voice v9):** answer the second question beside a quote; ask which one when
  two different items match ("the milk"); an in-transit return's refund isn't issued yet; never
  suggest reordering (checkout is off); speak only about the products returned, not all
  matches; a closed store is closed; warranty after the window; chat never says a typed "yes"
  confirms a return.
- **Judge:** it knows checkout is off, that a spoken yes confirms on voice but a typed yes
  doesn't in chat, and reads superseded statuses from later messages.
- **Eval checks:** variant checks accept ranges ("XS through XXL", "15-, 30-, and 40-pound",
  "four 5.3 oz cups"). This touched 8 locked cases' patterns, not their questions.

## Tried and reverted

- A template citation wording in the voice prompt ("`[[cite:` then the section's cite value")
  made voice write `[[cite:]]` and `[[cite:shipping-policy]]`. Back to a concrete example plus
  where the value comes from.

## Next steps, most valuable first

1. **Label the calibration page,** then compute judge/person agreement from the `labels`
   collection (doc id `<case>-t<turn>--<user>`, fields verdict, note, judge_verdict) and put it
   in the README.
2. **Close the holdout gap without reading it.** Write more dev questions in the support
   categories (stores and stock, price extremes, payment problems, order amounts, upset
   customers, non-English), with new templates, then run the holdout once. It has now run 3
   times; after the next round, build a fresh locked half with new templates.
3. **Voice help-center citations.** Voice answers checkout, promo, and subscription questions
   correctly but often without a citation (h-013, h-022, s-011 in the dev set).
4. **Remaining dev failures** that recur: x04-173 (no citation on "approve my refund
   yourself"), x04-199 (Arlington drop-off), xr-075 (two backpacks, one already returned),
   x07-117 (quotes headphones without asking which pair).
5. **Ragas on the round-9 policy turns,** then review the 0.0s by hand (see README).
6. **LangSmith and OpenTelemetry:** unchanged from the last handoff; LangSmith needs
   `LANGSMITH_API_KEY` and Taro's OK, since uploads send data to an outside service.

## Traps

- **Restarts.** Any edit to a service reloads it, and on Windows the reload takes the whole
  :3100 stack down (or hangs silently). Never edit services while an eval runs; restart the
  stack after edits. Prompts are cached at start, so prompt edits also need a restart.
  Coordinate restarts of :3100 through `.claude/SESSION-NOTES.md`.
- **Overnight stops.** If the machine sleeps, Postgres, OpenSearch and Qdrant stop too: run
  `pnpm local:up` before restarting the stack.
- **Reseed** (`pnpm db:seed`) before each run: order dates are relative to today.
- **OpenAI errors come in bursts** ("voice turn failed", 6-12 in a run). Count them separately
  before comparing runs.
- **Escaped regexes.** Python patch scripts in bash heredocs turn `\\b` into a backspace
  character. Write patch scripts with the Write tool, and check with `grep -c $'\x08' <file>`.
- **The policy retrieval query drops filler and repeated words** ("change of mind" becomes
  "change mind"), so tests should look for words that survive.
- **`--only` and `--sample`** judge runs write `*.judge-partial.json`.
- **Ragas pins `langchain-community<0.4`.** Use the `uv run --no-project --with ...` command.
- **Garbled characters.** On Windows, Python output piped into Git Bash shows `§` and `é` as
  `�`. The data is fine.
- **Noise.** Round to round, 5-15 cases flip by chance; look at the failures, not only totals.
