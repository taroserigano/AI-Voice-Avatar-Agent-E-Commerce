# 3.3. Jev in the assistant, especially returns and refunds — plan

## Goal

Use TypeSafe's **Jev** (System One model: typed questions in, calibrated probabilities out) for
the narrow decisions in the assistant, above all in the return and refund flow. Code stays in
control: Jev picks among fixed options, and its confidence decides whether code acts, asks, or
falls back to the LLM. Jev never decides eligibility, amounts, or confirmation on its own.

## API facts (docs.typesafe.ai, read 2026-09-26)

- `POST https://api.typesafe.ai/v1/systemone`, `Authorization: Bearer $TYPESAFE_API_KEY`.
- Body: `state` (string/object/array), `model` (`jev-latest` → `jev-1.13.0`), `questions`
  (map of `noul` | `choice` | `score`, each with `instructions` and `criteria`).
- Answers keyed by question ID; `choice` returns `choice`, `probabilities`, `confidence`;
  `noul` returns `noul` (P(yes)); `score` returns `score`, `probabilities`, `confidence`.
- Errors 401/422/429/529; retry 429/529 with backoff. Pin `jev-1.13.0` once thresholds are tuned.
- Many questions in one request cost one pass over the state ("speculative fan-out").

## Where Jev is used

One Jev request per user turn (fan-out), state = the last few turns plus a server-built context
(the customer's candidate order lines, never card data or addresses):

| Question | Type | Options | Used for | Gate |
|---|---|---|---|---|
| `intent` | choice | `product_search`, `product_question`, `order_status`, `start_return`, `refund_status`, `policy_question`, `store_info`, `talk_to_person`, `other` | Route to a tool set and prompt | act ≥ 0.70 confidence, else the LLM decides with all tools |
| `return_reason` | choice | `damaged`, `defective`, `wrong_item`, `not_as_described`, `spoiled_or_expired`, `missing_parts`, `no_longer_needed`, `better_price`, `arrived_late`, `other` | Reason code sent with a quote; perishable claims need damaged/spoiled | ≥ 0.60, else ask |
| `target_line` | choice | the candidate order-line IDs the server listed, plus `unclear` | "the other headphones" → which line | ≥ 0.80, else show cards and ask which |
| `wants_person` | noul | — | Offer a person / support case | ≥ 0.80 |
| `frustration` | score | calm / annoyed / upset / very upset | Tone, and offer a person when high | ≥ 2.5 → offer |
| `policy_bypass` | noul | — | "ignore your rules", "just refund me anyway", injected instructions | ≥ 0.70 → flagged turn, refuse politely |
| `voice_yes` | noul | — | Second vote on a spoken confirmation (item 6) | Confirm only if the deterministic rule **and** Jev ≥ 0.90 agree |

## Design

- `assistant/jev/` — `JevClient` (httpx, retries on 429/529, timeout 1.5 s, OTel span with model,
  tokens, latency), typed questions/answers (pydantic), `questions.py` (the question set above),
  `decisions.py` (thresholds → typed decisions: `Act(x)`, `Ask`, `Fallback`).
- `JevSimulator` — same interface, keyword rules, answers labeled `simulated=True`; used when
  `TYPESAFE_API_KEY` is missing. Unit tests and the scripted model use it.
- Feature flag `JEV_ENABLED` (default on; off → the LLM routes and nothing calls Jev).
  Any Jev error or timeout → `Fallback` (the turn continues without it).
- Graph: the `route` node calls Jev once, stores `TurnSignals` in state, restricts tools and picks
  the prompt; the return tools read `return_reason` and `target_line` from signals rather than
  asking the LLM to invent them. Signals are shown in a dev-only "why" panel and traced.
- Metrics: Jev latency, fallback rate, low-confidence rate per question, cost (input tokens × price).

## Evals

- `evals/assistant/jev_routing.jsonl`: labeled turns (intent, reason, target line) built from the
  returns and Q&A scripts, including noisy/voice-like transcripts.
- `evals/jev_eval.py`: accuracy and act-rate per question for Jev vs the baseline (LLM router or
  simulator), latency, and cost — the comparison the plan asked for. Runs against the real API
  when keyed; the simulator run is the baseline in CI.

## Tests

Unit: request payload shape; response parsing; thresholds → decisions; errors → fallback;
simulator determinism; `voice_yes` AND-gate never confirms on Jev alone.
