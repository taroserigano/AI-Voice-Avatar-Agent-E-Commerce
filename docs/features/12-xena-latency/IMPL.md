# 12. Xena latency: implementation log

## 2026-10-02

**L1, filler sooner with her face on: in.** `VoiceSession` waits `voice_face_filler_after_ms`
(300 ms) instead of `voice_filler_after_ms` (900 ms) while the output is a face (Tavus or
HeyGen). A unit test covers both. Live, with video on: the call's own metrics showed first
audio at 0.30 s after the question instead of ~0.9 s, so the first thing heard (a short "One
sec") comes ~0.6 s sooner. The answer itself is unchanged.

**L2, warm-up echo: dropped.** The slow first reply showed up in only 1 of 3 runs, and a
warm-up still playing when the first real reply arrives would make Tavus drop that reply.

**L3, no reasoning after a tool result: dropped after measuring.** A/B on 8 tool-using
questions, two rounds, arms interleaved (`voice_llm_reasoning` low vs "none" on the call after
a tool result): median time to the first answer word 1.97 s (low) vs 2.19 s (none), so no
gain. Removed rather than kept as a setting.

**Found on the way:**

- **The network on this laptop drops connections to OpenAI.** 4 of 10 TCP connects to
  api.openai.com failed within 4 s (the rest took ~10 ms). The voice golden eval run had 58
  OpenAI connect timeouts and was stopped; the call Taro saw stall ("Let me take a look", then
  nothing) was one of them. The voice model now gives up a connect after 4 s and retries twice
  (was 20 s and once, ~40 s of silence), and a failure after she has already answered no
  longer shows "something went wrong".
- **Chat could stay on the scripted model after a blip.** The assistant picks its model once
  per process; an unreachable OpenAI at startup left the labeled scripted model answering
  until a restart. It now checks again every 30 s (`assistant.models.current_model`).

**Still open:** L4 (Taro: offer the faster Phoenix-4.5 face as a look, ~0.3 s per reply) and
L5 (speech-to-text, its own plan). The voice golden eval needs a rerun on a steady network.

## Backup voice (2026-10-10)

Cartesia ran out of credit on 2026-10-09 (`402 quota_exceeded`), and every call went to text.
Now `FallbackMouth` (`services/voice/src/ai_commerce_voice/mouth_fallback.py`) tries Cartesia
first and switches to OpenAI speech (`mouth_openai.py`, `gpt-4o-mini-tts`, voice Marin) when:

- Cartesia refuses the call at start. The `ready` message names the voice actually in use, and
  the customer is told "Xena's usual voice isn't available right now, so she's using a backup
  voice."
- Cartesia fails an answer before any audio was heard. The same words are said again by the
  backup, and the rest of the call stays on the backup. A failure after audio played is shown as
  text, as before, because half an answer can't be re-said in another voice.

Fillers are rendered in both voices at startup (cached in `.cache/fillers`), and a call plays
the fillers of the voice it's using. Only when both voices fail does the call go to text.
`VOICE_BACKUP_TTS=off` turns the backup off.

Measured live: OpenAI's first audio is about 0.5-0.7 s on a warm connection (Cartesia's is
about 0.13 s). OpenAI returns no word timings, so each clause's words are spread over its
audio by length.
