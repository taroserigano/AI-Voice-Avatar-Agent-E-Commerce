# 10. Xana avatar (Tavus): implementation log

## A0 Spike (2026-09-30)

Taro approved decisions 31–34 and the spike, and picked the look ("a beautiful white female
model"): **Anna – Casual**, `rc9cff32ceba`, a stock Phoenix-4.5 face.

Setup: two echo PALs with that face (microphone echo on and off), one private conversation
(`require_auth`) each, headless Chromium joining with `daily-js` as a call object, fed real
Skylar clips (six fillers, 0.9–1.8 s, and one 13 s answer). Three calls, about 3 minutes
billed in all. Every conversation was ended by the script.

| Question | Answer |
|---|---|
| Does video arrive? | Yes. The PAL joins ~1.3 s after we join; first video frame at ~2.1 s. Tavus puts a "TAVUS" watermark in the corner. |
| **Microphone echo** | **Doesn't work** here. Our track was live and sending (~33 kbps audio), Daily showed it as playable, and Tavus never spoke it: no speaking events, silence back (peak level 3e-6), twice. |
| **Message echo** (`conversation.echo`, base64 PCM16, `sample_rate: 24000`) | Works. |
| Added delay: our audio sent → Tavus audio heard | 731, 811, 891, 781, 795, 782 ms (p50 ~790 ms). With 500 ms and 1 s chunks: 744 and 861 ms, so chunk size barely matters. |
| Largest message | 64 KB (1 s of audio per message) went through. |
| `started_speaking` event | ~550–680 ms after sending, about 150 ms **before** the audio is heard. |
| `stopped_speaking` | Carries `duration` (clip length + ~0.6 s) and `interrupted` (`false` when played through, `true` when cut off). Sent twice, as `pal` and the older `replica`. |
| `inference_id` in events | Neither ours nor an MD5-derived UUID of ours. Segments are matched **in order**, not by id. |
| Barge-in (`conversation.interrupt`) | Silence 665 ms after the interrupt, both times, measured with a 200 ms silence detector, so ~0.45–0.5 s in real terms. |

### What this changes in the plan

- **Feed mode: message echo.** Microphone echo is dropped. The browser sends each chunk of
  Xana's audio as a `conversation.echo` message as it arrives from the WebSocket; the last
  chunk of a segment has `done: true`.
- **Latency target:** video adds ~0.8 s to "first words" (2.3 s today → ~3.1 s). That's more
  than the 0.5 s the plan hoped for, so Video stays **opt-in**, off by default. A filler still
  plays if nothing is heard, and the filler timer needs to count Tavus's delay.
- **Read-back gating:** after the read-back's last chunk is sent, the next `stopped_speaking`
  (role `pal`) with `interrupted: false` marks it heard. `interrupted: true` never does.
- **Captions:** shift the player's clock by the time from the first chunk sent to
  `started_speaking`, plus ~150 ms.
- **Barge-in:** drop our queued audio and send `conversation.interrupt`; silence in ~0.5 s.

### Follow-up spike: segments back to back (two short calls, plus one stray re-run of mine)

| Case | Result |
|---|---|
| Filler (id A, `done`) then answer (id B) sent right after | **One** 2.4 s utterance: the answer was **dropped**. A new id while Tavus is speaking is lost. |
| Filler + answer under **one** id, then a 20 ms silent chunk with `done: true` | Both played: 4.3 s, not interrupted. |
| A segment, then a 20 ms silent chunk with `done: true` | Clean finish (`interrupted: false`). |
| 100 ms chunks at real-time pace | Tavus split one segment into two utterances at a short gap. |

So the browser sends everything Xana says in one turn under one `inference_id`, ends it with
a silent `done` chunk at `turn.done`, and holds the next turn's audio until Tavus has finished
the previous one. Whether a segment was heard in full is worked out on a playback timeline
(each segment starts when it's sent plus Tavus's delay, or when the one before it ends) and
confirmed by a `stopped_speaking` with `interrupted: false` at or after the segment's end.
Stop events alone can't be trusted, because Tavus splits utterances at gaps.

One of these calls was an accidental duplicate run (about 40 s billed); it ended itself.

## A1 Server (2026-09-30)

- [x] Settings in `services/voice/config.py`: `VOICE_AVATAR` (off by default), `TAVUS_APIKEY`
      (or `TAVUS_API_KEY`), `TAVUS_PAL_ID`, `TAVUS_FACE_ID` (default Anna – Casual),
      `TAVUS_MAX_LIVE` (2), `TAVUS_TEST_MODE`. Listed in `.env.example`.
- [x] `face_tavus.py`: `TavusFace` creates a private conversation (`require_auth`, name
      `xana-<conversation id>`, recording and captions off, `max_call_duration` = the voice
      session limit) and ends it (two tries; 400/404 means already ended). A process-wide
      limit on live avatars, reserved before the request so parallel starts can't overshoot.
      `AvatarLink` handles `avatar.start` / `avatar.stop` per call and ends the avatar in the
      call's `finally`. Any Tavus failure is `avatar.unavailable`, never a failed call.
- [x] `app.py`: `ready.avatar` says whether video is available (and the Tavus notice);
      `avatar.*` messages go to the link, everything else to the session.
- [x] `pnpm tavus:setup` (`ai_commerce_voice/tavus_setup.py`): finds or creates the echo PAL
      "Xana ai commerce echo" (Tavus strips punctuation from names, so names are compared
      normalized). Created `p544a255f656` with Anna – Casual. The spike PALs and one duplicate
      are deleted.
- [x] Tests: `tests/unit/test_face_tavus.py` (12: no personal data in the request, key never
      sent to the browser, ends exactly once on hang-up or Video off, retry on a failed end,
      the live limit incl. parallel starts, failures mean no video, a server without video
      says so). `tests/live/test_live_tavus.py` (`TAVUS_LIVE=1`): a real test-mode
      conversation is created with a meeting token and ends. Both pass.
- Face changed to **Rose – Business** (`rf1bd7e252de`): Taro asked for customer-support
      clothes (Anna – Casual wore a leather jacket). `pnpm tavus:setup` made PAL
      `p47f6df86787`; the Anna PAL is deleted. Screenshots of Rose idle and talking, from a
      40 s call: [screenshots/rose-sheet.png](screenshots/rose-sheet.png).

## A2 Browser (in progress)

- [x] `apps/web/lib/avatar-echo.ts`: `AvatarEcho` turns the agent's audio into echo messages
      (one id per turn, the next turn held until Tavus finishes, silent `done` chunk at
      `turn.done`, ~100 ms coalescing) and keeps the playback timeline for captions and "heard
      in full". A read-back only completes on a clean `stopped_speaking` at or after its end;
      other segments fall back to the timeline 3 s after their end.
      `avatar-echo.test.ts`: 13 tests pass.

## Xana's personality: prompt `xana.voice.v3` (2026-09-30)

Taro: "make her upbeat, a few little jokes, a super positive vibe". v3 is v2 plus a "Your
personality" section: cheerful in fresh words each time (no stock opener twice in a call), a
tiny kind joke now and then when the moment is light, and **no jokes, only a short, kind
apology, when something went wrong** (upset customer, damage, spoilage, a missing package, a
late refund, a charge, a refused return, allergies or safety). Personality changes only how
she sounds, never what she does. Fillers are a little brighter but safe before bad news. Emoji
are stripped before speech (`speech_text.speakable`), because the upbeat prompt let one slip
into 2 of 364 answers.

Face and voice: Tavus takes emotion tags only on text echoes (we send audio), and Cartesia's
emotion guidance works reliably only on its "Emotive" voices (Skylar isn't one) and needs the
tone to match the words, so the cheer comes from the words themselves.

Golden sets, voice channel, gpt-6-luna (products /200, returns /198):

| Wording | Products | Returns | Notes |
|---|---|---|---|
| v2 baseline | 197 | 187 | |
| v3, first draft | 197 | 186 | Damaged-item turns turned hesitant (a hand-off instead of a quote). Fixed by "personality never changes what you do". |
| v3, rules tightened | 198 | 192 | Tone mostly stock openers ("Good news!", "Happy to help!"), almost no jokes. |
| v3, cheer asked for | 198 | 190 | "Great pick!" 51 times (copied from the example), "Oh no" 32 times, one emoji. |
| **v3, final** | 195 | 188 | Varied openers; about 1 reply in 5 openly cheerful, plus small jokes ("Great pick for a cozy puzzle night!", "Glad that's settled!"). Same total as v2 (383 vs 384); runs vary by about ±3. |
