# 3.3. Jev — implementation

Status: **done** for routing and signals (2026-09-26). The return tools start using
`return_reason` and `target_line`, and the voice step uses `voice_yes`, in item 6.

## Tasks

- [x] `assistant/jev/client.py` — httpx client for `POST /v1/systemone` (Bearer key, `jev-latest`), retries 429/529 once, 1.5 s timeout, OTel span (model, input tokens, latency)
- [x] `assistant/jev/types.py` — pydantic questions (noul/choice/score) and answers
- [x] `assistant/jev/questions.py` — one fan-out request per turn: `intent` (9 options), `return_reason` (10), `wants_person`, `frustration` (4 levels), `policy_bypass`, and `target_line` over the order lines the server already showed; `voice_yes` for item 6
- [x] `assistant/jev/decisions.py` — thresholds (intent 0.70, reason 0.60, line 0.80, person 0.80, bypass 0.70, voice yes 0.90) → `TurnSignals`; `prompt_hint()`; `voice_yes_passes()` fails closed
- [x] `assistant/jev/simulator.py` — keyword simulator, labeled `simulated`
- [x] `assistant/jev/signals.py` — decision model factory (Jev / simulator / off), turn state (last 6 turns + candidate order lines from earlier tool results), errors → `source: "error"`
- [x] Graph: `route` asks Jev once per turn and stores the signals; `agent` appends the confident ones to the system prompt as hints; the scripted model acts on them (declines rule-bypass attempts, hands off on a confident "talk to a person")
- [x] Settings: `JEV_ENABLED`, `TYPESAFE_API_KEY`, `TYPESAFE_BASE_URL`, `JEV_MODEL`, `JEV_TIMEOUT_S`; tests force the simulator
- [x] `signals` stream event; `debug` + `decision_model` in `/v1/assistant/status`; "Why this answer (development)" panel under each answer in dev
- [x] `evals/assistant/jev_routing.jsonl` (44 labeled turns incl. voice-like transcripts and order-line disambiguation), `evals/jev_eval.py` (`pnpm eval:jev`): accuracy, act rate, acted accuracy, latency, cost; simulator baseline in `evals/baselines/jev-simulator.json`
- [x] Tests: 17 unit (payload shape, retries, errors, thresholds, hints, voice-yes table, fail-closed, candidate lines, off/error paths, baseline) + 1 integration (bypass attempt declined, no tools called)
- [x] Docs: HANDOFF decision 19, `.env.example`

## Log

- No `TYPESAFE_API_KEY` yet: everything ran on the simulator. With a key, `pnpm eval:jev --model jev`
  scores the real model on the same set; record it with `--record-baseline` and compare.
- The simulator's rules were tuned on this set (intent 97%, reason 91%, line 100%), so its
  numbers are optimistic; add a held-out split before comparing seriously.
