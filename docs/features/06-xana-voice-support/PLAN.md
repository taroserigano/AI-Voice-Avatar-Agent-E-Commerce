# 6. Support tab: voice returns and refunds with Xana — plan

## Goal

A **Support** tab (`/support`) centered on **Xana**, a customer-support agent customers can talk to
by voice (or type to) about returns, refunds, and orders. Xana finds the order and item, explains
eligibility from the policy engine, shows an exact quote, and starts the return only after the
customer confirms, by the on-screen button or a clear spoken "yes" that the app (not the model)
verifies. Refund status questions read live records.

## Depends on

- Item 5 (assistant service, graph, tools, chat UI) and item 3.3 (Jev signals).
- The returns engine on branch `design-ratings-sitemap` (policy rules, `return_options`,
  `ReturnRequest`/`ReturnItem`/`RefundAttempt`, payments). That branch must be committed and
  merged into `catalog-stores` first; quote/confirm are built on it, not beside it.

## Returns backend (commerce)

- `return_quotes` table: owner, order, lines (line, quantity, per-unit refunds), reason code,
  refund timing, shipping refund, total, policy version, `quote_hash` (SHA-256 of the canonical
  terms), `expires_at` (15 min), `token_hash`, `used_at`, `return_id`.
- `POST /v1/returns/quote` — owner check; recomputes with `line_eligibility` / `refund_for` /
  `whole_order_shipping_refund`; refuses ineligible lines with the reason; returns the quote.
  Allowed for the assistant's service identity.
- `POST /v1/returns/quotes/{id}/confirmation` — **browser session only**; mints a single-use
  token (returned once, stored as a hash, bound to user + quote hash).
- `POST /v1/returns/confirm` — **browser session only**; needs `quote_id`, `confirmation_token`,
  `Idempotency-Key`; rechecks ownership, expiry, hash, returned quantities; creates exactly one
  `ReturnRequest` (+ items), marks the token used, writes an outbox event. A repeat with the same
  key returns the same return.
- Refund processing stays simulated (no Stripe checkout exists yet): instant-eligible returns are
  refunded by a dev "carrier scan", others by a dev "inspect"; perishables are refunded on
  confirm. Dev endpoints `POST /dev/returns/{id}/carrier-scan` and `/inspect` (dev only).
  Temporal and Stripe replace this in Milestone 3; the records and states are the same.
- `GET /v1/returns` / `GET /v1/returns/{id}` for status (owner only).

## Assistant (Xana)

- Same graph, persona `xana` (`prompts/xana.v1.md`): support-first, short spoken sentences.
- Extra tools: `get_return_options(order_id)`, `quote_return(order_id, line_id, quantity)`
  (reason from Jev signals), `propose_return(quote_id)` — pauses the graph with `interrupt()`
  and sends a quote card; `get_refund_status`. No confirm tool.
- Resume: after the browser's confirm succeeds (or is declined/expired), the browser posts the
  outcome to the assistant, which resumes the graph with the result from the commerce API.

## Voice (no LiveKit yet)

- Browser: mic permission, push-to-talk and hands-free modes, energy-based voice detection
  (Web Audio), MediaRecorder capture, live state (listening / thinking / speaking), captions,
  mute, stop, interruption (speech during playback stops audio within ~300 ms and cancels the
  turn), text fallback always visible.
- `POST /v1/voice/turn` (assistant): audio → STT → graph turn → streamed SSE: `transcript`,
  `text`, `card`, `audio` (sentence-by-sentence TTS chunks), `done`.
- STT adapters: Deepgram (if keyed) → Groq Whisper (`whisper-large-v3-turbo`, keyed today) →
  browser Web Speech API (labeled). TTS: Cartesia `sonic-3.6-2026-08-27` (keyed, a support voice)
  → browser speech synthesis (labeled). A **transcript simulator** (type what you'd say) runs the
  same voice states without any keys.
- **Voice confirmation (app-controlled):** when a quote card is pending, Xana reads back the
  item, amount, and refund method. A spoken confirmation counts only if: the read-back played in
  full; the transcript is final; it matches the strict affirmative rule (e.g. "yes", "yes,
  confirm", "confirm the return"; rejects "mm-hmm", "yeah maybe", "yes but…", questions, and
  anything under the duration floor); and Jev's `voice_yes` ≥ 0.90 when Jev is on. Then the
  browser (not the assistant) mints the token and calls confirm. Otherwise Xana asks again or
  points to the button.
- Caps: voice turns per conversation, audio length per turn, minutes per day per user.
- Notice on the page: Xana is an AI assistant; audio is sent to the named speech providers and
  not stored; transcripts are saved with the conversation.

## Page

`/support`: hero with Xana, big mic button and state ring, captions/transcript, order picker
cards, quote card with Confirm/Cancel, return status timeline, "talk to a person" (support case),
FAQ links into `/returns-policy`, and the text box. Header gets a **Support** tab. The order
page's "Start a return" (other branch) opens `/support?order=…`.

## Tests

- Commerce: quote math matches the eval oracle for every seeded scenario; altered/expired quote
  and reused token rejected; double confirm returns the same return; Bob can't quote Alice's
  order; the assistant's service identity is refused on token/confirm.
- Assistant: `propose_return` interrupts and resumes; no token in any model message, tool result,
  or checkpoint (scan the checkpoint); returns scripts in `evals/assistant/returns.jsonl` pass
  with the scripted model.
- Voice: affirmative-rule table test (mm-hmm, yeah maybe, background speech…); AND-gate; e2e
  with the transcript simulator: start a return by "voice", confirm by saying yes, see status.
