# Xena: live demos (15 and 30 seconds)

Two real recordings of the voice screen on the local stack (http://localhost:3100/support/voice),
signed in as the seeded customer Alice. Nothing is mocked: the question goes to Xena's voice
service, she reads Alice's orders, and she answers in her own voice (Cartesia Skylar).

| File | What it shows |
|---|---|
| `xena-voice-15s.mp4` | Voice only: the orb, live captions, and the conversation panel |
| `xena-avatar-15s.mp4` | The same question with Video on: Xena's Tavus face speaks the answer |
| `xena-voice-30s.mp4` | Three questions, voice only: when the yoga mat arrives (her orders), can I return a gift card (return policy), do you ship to Canada (shipping policy) |
| `xena-avatar-33s.mp4` | The same three questions with the Tavus face. 33 s: each answer with video takes about a second longer, and the Tavus account ran out of credit (HTTP 402) before a take fit in 30 s |

In the 30-second cuts, only the customer's pause before the next question is shortened (to
0.3 s, `cut_turns.py`); Xena's response time after every question is as recorded.

The customer's question ("Hi Xena, when is my yoga mat arriving?") is a Cartesia voice (Cathy),
fed to the page as its microphone (`question.wav`). Answers come from the live model, so each
take words them a little differently.

To record again (stack running, `pnpm db:seed` first; the avatar take uses about a minute of
Tavus time):

```
node record.mjs voice      # or: node record.mjs avatar
python cut.py voice        # muxes and cuts 15 s around the conversation -> out/<mode>/

node record.mjs voice q1c.wav,q2e.wav,q3b.wav voice30   # several questions, one after another
python cut_turns.py voice30 30
```

`record.mjs` captures the screen with timestamped CDP screencast frames and the page's own audio
(Xena's playback, the avatar's WebRTC audio, and the question), so sound and picture line up.
Open the app at `localhost`, not `127.0.0.1`: Next.js blocks its dev scripts for other origins
and the page never becomes interactive.
