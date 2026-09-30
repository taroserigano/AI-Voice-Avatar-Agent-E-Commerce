# 10. Xana avatar (Tavus): plan

Status: **A0 spike done, A1 in progress** (2026-09-30). Branch `xana-avatar`. Spike numbers:
[IMPL.md](IMPL.md).

## Goal

Give Xana a face on the voice screen. A Tavus video avatar replaces the orb and lip-syncs to
Xana's own voice. Everything else stays as it is: our speech-to-text, our brain (Luna, and Sol
when code escalates), Cartesia Sonic with the Skylar voice, fillers, captions, and the
confirmation rule.

- The avatar is **opt-in per call** (a "Video" toggle) and **off unless configured**.
- If the avatar fails, the call carries on as voice with the orb. The customer never loses the
  call because of video.
- The avatar adds as little delay as possible. Measured in the spike: Tavus adds **~0.8 s**
  to "first words" (p50 790 ms), more than the 0.5 s hoped for, so Video stays opt-in, off by
  default.

## Decisions (Taro, 2026-09-30: approved)

| # | Decision |
|---|---|
| 31 | **Tavus renders Xana's face in echo mode.** Tavus only animates the face. It does not run its own speech-to-text, LLM, voice, or perception. Our pipeline still decides every word. This lifts "avatar" out of decision 30; phone and cloud deploy stay out of scope. |
| 32 | **The browser joins the Tavus room and feeds it Xana's audio**, on today's WebSocket stack. The server creates the Tavus conversation; the key never reaches the browser. When LiveKit (plan 09, V1) lands, the worker can use `tavus.AvatarSession` instead, but only where Tavus can reach the LiveKit server (LiveKit Cloud, which decision 30 leaves out for now). Locally, a Tavus avatar can't join a `livekit-server --dev` on this laptop, so the browser bridge is the path that works here. |
| 33 | **Only Xana's voice goes to Tavus, never the customer's.** The customer's microphone and camera are never published to the Tavus room. Recording, transcription and captions are off on Tavus's side. |
| 34 | Face: **Anna – Casual** (`rc9cff32ceba`), a stock Phoenix-4.5 face (Tavus recommends these for real time). Taro asked for "a beautiful white female model". Setting `TAVUS_FACE_ID`. |
| 35 | Feed: **audio echo messages** (`conversation.echo`). Microphone echo was silent in the spike. |

## How it works

```
 Browser /support/voice                                    services/voice (:8103)
 ┌─────────────────────────────────────┐   WebSocket (unchanged)  ┌───────────────────────────┐
 │ mic ──PCM──────────────────────────────────────────────────▶   │ ears → brain → mouth      │
 │                                     │ ◀── Xana PCM + captions ─│ (Sonic Skylar)            │
 │ Xana's audio chunks                 │                          │                           │
 │   ├─ avatar off: → playback worklet │ ── avatar.start ───────▶ │ face_tavus.py:            │
 │   └─ avatar on:  → echo messages    │ ◀── avatar {url, token} ─│  POST /v2/conversations   │
 │                                     │                          │  (echo PAL, private room) │
 │ Daily call (daily-js)               │                          │  POST …/end on hang-up    │
 │   publishes: nothing (no mic/camera)│                          └───────────────────────────┘
 │   sends: conversation.echo messages │
 │   receives:  Tavus face video+audio │
 │   <video> where the orb was         │
 └────────────────┬────────────────────┘
                  │ WebRTC
                  ▼
        Tavus (Daily room, face rendering)
```

1. The customer turns on **Video**. The browser sends `avatar.start` on the existing
   WebSocket, which is already signed in and origin-checked.
2. The voice service creates a Tavus conversation: echo PAL, `require_auth: true`, short
   timeouts. It sends back the room URL and the short-lived meeting token, only to this
   customer.
3. The browser joins the room with `daily-js` as a call object (our own UI, no Tavus
   iframe), with microphone and camera off: it publishes nothing. Each chunk of Xana's audio
   that arrives on the WebSocket goes to Tavus as a `conversation.echo` message (base64
   PCM16, 24 kHz; `done: true` on a segment's last chunk) instead of to the playback worklet.
4. Tavus lip-syncs to that audio and sends back video with the same speech. The browser shows
   the video where the orb was. Our own audio isn't played locally, so nothing plays twice.
5. Hang-up, WebSocket close, or "Video off": the browser leaves the room, and the server ends
   the conversation (`POST /v2/conversations/{id}/end`), so billing stops.

**Why echo messages, not microphone echo:** the plan first preferred publishing Xana's audio
as a WebRTC "microphone" track. In the spike, Tavus never spoke that audio (twice), while echo
messages worked, carried speaking events, and accepted 1 s chunks (64 KB messages).
Tavus's `inference_id`s in events don't match ours, so segments are matched in order.

## What changes

| Part | Change |
|---|---|
| **`services/voice/config.py`** | `tavus_api_key` (env `TAVUS_APIKEY`, alias `TAVUS_API_KEY`), `tavus_pal_id`, `tavus_face_id`, `voice_avatar: "off" \| "tavus"` (default `off`), `tavus_max_live` (default 2, the most avatar calls at once, to stay within the account's limits). |
| **`face_tavus.py`** (new) | Creates and ends Tavus conversations with `httpx`. Request: `pal_id`, `face_id`, `require_auth: true`, `conversation_name: "xana-<conversation id>"` (no names or emails), `properties`: `max_call_duration` = the voice session limit, `participant_absent_timeout` 30 s, `participant_left_timeout` 10 s, recording, transcription and captions off. Times out fast; any failure means "no video", never a failed call. |
| **`app.py` / `session.py`** | New messages: `avatar.start` / `avatar.stop` in, `avatar` (url, token) and `avatar.unavailable` (reason) out. One avatar per call. The conversation is ended in the same `finally` that closes the ears and mouth. `ready` says whether video is available. |
| **`scripts/tavus-setup.mjs`** (new, `pnpm tavus:setup`) | Creates or updates the echo PAL "Xana (ai-commerce echo)" with the chosen face and prints `TAVUS_PAL_ID` for `.env`. Nothing creates Tavus resources at runtime without being asked. |
| **Web: `use-xana-avatar.ts`** (new) | Joins and leaves the Daily room, sends Xana's audio chunks as echo messages, finds the Tavus participant's video and audio, reports speaking events, and falls back to the orb if the join fails or no video arrives within 8 s. |
| **Web: `xana-avatar.tsx`** (new), `xana-voice-screen.tsx` | The video in the orb's place, same size and dark stage; the state ring stays around it. A "Video" toggle next to Mute, shown only when the server offers video. |
| **Captions** | Captions follow the player's clock. With video, Tavus adds a delay, so the clock is shifted by the measured delay (from Tavus's `started_speaking` event) and the words stay in step with the lips. |
| **Notice** | With video on: "Xana's replies (not your voice) are sent to Tavus to animate her face." |
| **Dependency** | `@daily-co/daily-js` in `apps/web`. No new Python packages (plain `httpx`). |

## Safety: confirmation and barge-in with video

Today the browser reports a segment as played in full when the worklet has played it. With
video, the customer hears it later, after Tavus renders it. So:

- **The read-back counts as heard only when Tavus has said it.** With video on, the `played
  complete` for a segment is sent on the first `conversation.pal.stopped_speaking` with
  `interrupted: false` after that segment's last chunk was sent. `interrupted: true` never
  counts. A "yes" before that is "unclear", as it is today.
- **Barge-in:** on the server's `drop`, the browser stops sending the dropped segments and
  sends `conversation.interrupt`. Measured: silence ~0.5 s later (vs ~0.3 s without video).
- Nothing about the model changes: no confirm tool, eligibility and amounts come only from
  commerce, and the browser still confirms with the quote-bound token and Idempotency-Key.

## Privacy and cost

- Tavus gets Xana's speech: the customer's first name, and order items and amounts in answers
  and read-backs. It never gets the customer's voice, camera, email, or address.
- The room is private (`require_auth`); the token expires with the join window; the URL and
  token go only to the signed-in customer who owns the call.
- Tavus bills per minute. The conversation exists only while Video is on and ends on hang-up.
  `max_call_duration` stops it anyway; `tavus_max_live` limits how many run at once; each
  call's avatar minutes are logged.
- Tests use `test_mode: true`, which Tavus doesn't join or bill.

## Phases

| Phase | Scope | Done when |
|---|---|---|
| **A0 Spike** ✅ | Echo PAL in both feed modes, real Skylar clips, three short calls. | Done: numbers in `IMPL.md`, echo messages chosen, ~0.8 s added |
| **A1 Server** | Settings, `face_tavus.py`, `avatar.*` messages, end on close, the limit on concurrent avatars, `pnpm tavus:setup`. | Unit tests (below) pass; live create and end with `test_mode` passes when the key is set |
| **A2 Browser** | `daily-js`, `use-xana-avatar`, `xana-avatar.tsx`, toggle, audio routing, fallback to the orb, caption delay. | With video on, a real call answers a question on screen; with the key removed, the page shows the orb and says video isn't available |
| **A3 Safety with video** | Read-back gating on Tavus events, `conversation.interrupt` on barge-in. | Confirmation and barge-in tests (below) pass, with video on and off |
| **A4 Measure** | The live e2e (`VOICE_E2E_LIVE=1`) with video: first words, barge-in, avatar minutes per call. The golden evals don't change (they're text). | Numbers written down; Taro decides whether Video starts on or off |

## Tests that matter

- The Tavus key never reaches the browser, and the create request carries no name, email, or
  address (`conversation_name` is the conversation id only).
- The browser publishes no track to the Tavus room (microphone and camera off). With video on,
  nothing from the customer's mic reaches Tavus.
- A spoken yes during or before Tavus finishes the read-back is "unclear". An interrupted
  read-back never counts as heard.
- Hang-up, a dropped WebSocket, and "Video off" each end the Tavus conversation exactly once.
  A failed end is retried once and logged.
- A Tavus failure (no key, 4xx/5xx, timeout, join failure, no video in 8 s) leaves a working
  voice call with the orb and a short message.
- Only the signed-in owner of the call gets the room URL and token; a third avatar call past
  `tavus_max_live` gets `avatar.unavailable`.
- Barge-in with video: Xana goes quiet within the target, and the dropped segment's captions
  disappear as they do today.

## Sources

- [Tavus echo mode](https://docs.tavus.io/sections/conversational-video-interface/echo-mode.md) (text, audio, and microphone echo)
- [Tavus pipeline modes](https://docs.tavus.io/sections/conversational-video-interface/quickstart/pipeline-modes.md)
- [Tavus private rooms](https://docs.tavus.io/sections/conversational-video-interface/conversation/customizations/private-rooms.md) (`require_auth`, `meeting_token`)
- [Tavus speaking events](https://docs.tavus.io/sections/event-schemas/conversation-started-stopped-speaking.md) (`interrupted`, `duration`)
- [Tavus OpenAPI](https://docs.tavus.io/openapi.yaml) (create conversation, `conversation.echo`, `conversation.interrupt`)
- [Tavus in LiveKit Agents](https://docs.tavus.io/sections/integrations/livekit.md) (for after plan 09's V1)
