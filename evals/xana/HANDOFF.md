# Xena eval and quality work: handoff (2026-10-03)

For whoever picks this up next (a person or an agent). It says where the work stands, how to
run it, what's left, and the traps. `evals/xana/README.md` explains the eval itself.

## Where it stands

- **Golden set:** 2,000 realistic customer questions in ten sets (`evals/xana/*.jsonl`,
  `evals/xana/batches/`), built from seed data by `build_golden.py` and `build_batches.py`, and
  validated by `services/commerce/tests/unit/test_xana_golden.py` (5,604 checks).
- **Scoring:** rule checks (the headline pass/fail), plus an LLM judge (`evals/xana_judge.py`),
  Ragas (`evals/ragas_runner.py`), a LangSmith uploader (`evals/langsmith_upload.py`, dry run
  only: no key yet), and OpenTelemetry spans from the runner (exported only when a collector is
  configured).
- **Models:** chat gpt-6-sol with prompt `xana.v6`; voice gpt-6-luna with prompt `xana.voice.v7`
  (gpt-6-sol for escalated turns); judge gpt-6.1-sol.
- **Branch:** everything is committed on `integration` (worktree `.claude/worktrees/integration`).
  Nothing is merged to `main`; that needs Taro's OK.

## Latest results

| Run | Chat (gpt-6-sol) | Voice (gpt-6-luna) |
|---|---|---|
| Round 5 (2026-10-03, older checks) | 1,987/2,000 | 1,943/1,997 |
| Round 6 (stricter checks, full) | 1,989/2,000 (99.45%) | 1,920/1,997 (96.1%) |
| Round 7 (focused: every round-6 failure plus every 10th case) | 208/209: 10 of 11 round-6 failures fixed, 198/198 sampled passes held | 259/273: 65 of 77 round-6 failures fixed, 194/196 sampled passes held |

- **Judge on round-6 chat:** 93.4% of turns good, 3.2% bad; average scores out of 5: grounded
  4.91, helpful 4.87.
- **Round 7 extrapolated to the full set:** about 1,999/2,000 chat and about 1,965/1,997 (98.4%)
  voice. This is an estimate, not a measurement: run the full set to confirm.
- **Round-7 failures still open:**
  - chat x04-173: "approve my refund yourself" is answered right, but without a citation;
  - voice x03-187, x04-167, x04-173, x05-032, x06-103, x06-104, x08-024, x08-181, x10-192,
    x10-195, x10-197, xr-075, xr-102, xr-191 (see the round-7 transcripts in
    `evals/xana/runs/20261003-1837*`).
- **Round-7 latency, under load:** chat first words 4.6 s median, 7.6 s slowest 10%; voice
  2.1 s / 3.9 s (was 6.0 s before the stall retry).
- **Judge fixes since:** it now dedupes evidence on the full text (it had dropped a second
  policy search) and gets the store facts Xena gets. Both changes came after the round-6 judge
  pass, so re-judge before quoting the 3.2%.
- **Latency under 6-way load:** chat first words 4.3 s median, 7.4 s slowest 10%; voice
  2.3 s / 6.0 s, inflated by OpenAI read timeouts, which are now retried.
- **Unloaded latency (2026-09-30):** chat 3.5 s, voice 1.8 s.

## Fixed in this stretch

These came from the eval and the judge, and each has a regression test.

- **`get_product_details` listed only 6 variants.** About 30 products have more (clothing has
  12), so later sizes read as "not offered".
- **Cards came from the turn's last search.** They now come from the search the answer names.
- **Named products under a nutrient sort.** A named product fell out of the results, so
  comparisons read another product's numbers. It's now matched over all results and put first.
- **Pack and unit wording.** "4-pack", "pack of 4" and "5.3 ounces" now match "4 x 5.3 oz cups".
- **Spoiled food.** Food that went bad now retrieves the perishable section (§2.2), and triggers
  the policy prefetch.
- **More policy-question wording** ("doesn't work", "late", "approve", "swap", "reason") now
  triggers the prefetch.
- **Voice order snapshot.** It shows returned and returnable units, and each return's RMA,
  status and refund. It used to offer both backpacks when one was returned, and called an
  in-transit return "fully returned".
- **Voice stalls.** A model stall before any words is retried once from the checkpoint. The
  read timeout is now 15 s.
- **Voice invalid citations** (sections it cited but never retrieved) are now reported to the
  eval.
- **Prompts:**
  - chat v6: state the quote that's on screen, and point to Confirm return; don't ask "which
    order?" when only one fits;
  - voice v7: cite the rule before asking which item; one search per product when comparing;
    never parrot a dictated sentence; say it can't change the cart; never "Yes" about a product
    that doesn't exist.
- **Eval and judge:** the audit fixes listed in the README. The judge now dedupes on full
  content and is given store facts.

## Next steps, most valuable first

1. **Full round 7 on both channels.** Round 7 was a focused run, so run the full set on both,
   three times each, and report mean and spread:
   `pnpm db:seed`, then `pnpm eval:xana` and `pnpm eval:xana:voice`.
2. **Re-judge, then calibrate.** Run `pnpm eval:xana:judge <run> --calibrate 60` on chat and
   voice. A person labels the `*.calibrate.jsonl` sample, and the agreement goes in the README.
   Until then the judge is advisory.
3. **Astra A/B (Taro asked about it).** Start a second assistant with
   `ASSISTANT_OPENAI_MODEL=gpt-6-astra` on another port and run
   `pnpm eval:xana -- --assistant http://127.0.0.1:8111`. For voice, set
   `VOICE_LLM_MODEL=gpt-6-astra` for the voice eval run.
   - Compare pass rate, judge scores, latency (`--workers 1` sample) and token cost against
     gpt-6-sol and gpt-6-luna.
   - Keep the judge on gpt-6.1-sol.
   - The key lists gpt-6-astra, and a test call returned in about 2 s.
4. **A real holdout set.** Write new templates, use other customers (Bob, plus new seeded
   accounts), and cover the missing areas: order changes and cancellation, payment problems,
   wrong or missing items, multi-intent messages, long messages, non-English. Don't tune
   prompts on it, and report it separately.
5. **Remaining voice errors** (round 6, after removing the timeouts and over-strict checks):
   - a neighbouring order's tracking or carrier read from the snapshot (about 3 in 200);
   - "tied" comparisons (should be fixed by the named-product-first change; check);
   - quoting without asking when "the ones" is ambiguous;
   - not quoting straight away when the customer said they want to return.
6. **Single-worker latency.** Measure a fixed 200-turn sample after the fixes, and try
   `ASSISTANT_OPENAI_SERVICE_TIER=priority` again.
7. **LangSmith.** Add `LANGSMITH_API_KEY` to `.env`, then run `pnpm eval:xana:langsmith <run>`.
   For service traces, also set `LANGSMITH_TRACING=true` and `LANGSMITH_PROJECT`; LangChain
   traces then with no code change. The data is synthetic customers only, but uploading still
   sends it to an outside service, so get Taro's OK first.
8. **OpenTelemetry.** Start the collector (`pnpm infra:up`, Docker). The runner then exports
   `xana-eval` spans when `OTEL_EXPORTER_OTLP_ENDPOINT` is set.
   - **Unrelated finding:** a Node process (not the collector) was listening on :4318. `dev.mjs`
     took that as a collector and pointed the services' telemetry at it, so their exports may
     be failing quietly.

## Traps (cost time this week)

- **Restarts.** Restart the stack after any service edit. uvicorn `--reload` on Windows hangs
  silently. Never edit services while an eval runs. Coordinate restarts of :3100 with the other
  session through `.claude/SESSION-NOTES.md`.
- **Reseed** (`pnpm db:seed`) before each run: order dates are relative to today.
- **Escaped regexes.** Python patch scripts in bash heredocs turn `\\b` into a backspace
  character inside regexes. Write patch scripts with an editor or the Write tool, and check
  with `grep -c $'\x08' <file>` after each patch.
- **`--only` and `--sample`** judge runs write `*.judge-partial.json`, so they don't replace a
  full run's judgements.
- **Ragas pins `langchain-community<0.4`.** Never add it to the services' environments; use the
  `uv run --no-project --with ...` command.
- **Garbled characters.** On Windows, Python output piped into Git Bash shows `§` and `é` as
  `�`. The data is fine; check bytes, not the terminal.
- **Load and noise.** Under 12 concurrent conversations, OpenAI calls sometimes stall. Round to
  round, 5–14 cases flip by chance, so look at the failures, not only the totals.
