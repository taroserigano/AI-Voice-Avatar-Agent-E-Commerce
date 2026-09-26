# 8. Assistant v2 — plan

Full plan with diagrams: https://claude.ai/artifact/BusvSUF2bi8UHUVBWXY1eK (private to Taro).
It came from three parallel agent reports (architect, UX designer, stack researcher), 2026-09-26.

## Goal

Turn Steph and Xana into a supervised multi-agent chat service:

- **SSE v2 streaming** that survives reconnects.
- **A LangGraph supervisor** with Steph → Xana handoff inside the conversation.
- **A deep-agent shopping planner** behind an internal A2A boundary. It handles tasks like
  meal plans under a budget, allergen-aware baskets and "restock my usual".
- **Hybrid retrieval**, using LlamaIndex ingestion into Qdrant.

Money, eligibility and confirmation stay in code.

## Decisions (Taro, 2026-09-26)

| # | Decision |
|---|---|
| 22 | The assistant LLM is **OpenAI**; the Anthropic key is rejected. `gpt-5.5` and `gpt-5.4-mini` both passed a strict tool-call check. Provider switch: `openai` \| `anthropic` \| `scripted`, with the model set per role and chosen by evals. |
| 23 | **Qdrant replaces Pinecone** as the only vector store. No Pinecone index is deleted. Embeddings come from OpenAI `text-embedding-3-small`, for product and policy text only. Locally, a native Qdrant binary runs via `pnpm local:up`; there are no containers. |
| v2-1 | The planner runs in-process first, behind `PlannerPort`. `PLANNER_TRANSPORT=a2a` is switched on only after evals show it earns its place. |
| v2-2 | A2A stays internal only. The Agent Card requires a service token, and there are no push notifications. |
| v2-3 | Stated allergies may go to the model and live in checkpoints, but never in traces. Baskets say "no listed allergens per label data, check the package" and never say "safe". Allergen checks come from PostgreSQL fields. |
| v2-5 | Planner caps: 40 tool calls, 12 model calls, 90 s, plus a token and USD budget. |
| v2-6 | `assistant_turn_events` are kept for 30 days. The web moves to v2 events in P1, and the v1 translator is deleted at the end of P2. |

## Phases

| Phase | Scope | Status |
|---|---|---|
| P0 | SSE v2 contract (native `fastapi.sse`, `id:` on every event, v1 translator, golden test) | Waiting for the catalog-stores commit |
| P1 | TurnRunner: events stored in PostgreSQL, resume via Last-Event-ID, 409 on a concurrent turn, cancel; web reconnect | — |
| P2 | Supervisor and handoff (`graph_version` per conversation); provider switch to OpenAI | — |
| P3 | Retrieval: **`packages/retrieval` (started)**; move commerce product and policy search from Pinecone to it | In progress |
| P4 | `deepagents` planner (in-process, then A2A), `POST /v1/cart/estimate`, bulk add with `Idempotency-Key` | — |
| P5 | Evals (Ragas 0.4 `ascore()`), red-team scripts, CI gates, dashboards | — |

## Where

- **Branch:** `assistant-v2`, in worktree `.claude/worktrees/assistant-v2`, cut from `2f66018`.
- **Local setup:** databases `commerce_assistant` and `commerce_assistant_test`; `SEARCH_ENV=assistant-v2`; ports :8300 (API), :8301 (assistant), :8302 (planner) and :3300 (web).
- **Merge order:** the existing assistant (Steph, Jev, Xana) is still uncommitted in `catalog-stores`, owned by session ai-commerce-8a. P0 starts from its commit, once Taro OKs it there.
