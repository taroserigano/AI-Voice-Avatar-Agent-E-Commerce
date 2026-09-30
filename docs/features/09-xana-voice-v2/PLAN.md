# 9. Xana voice v2: plan

Status: **plan only** (2026-09-27). Nothing here is built yet.

## Goal

Move Xana's real-time voice agent from our own WebSocket pipeline to **LiveKit** (WebRTC plus
LiveKit Agents). Keep everything that made today's version fast and safe, and make it:

- **faster**: the first words of a real answer ≤ 1.6 s after the customer stops speaking
  (today 2.3 s), policy answers ≤ 2.5 s (today 3.2 s), and the return read-back ≤ 3 s
  (today ~7 s);
- **sturdier** on real networks: WebRTC handles jitter, packet loss, echo and mobile networks;
- **smarter** on hard cases: GPT-6 Sol for the few turns that need it;
- **observable and redacted**: every stage timed, with no personal data in traces.

## Decisions (Taro, 2026-09-27)

| # | Decision |
|---|---|
| 24 | Transport is **LiveKit WebRTC** and the agent is a **LiveKit Agents** worker (Python). Locally, `livekit-server --dev` runs as a native Windows binary from `pnpm local:up` (no containers). |
| 25 | Speech-to-text: **Cartesia Ink-2 is the candidate**, with LiveKit's turn-detector model deciding end of turn. It is adopted only if it beats `gpt-live-transcribe` in a measured A/B (phase V2). The loser stays available behind `VOICE_STT`. |
| 26 | LLM: **gpt-6-luna** for every turn. **gpt-6-sol** only when code-side rules escalate, never on the model's own judgment. |
| 27 | Text-to-speech: **Cartesia Sonic 3.6, voice Skylar** (unchanged). |
| 28 | RAG stays on **Qdrant** (decision 23), with OpenSearch keywords, fused by RRF. No Pinecone. |
| 29 | **Temporal** runs returns and refunds after confirmation. **Redis** is cache only. **Presidio** redacts traces and logs. **OpenTelemetry** plus **LangSmith** for tracing. |
| 30 | Out of scope for now: **avatar**, **phone calls**, **cloud deploy** (ECS/Fargate, LiveKit Cloud). The design leaves room for each (see "Later"). |

Model check, 2026-09-27: the OpenAI key lists `gpt-6-luna` and `gpt-6-sol`.

## Target architecture

```
 Browser (Next.js /support/voice)                       Our services (local)
 ┌──────────────────────────────┐   POST /v1/voice/token  ┌──────────────────────────────┐
 │ Meet Xana screen (unchanged) │ ──── session cookie ──▶ │ voice API (FastAPI)          │
 │ livekit-client:              │ ◀── LiveKit JWT ─────── │  /v1/auth/me → customer id   │
 │  mic track (AEC/NS on)       │                         │  room = xana-<conversation>  │
 │  Xana audio track            │                         │  dispatches the Xana agent   │
 │  captions (aligned words)    │                         └──────────────────────────────┘
 │  RPC/data: cards, quote,     │
 │   citations, metrics         │        WebRTC (UDP)     ┌──────────────────────────────┐
 └──────────────┬───────────────┘ ◀────────────────────▶  │ livekit-server --dev :7880   │
                │ confirm (unchanged):                    └──────────────┬───────────────┘
                │ /v1/returns/quotes/{id}/confirmation                   │
                ▼ → /v1/returns/confirm + Idempotency-Key                ▼
 ┌──────────────────────────────┐                         ┌──────────────────────────────┐
 │ commerce API (FastAPI)       │ ◀── service token + ─── │ Xana agent worker            │
 │  orders, returns, policies   │     X-On-Behalf-Of      │  (LiveKit Agents)            │
 │  hybrid search: OpenSearch   │                         │  Silero VAD + turn detector  │
 │   + Qdrant (RRF)             │                         │  STT: Ink-2 | live-transcribe│
 │  starts Temporal workflow    │                         │  llm_node → XanaBrain        │
 └──────┬──────────────┬────────┘                         │   (LangGraph, Luna → Sol)    │
        ▼              ▼                                  │  TTS: Sonic 3.6 Skylar       │
   PostgreSQL     Temporal worker                         │  fillers, confirm rule       │
   (records,      (return → label →                       └──────┬───────────────────────┘
   checkpoints)    refund on scan)                               ▼
                                                        Redis (cache only), OTel → LangSmith
```

### What each part does

| Part | Role | Notes |
|---|---|---|
| **Token endpoint** `POST /v1/voice/token` | Checks the session cookie via `/v1/auth/me` and conversation ownership, then mints a short-lived LiveKit token: identity = customer id, room = `xana-<conversation_id>`, publish mic only. | The agent trusts the participant identity because only our server mints tokens. The browser never names the customer. Origin allowlist stays. |
| **Agent worker** `services/voice` | A LiveKit Agents `AgentSession` per room. | Replaces `app.py`'s WebSocket, `vad.py`, `ears_openai.py` and the audio worklets. Keeps `brain.py`, `speech_text.py`, `fillers.py`, the confirm rule and the prompts. |
| **Turn taking** | Silero VAD, LiveKit's turn-detector model, `preemptive_generation=True`. | Preemptive generation replaces our Draft → Final early start. Barge-in uses `min_interruption_duration` 0.25 s, with false-interruption resume. |
| **Brain** | Our own `llm_node` override calls `XanaBrain.turn()`. | Not `LLMAdapter`: it rebuilds history from LiveKit's chat context each turn. We keep the Postgres checkpointer thread (the same one chat uses), the policy prefetch, the orders snapshot, the early tool announcements and the quote events. |
| **Voice** | `cartesia.TTS(model="sonic-3.6-2026-08-27", voice=Skylar)`, `use_tts_aligned_transcript=True`. | Word timings drive captions, as they do today, but LiveKit syncs them to playout. |
| **Side channel** | LiveKit RPC and data topics: `xana.card`, `xana.quote`, `xana.citations`, `xana.metrics`; browser → agent `quote.outcome`. | Same messages as `voice-protocol.ts`, minus the audio framing. |
| **Confirmation** | Unchanged. The model has no confirm tool. A spoken yes counts only after a complete read-back and the strict rule plus Jev veto pass. The **browser** then confirms with the store using the quote-bound token and an Idempotency-Key. | Covered by the existing session tests, ported. |

## Speed plan (latency budget)

End of speech → first audio of the real answer, simple question:

| Stage | Today | Target | How |
|---|---|---|---|
| End-of-turn decided | ~0.36–0.65 s (our VAD) | 0.25–0.45 s | turn-detector model, shorter silence when the sentence is complete |
| Transcript ready | ~0.3 s after | overlaps | preemptive generation starts the LLM on the interim transcript |
| LLM first token | 0.8–1.5 s | ≤ 0.8 s | Luna, priority tier, a stable prompt prefix for caching, snapshot and prefetch ready before the call, connection kept warm |
| First clause → TTS audio | ~0.13 s | ~0.13 s | unchanged |
| Network / playout | local WebSocket | +0.05–0.1 s | WebRTC |
| **Total** | **2.3 s** | **≤ 1.6 s** | Filler at 0.9 s if no answer audio yet |

**Returns, from ~7 s to ≤ 3 s.** Today the model makes three calls in a row (options → quote →
propose). Add one server tool, `prepare_return(order, items, reason)`, that runs eligibility,
pricing and the quote in a single commerce call (`POST /v1/returns/prepare`) and returns the
read-back. One model call instead of three. Eligibility and amounts still come only from
commerce.

## Luna → Sol escalation

Luna answers every turn. Code, not the model, moves a turn to Sol when any of these hold:

- a tool failed twice in the same turn;
- the customer repeats or rephrases the same request after an answer, or says it is wrong;
- a dispute: damaged, wrong or missing item, a missing refund, or a charge question;
- a return with more than two items or mixed return classes.

Limits: one Sol call per turn, at most three per call. A filler always plays first. If Sol has
not started speaking within 4 s, Luna's answer is used. Evals (V5) decide whether these rules
earn their place.

**Built early, on the current voice agent (2026-09-30):** `services/voice/src/ai_commerce_voice/escalation.py`.
The dispute, "that's wrong" or repeated question, and two-failed-tools rules are in. The
more-than-two-items rule isn't: the item count isn't known until the model has quoted. The
limits above aren't built yet. An escalated turn uses Sol for all its model calls, and there's
no 4 s fallback: measured, Sol started speaking no later than Luna on the same turns.

Also measured, on the golden sets (`evals/xana`), and left out: escalating every return, refund,
or policy question. That was 185 of 413 turns. It scored the same as Luna alone (returns 188/198
both ways, products 198 vs 197 of 200), at the same speed (median first words 2.29 s vs
2.32 s), and Sol costs more. Sol fixed some of Luna's misses and made others.

## Other layers

| Layer | Plan |
|---|---|
| **Temporal** | New, since nothing uses it yet. `ReturnWorkflow` (id = return id) starts after confirmation: issue label → wait for carrier scan → refund through Stripe (test mode) → notify. Activities are idempotent, and the outbox stays the event source. It runs locally with `temporal server start-dev` (a native binary) from `pnpm local:up`. |
| **Redis** | Cache only; everything works when it is down. Caches: policy search results (query hash, 10 min), each customer's orders snapshot (30 s, dropped on order events), rendered filler clips (instead of `.cache/fillers`), and token-endpoint rate limits. Locally on Windows: **Garnet** (Microsoft's Redis-compatible server, native). |
| **Presidio** | Off the live path. It redacts transcripts and tool text in OTel spans and LangSmith runs, and in logs, on top of `packages/telemetry/redaction.py`. Allowlist: order numbers, SKUs, RMA numbers, prices. Use the small spaCy model plus custom recognizers (name, address, phone, email, card). |
| **OTel + LangSmith** | One trace per voice turn, with spans: `vad.end`, `stt.final`, `llm.first_token`, `tts.first_audio`, `playout.start`, plus tool spans. LiveKit telemetry with `allow_pii=False`. LangSmith gets graph runs only after redaction. The dev metrics line on screen reads from the same numbers. |
| **PostgreSQL** | Unchanged: records, conversations, checkpoints. Voice transcripts go into the same conversation thread as chat. |

## Phases

| Phase | Scope | Done when |
|---|---|---|
| **V0 Measure** | A fixed set of 30 recorded questions (orders, policies, returns, with noise and accents) plus a runner that reports each stage's time and grades each answer. Run it on today's stack. | Baseline numbers written down |
| **V1 LiveKit** | Add `livekit-server` to `local:up`, the token endpoint, the agent worker (current STT, XanaBrain via `llm_node`, Sonic Skylar, fillers, confirm rule) and the web client on `livekit-client`. Old WebSocket stays behind `VOICE_TRANSPORT=ws` until parity. | Ported session tests, e2e (live) and V0 pass, no slower than baseline; then the WebSocket path is deleted |
| **V2 STT A/B** | Ink-2 + turn detector vs `gpt-live-transcribe` + turn detector, on the V0 set. | Winner picked by end-of-turn time and word accuracy, especially order numbers |
| **V3 Faster, smarter turns** | `prepare_return` (one call), Luna → Sol router, Redis caches. | Read-back ≤ 3 s; simple answers ≤ 1.6 s p50 |
| **V4 Durable and private** | Temporal `ReturnWorkflow`, Presidio redaction, OTel spans, LangSmith. | Return survives a worker restart; no personal data in a sampled trace |
| **V5 Evals and gates** | Voice evals in the eval suite: latency p50/p95, answer accuracy, citation correctness, and the confirmation safety cases (a yes before the read-back, an unclear yes, a new request during a quote). | Safety cases block merges |

## Tests that matter

- A spoken yes never confirms without a full read-back, the strict rule and the browser confirm. The model has no confirm tool, even with Sol.
- The token endpoint refuses a missing cookie, another customer's conversation and a bad origin.
- Another customer can never join a room or receive its data messages.
- Barge-in stops Xana within 300 ms; a cough doesn't.
- The Temporal refund runs once under retries and restarts.
- With Redis, Qdrant or Sol down, answers still come, only slower.

## Later (designed for, not built)

- **Avatar**: a LiveKit avatar plugin joins the room as a video participant. Audio passes through untouched, so speech never waits on video. Now planned with Tavus on today's stack: [plan 10](../10-xana-avatar/PLAN.md).
- **Phone**: LiveKit SIP plus a carrier trunk. It needs a caller-verification step before any order tool, and a server-side confirmation path, because there is no browser.
- **Cloud**: the API, workers and web on ECS/Fargate; media on LiveKit Cloud or EC2, because Fargate handles UDP port ranges badly.

## Sources

- [Cartesia STT in LiveKit Agents](https://docs.livekit.io/agents/models/stt/cartesia/) (Ink-2, `turn_detection="stt"`, plugin ≥ 1.5.15)
- [LiveKit turn detector](https://docs.livekit.io/agents/build/turns/turn-detector)
- [LiveKit agent session](https://docs.livekit.io/agents/logic-structure/sessions/) (`preemptive_generation`, `use_tts_aligned_transcript`)
- [LiveKit LangChain / LangGraph adapter](https://docs.livekit.io/agents/models/llm/langchain/)
- [Running LiveKit locally](https://docs.livekit.io/transport/self-hosting/local/)
