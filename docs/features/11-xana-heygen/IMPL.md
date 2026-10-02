# 11. Xana: HeyGen provider implementation log

## 2026-09-30: planning

- [x] Located the existing Tavus implementation in the `xana-avatar` worktree (`15f5dc1`).
- [x] Reviewed server session ownership, browser audio routing, captions, and quote read-back gating.
- [x] Checked LiveAvatar LITE documentation and OpenAPI for session and streaming contracts.
- [x] Wrote [PLAN.md](PLAN.md), including provider tabs/routes, serialized handoff, and acceptance gates.
- [ ] H0: Tavus baseline and LiveAvatar spike.
- [ ] H1: Shared session/playback contracts and cancellation/read-back separation.
- [ ] H2: HeyGen server and browser adapters.
- [ ] H3: Persistent provider routes and accessible tabs.
- [ ] H4: Acceptance tests, live measurements, and setup documentation.

No runtime files changed, automated tests executed, or provider sessions created during this planning step.

## 2026-09-30: root credential follow-up

- Taro added `HEYGEN_APIKEY` to the parent workspace root `.env`.
- Read-only authentication checks: HeyGen `/v2/avatars` returned HTTP 200; LiveAvatar
  `/v1/avatars` returned HTTP 401 for that key. No credential values or response bodies logged.
- The Tavus worktree has its own `.env` and does not currently contain either provider key.
- Updated the plan with the `LIVEAVATAR_API_KEY` requirement and explicit, voice-only
  loading of shared root secrets during worktree development.
- The provider session spike and final LiveAvatar avatar selection remain pending.

## 2026-09-30: implementation

- Implemented in the `xana-avatar` worktree, preserving the independently added Tavus
  look/background picker and green screen renderer.
- Added persistent layout and validated provider routes, accessible manual-activation
  tabs, Back/Forward support, and per-tab conversation resume storage.
- Added a server provider registry and serialized latest-selection-wins lifecycle.
  Slow creates do not block incoming socket messages. Late rooms are stopped, failed stops
  retain capacity/ownership, and the service retries cleanup every five seconds.
- Added LiveAvatar LITE token/start/stop calls and receive-only LiveKit + control WebSocket
  transport, pinned to `livekit-client@2.22.3`. No provider key, session bearer token, or
  LiveKit agent token is sent to the browser.
- Replaced the Daily-only browser hook with a generation-guarded dual-provider transport.
  Both remote audio and video tracks plus control readiness are required. Actual HTML media
  playback enables audio forwarding; autoplay failures expose an explicit retry button.
- Added bounded PCM buffering, utterance/source-event correlation, interruption, heartbeat,
  readiness deadlines, and disconnect fallback for LiveAvatar.
- Added a shared playback interface while retaining Tavus's existing measured timeline.
  Split scheduling completion from heard completion, added output generations, and stopped
  cancelled/stale readbacks from enabling spoken confirmation.
- Switching preserves the quote and mute preference, pauses microphone input during
  handoff, and uses button confirmation for the interrupted quote. HeyGen spoken
  confirmation remains disabled pending real playout verification.
- Added voice-only shared env loading with alias-aware precedence and documented
  configuration in [SETUP.md](SETUP.md). No user secret files were edited.
- Tightened an existing `with_brands` return annotation with a type cast while clearing
  the voice service's strict typecheck; runtime order behavior is unchanged.

### Verification

| Check | Result |
|---|---|
| Voice unit suite | 80 passed |
| Tavus + HeyGen playback and caption tests | 25 passed |
| Shared env allowlist/precedence test | 1 passed |
| Browser provider journey, Chromium against port 3200 | 1 passed |
| Web TypeScript | Passed |
| Voice mypy, 16 source files | Passed |
| ESLint for changed web files | Passed |
| Ruff for voice source and changed tests | Passed |

The browser journey uses a fixture voice socket and silent microphone, and covers:
no pre-call session creation, keyboard activation, active-video tab switching, one app
socket, retained mute/transcript/quote, stale response rejection, Video off, Back navigation,
direct HeyGen navigation, reconnect with the same conversation ID, invalid slugs, and Axe.
Adapter tests cover request payloads, secret exclusion, partial-start cleanup, capacity,
rapid selections, disconnect during create, failed-stop retry, and stale playback events.

### Remaining connected acceptance

- [x] H0: existing automated Tavus baseline.
- [ ] H0: LiveAvatar connected session spike (correct key still missing).
- [x] H1: shared lifecycle/playback contracts and readback cancellation protection.
- [x] H2: server/browser adapters with fixture verification.
- [x] H3: persistent provider routes and accessible tabs.
- [x] H4: automated acceptance and setup documentation.
- [ ] H4: actual Tavus ↔ HeyGen media handoff, latency/lip sync, target-browser
  autoplay/reconnect, production presenter selection, and provider usage returning to zero.

No live provider sessions were created during this implementation. The browser test is
not evidence of a connected LiveAvatar call. The app at port 3200 picked up UI edits through
the existing dev server; restart the voice service after adding its configuration.

## 2026-09-30: LiveAvatar credential connected

- Found the newly supplied `HEYGEN_LIVE_APIKEY` in the parent root `.env`; LiveAvatar's
  catalog returned HTTP 200. Added it and `HEYGEN_LIVE_API_KEY` as supported aliases,
  with canonicalization and exclusion from non-voice child environments.
- Added the standalone `pnpm dev:voice` launcher so it uses the same allowlisted shared
  env loader as `pnpm dev`. Credentials stay in the parent file.
- Set the ignored worktree env to `VOICE_AVATAR=both`, sandbox mode, and the explicit shared
  file pointer. The dedicated voice service runs at 8303. Ports 8103 and 8203 were already
  owned by other running voice processes and were left alone.
- Aligned the checkout's conversation storage with the existing local `commerce_main`
  database used by the app at commerce port 8100. The previous default database lacked
  `assistant_conversations`; no migrations or changes to that database were made.
- Configured and restarted the Xana web checkout at port 3200 with its dedicated voice URL.
- Server sandbox lifecycle: token HTTP 200, start HTTP 201, stop HTTP 200, adapter tracked
  session count zero after cleanup.
- Connected Chromium test passed: one remote audio track, one remote video track,
  **1280×720 video / 210 decoded frames**, provider speaking events, complete playback of an
  actual generated answer (not just its filler), return to listening, Video off, and call close.
  The service log confirms the browser session's stop returned HTTP 200.
- Focused checks passed: 6 Python configuration/adapter tests, 2 shared-env tests, E2E
  TypeScript, config mypy, and the connected browser journey. A preview is saved under
  `demo/heygen-sandbox.png`.

The initial connected attempt found a busy local port; the next found the old database
configuration. Both were corrected before the passing run. A subsequent check found the
existing web dev process had exited; it was restarted before the final passing run.

The sandbox currently displays Wayne and ends after approximately one minute. Production
presenter selection and real Tavus ↔ HeyGen handoff remain to be validated. HeyGen spoken
return confirmation remains disabled.
