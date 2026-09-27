# Feature batch: policy, Steph, Jev, Xana, maturity (requested 2026-09-26)

Taro's request, numbered as he gave it:

| # | Feature | Status | Plan | Implementation log |
|---|---|---|---|---|
| 7 | Detailed return and refund policy plus "regulations", on a dedicated page | Done | [PLAN](07-returns-policy/PLAN.md) | [IMPL](07-returns-policy/IMPL.md) |
| 5 | "Ask Steph": a chat assistant behind a lower-right button (voice later) | Done | [PLAN](05-ask-steph/PLAN.md) | [IMPL](05-ask-steph/IMPL.md) |
| 3.3 | Jev (TypeSafe) in the assistant, especially for returns and refunds | Done (simulator until a key is set) | [PLAN](03.3-jev/PLAN.md) | [IMPL](03.3-jev/IMPL.md) |
| 6 | A Support tab where customers talk by voice with Xana about returns and refunds | Done (turn-based voice) | [PLAN](06-xana-voice-support/PLAN.md) | [IMPL](06-xana-voice-support/IMPL.md) |
| 4 | A more mature, in-depth site: critique, investigator, and eval agents, then improve | Done (3.55 → 4.38) | [PLAN](04-site-maturity/PLAN.md) | [IMPL](04-site-maturity/IMPL.md) |

## Build order: 7 → 5 → 3.3 → 6 → 4

- **7 first.** Steph, Jev's return triage, and Xana all cite the policy; its section IDs are the
  citation targets. It touches only `content/policies/` and one new public page.
- **5 next.** It creates `services/assistant` (LangGraph + Claude), the chat UI, the tool
  boundary, and policy search. Item 6 reuses all of it.
- **3.3 then.** Jev plugs into the assistant graph as the router and return-triage signal
  source. It needs the graph from item 5 and makes item 6 better.
- **6 after 5, as asked.** It needs the returns engine (eligibility, return records) that the
  parallel agent is finishing on branch `design-ratings-sitemap`. Quote and confirm
  endpoints are built here, on that engine, after that branch is committed and merged.
- **4 last.** It reworks the whole site, which overlaps the other agent's redesign. Doing it on
  the merged branch avoids conflicts, and the critique agents review the new features too.

## Decisions this batch makes (recorded in HANDOFF.md)

| Topic | Decision | Why |
|---|---|---|
| Jev | **Used**, not only an experiment: intent routing, return-reason and item disambiguation, escalation signals, and a second vote on voice "yes". Behind `JEV_ENABLED`; a labeled local simulator when `TYPESAFE_API_KEY` is missing. | Taro, 2026-09-26: "we will use Jev AI, especially for return refund feature." Jev never decides eligibility or amounts, which always come from the commerce API. |
| Assistant identity | The assistant calls the commerce API with a **service token plus the signed-in user's ID**, never the user's cookie. The commerce API refuses that service identity on return confirmation. | "Inject identity on the server"; the model's side of the system can't confirm a return even by mistake. |
| Policy search | OpenSearch keyword search over policy **sections**, merged with Pinecone meaning search when Pinecone is connected (same design as product search). | Pinecone stays the only vector store; the policy set is small enough for keyword search to work until the index slot is free. |
| Voice transport | Turn-based voice over HTTP (browser voice detection → speech-to-text → same graph → speech) until LiveKit keys exist. STT: Deepgram if keyed, else Groq Whisper (keyed), else the browser. TTS: Cartesia (keyed), else the browser. The LiveKit worker from the plan's Step 6 stays the target. | There are no LiveKit or Deepgram keys; Cartesia and Groq keys work today. |
| Returns policy page | `/returns-policy` is **public**, like terms and privacy. | A return policy is a legal disclosure that must be readable before buying (for example California Civil Code §1723). |

## Keys found on 2026-09-26

| Key | State |
|---|---|
| `ANTHROPIC_API_KEY` | **Invalid** (401). Steph and Xana run on the labeled scripted model until a valid key is set. |
| `CARTESIA_SONIC_API_KEY` | Works. |
| `GROQ_API_KEY` | Works (`whisper-large-v3-turbo`). |
| `TYPESAFE_API_KEY` | Not set. Jev runs as the labeled simulator. |
| LiveKit, Deepgram | Not set. |
