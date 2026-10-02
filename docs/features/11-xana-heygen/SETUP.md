# Xana avatar providers

Implementation lives in the `xana-avatar` worktree. Both tabs use Xana's existing voice
service, conversation, Cartesia audio, and return controls.

## Routes

- `/support/voice` — Tavus selected.
- `/support/voice/tavus` — Tavus selected.
- `/support/voice/heygen` — HeyGen selected.

Choose a tab, start talking, then turn Video on. Selecting a tab before a call creates no
provider session. During active video, a switch interrupts the reply, pauses microphone
input, stops the old provider, joins the selected provider, and restores the previous mute
setting. If video cannot connect within 45 seconds, the call returns to voice.

The same conversation and pending return survive tab changes. The conversation ID is also
kept in session storage for reconnects in that browser tab; the server still verifies ownership.
An interrupted return readback requires the Confirm return button. HeyGen uses button
confirmation until its actual audio playout has passed a connected acceptance test.

## Server settings

Keep existing Tavus, Cartesia, and OpenAI configuration. Add:

```dotenv
VOICE_AVATAR=both
LIVEAVATAR_API_KEY=your_liveavatar_developer_key
HEYGEN_SANDBOX=true
HEYGEN_MAX_SESSION_S=60
HEYGEN_MAX_LIVE=2
```

Get the key from [LiveAvatar developers](https://app.liveavatar.com/developers).
`HEYGEN_LIVE_APIKEY` and `HEYGEN_LIVE_API_KEY` are also accepted names for this key.
A HeyGen video API key (`HEYGEN_APIKEY`) is a different credential and is not accepted here.
The initial read-only checks found that the supplied HeyGen key authenticated the video
catalog but received HTTP 401 from LiveAvatar. No billable session was created.
The subsequently supplied `HEYGEN_LIVE_APIKEY` authenticated successfully, and a connected
browser sandbox check passed on 2026-09-30.

Sandbox uses LiveAvatar's designated Wayne avatar, with a maximum 60-second session.
For a selected production presenter, set `HEYGEN_SANDBOX=false` and
`HEYGEN_AVATAR_ID=<a LiveAvatar avatar ID>`. Increase `HEYGEN_MAX_SESSION_S` only within the
account's duration limit. A Tavus face ID is not a LiveAvatar avatar ID.

### Root .env shared with the worktree

`pnpm dev` supports an explicit shared env file. From the Xana worktree in PowerShell:

```powershell
$env:VOICE_SHARED_SECRETS_FILE = "../../../.env"
$env:VOICE_AVATAR = "both"
pnpm dev
```

Process variables override the worktree's own `.env`; the worktree overrides the shared
file. Only allowlisted avatar settings enter the voice child. Shared credentials never
enter the web child. Other services keep their existing settings. `pnpm dev:voice` uses
the same shared-file loader, and reads `VOICE_SHARED_SECRETS_FILE` from either its process
environment or the worktree's `.env`. Restart the voice service after changing configuration.

The configured local Xana checkout uses web port 3200, its own voice port 8303, and the
existing commerce service at 8100. Its conversation storage uses the existing local
`commerce_main` database. Other running checkouts' voice services are left running.

## Behavior and limits

- API keys, session bearer tokens, and LiveKit agent tokens stay on the voice server.
  The authenticated browser receives only room/client and control socket credentials.
- Daily and LiveKit receive remote media only; user microphone/camera tracks are never
  published to either avatar provider.
- The customer sees an explicit Play avatar audio button if autoplay is blocked.
- The lifecycle keeps at most one provider room per call. A failed stop blocks a new start,
  retains capacity, and is retried every five seconds until stopped or its duration expires.
- Playback completions carry a generation. Old provider callbacks and cancelled segments
  cannot establish that a return readback was heard.
- Full process crashes still rely on provider duration limits. Network timeouts before a
  provider returns any session ID cannot be reliably reconciled by this client.
- LiveAvatar captions use estimated timing; actual latency, lip sync, and the chosen
  presenter still need validation with the correct key.

## Checks

```powershell
uv run --directory services/voice pytest tests/unit -q
pnpm --filter @ai-commerce/web exec vitest run lib/heygen-playback.test.ts lib/avatar-echo.test.ts lib/voice-captions.test.ts
pnpm --filter @ai-commerce/web exec tsc --noEmit
node --test scripts/voice-env.test.mjs
$env:WEB_URL = "http://localhost:3200"
pnpm --filter @ai-commerce/e2e exec playwright test specs/xana-providers.spec.ts --project desktop
```

The provider-switch browser test uses a fixture voice socket and silent microphone; it creates
no provider sessions. A separate opt-in test now verifies real sandbox video, Xana's generated
answer audio, correlated playback completion, and shutdown:

```powershell
$env:WEB_URL = "http://localhost:3200"
$env:HEYGEN_E2E_LIVE = "1"
pnpm --filter @ai-commerce/e2e exec playwright test specs/xana-heygen-live.spec.ts --project desktop
```

The live test uses the configured sandbox avatar and a short OpenAI/Cartesia answer.
It disables traces to avoid persisting session credentials. The connected check returned
1280×720 video, remote audio, an answer completion, and a successful provider stop.
Remaining acceptance includes real Tavus ↔ HeyGen switching during speech, target-browser
reconnect/autoplay, and measured end-of-audio timing. Spoken confirmation stays disabled
for HeyGen until that gate passes.

Contracts: [LiveAvatar LITE events](https://docs.liveavatar.com/docs/lite-mode/events),
[session lifecycle](https://docs.liveavatar.com/docs/lite-mode/lifecycle),
[sandbox mode](https://docs.liveavatar.com/docs/sandbox-mode).
