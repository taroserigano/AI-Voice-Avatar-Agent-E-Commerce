# 6. Xana voice support — implementation

Status: **done** (2026-09-26) with turn-based voice. LiveKit streaming voice and Stripe refunds
remain for their milestones.

## Tasks

Merge
- [x] Merged `design-ratings-sitemap` (fast-forward to 2f66018; the other agent had already re-parented its migrations onto `aff3bd840644`)
- [x] Its `/help/returns` links to `/returns-policy`; its constants are checked against the policy `rules:` (web test); `SANDBOX_POLICY` and the quote expiry are checked too (Python test). Its order page never had the `/terms` link committed, so nothing to change there.

Commerce returns
- [x] `return_quotes` model + migration `7d3e9b41c2a8` (0006)
- [x] `returns/quotes.py` — price from saved amounts with the engine (`line_eligibility`, `refund_for`), perishable-reason rule, shipping only when the whole order comes back, canonical `quote_hash`, 15-minute expiry
- [x] `POST /v1/returns/quote` (assistant identity allowed) and `GET /v1/returns/quotes/{id}`
- [x] `POST /v1/returns/quotes/{id}/confirmation` (browser only) — single-use token, stored as a hash bound to customer + quote hash
- [x] `POST /v1/returns/confirm` (browser only, `Idempotency-Key`) — one return per quote (201, repeats 200), recompute-and-compare, outbox `return.confirmed`, activity events
- [x] `GET /v1/returns`
- [x] Simulated refunds: perishables at confirmation; `POST /v1/returns/{id}/dev-advance` (dev only) for carrier scan / receipt / inspection, one refund per stage, forward only; `POST /v1/returns/dev-reset` (dev only) for repeatable demos and tests
- [x] `POST /v1/support/cases`, `GET /v1/support/cases` (the handoff tool opens real cases)
- [x] Tests (25): every seeded scenario's quote equals the eval oracle to the cent (and the refusals match); double confirm → one return; wrong/expired/stale/cross-quote tokens create nothing; the assistant can quote but gets 401 on token and confirm; Bob can't touch Alice's quotes; perishable reason rule and instant refund; simulated journey refunds each stage once

Assistant
- [x] `prompts/xana.v1.md`; voice note for spoken turns
- [x] Tools: `get_return_options`, `quote_return` (reason from Jev when the model leaves it out), `propose_return` (LangGraph `interrupt`, read-back built by code, outcome re-checked with the store after resume), `get_refund_status`; handoff opens a support case
- [x] `POST /v1/assistant/conversations/{id}/resume`; pending quote in conversation detail; a typed "yes" points to the button; moving on closes the waiting quote quietly
- [x] Scripted model runs the whole flow (orders → options → quote → propose → outcome) without an LLM key
- [x] Voice: `GET /voice/config`, `POST /voice/transcribe` (Groq Whisper / Deepgram), `POST /voice/speak` (Cartesia), `POST /voice/confirm-check` (strict rule, full read-back, final transcript, minimum length, Jev AND-gate that can only veto)
- [x] Tests: tool allowlist; 19 confirmation-gate cases; Xana flow integration (pause, typed yes, resume confirmed, store decides, wrong quote 409, moving on, voice checks, no token in checkpoints)

Web
- [x] `/support` page, **Support** tab in the header, voice stage (state ring, captions, hands-free, captions-only, privacy notice, provider labels), conversation with quote card (Confirm / Not now, countdown), return-options and return-status cards
- [x] `lib/use-voice.ts` — mic, energy-based end-of-speech detection, upload, playback with barge-in, browser fallbacks, simulated speech
- [x] `lib/returns-confirm.ts` — the browser mints the token and confirms with the store (per-quote idempotency key)
- [x] Order page **Start a return** → `/support?order=…&line=…` (was a disabled "Soon" button)
- [x] Steph hides on `/support`
- [x] e2e `xana-support.spec.ts`: button path (typed yes refused, confirm, axe), simulated voice path ("mm-hmm" refused, clear yes confirms), order page deep link

## Log

- Verified live through the web app: Groq Whisper transcribed a Cartesia clip in ~0.55 s; Cartesia
  speech in ~1.1 s; signed-out voice calls get 401.
- Found by the tests: on resume LangGraph re-runs the paused tool from the top, so its "quote must
  be open" check blocked the confirmed path; axe caught an unlabeled-role captions box and an
  invalid `<dl>` in the quote card.
- Not done here: LiveKit streaming voice, Temporal return workflow, Stripe refunds, the staff
  review queue (plan Steps 3, 4, 6).
