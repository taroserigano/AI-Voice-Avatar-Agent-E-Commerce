# 12. Xena latency: faster replies, especially with video

Taro (2026-10-02): "especially when avatar is on, response is slow, we need to improve latency."

## Where the time goes today

One spoken question with video on ("how many types of milk do you have?", the call's own
metrics, 2026-10-02):

| Step | Time | Source |
|---|---|---|
| She notices you stopped | 0.45 s of silence | `voice_end_silence_ms` |
| Final transcript | +1.19 s | `stt_ms` |
| Filler starts | +0.90 s after the transcript | `voice_filler_after_ms`, a fixed wait |
| Her face starts moving | +0.83 s (Phoenix-4.5) / **+1.12 s** (the Phoenix-4 looks with backgrounds); +1.85 s on a call's first reply | measured in plan 10, A4 |
| **First thing you hear** | **about 3.2 s after you stop** | |
| The answer's first word from the model | 2.5 s after the transcript (a product search, then the answer: two model calls) | `llm_first_token_ms` |

Without video the same turn is heard about 2.1 s after you stop. The face itself (~1.1 s) is
Tavus's rendering and can't be removed; what we control is everything before it, and hiding
it with a quick spoken acknowledgement.

## What we'll change

| # | Change | Expected gain | Risk |
|---|---|---|---|
| L1 | **Filler sooner when the face is on**: 0.3 s after the transcript instead of 0.9 s. The face's ~1.1 s means a reply is never heard sooner than that anyway, so a short "One sec" covers the wait. | First sound ~0.6 s sooner with video | A filler before a fast answer; with video that wait exists regardless |
| ~~L2~~ | ~~Warm the face up when video starts.~~ **Dropped**: the slow first reply (1.85 s) showed up in 1 of 3 runs (the other first replies were 0.83 s and 1.14 s), and a warm-up still playing when her first real reply arrives would make Tavus drop that reply. | — | — |
| ~~L3~~ | ~~Answer faster after a tool call (reasoning effort "none" on the call after a tool result).~~ **Dropped after measuring**: no faster (median first word 2.19 s vs 1.97 s, 11-12 tool questions each, interleaved). That call already spends almost nothing on reasoning. | — | — |
| L4 | **Faster default face** (decision for Taro): the Phoenix-4.5 "Rose – Business" face is ~0.3 s faster than the green-screen looks but has its own office background. Offer it as a "Fastest" look, or make it the default. | ~0.3 s per reply | Product choice |
| L5 | Speech-to-text: the final transcript takes ~1.2 s. Deepgram Flux (decision 25, needs a key) ends turns from the words themselves. | ~0.5-0.8 s per turn | Separate plan; not in this round |

Not changed: barge-in (already ~0.65 s with video), the read-back rules, and fillers without
video (0.9 s stays: without the face, fast answers shouldn't get a filler).

## How we'll know

- The live spec (`tests/e2e/specs/xana-avatar-live.spec.ts`, `TAVUS_E2E_LIVE=1`) prints first
  audio and first heard per turn, video on and off. Run it before and after.
- The voice golden eval (`eval:xana:voice`) for L3: no drop beyond run-to-run noise (±3).
- Unit tests: the filler delay follows the output (face on/off); the warm-up echo is sent
  once per room and never counts as speech; the post-tool step uses the fast setting.

## Done when

L1-L3 are in, the numbers before and after are in `IMPL.md`, and Taro has decided L4.
