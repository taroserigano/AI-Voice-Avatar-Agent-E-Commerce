# 5. Ask Steph — plan

## Goal

A shopping assistant named **Steph**, opened from a round button in the lower-right corner of
every signed-in page. It answers product questions from the real catalog ("non fat organic milk,
not regular milk", "sugar free yogurt"), checks order status, answers policy questions with
citations, finds stores, and adds items to the cart. It's built so voice can be added to the
same panel later, and so Xana (item 6) reuses the same graph.

## Architecture

```
browser ── /api/assistant/* (Next rewrite, cookie) ──► services/assistant (FastAPI, :8001)
                                                         │  resolve user: GET /v1/auth/me with the cookie (only use)
                                                         │  LangGraph: route → agent ⇄ tools → respond
                                                         │  checkpoints + conversation index in PostgreSQL
                                                         ▼
                              commerce API (:8000) with  Authorization: Bearer <service token>
                                                         X-On-Behalf-Of: <user id>
```

- **New Python package** `services/assistant` (`assistant`), in the uv workspace, own port
  (`ASSISTANT_PORT`, default 8001; this worktree 8201). `pnpm dev` starts it.
- **Identity:** the browser's cookie is used once per request to resolve the user. Tools call the
  commerce API with a shared service token plus the user ID. The commerce API accepts that
  identity only on routes marked for it, and refuses it on return confirmation (item 6) and auth.
  The model never sees a user ID, cookie, or token.
- **Graph (LangGraph 1.x):** `route` (Jev in item 3.3; a simple default until then) →
  `agent` (Claude, `claude-sonnet-5`, tools bound per route) ⇄ `tools` → end.
  Postgres checkpointer (`langgraph-checkpoint-postgres`) keyed by conversation ID.
- **Tools (typed, narrow):** `search_products` (type/tags/exclude_tags/price/text),
  `get_product_details`, `list_stores`, `add_to_cart`, `list_my_orders`, `get_order_status`,
  `search_policies`, `handoff_to_person`. Results go to the model as data, fenced as untrusted
  content, and to the browser as **cards** (product, order, store, citation).
- **Policy search:** new commerce endpoint `GET /v1/policies/search` over policy **sections**
  (OpenSearch index `policies-<env>`, built by `pnpm reindex`), plus Pinecone meaning search when
  connected, merged with RRF. `GET /v1/policies/{id}` returns a document.
- **Model without a key:** a labeled **scripted model** implements the same chat-model interface:
  it reads the request with simple rules, calls the same tools, and writes a plain answer from
  the results. It keeps the demo and integration tests working without spending tokens. The UI
  shows "Simulated assistant" when it's in use.
- **Streaming:** `POST /v1/assistant/conversations/{id}/messages` returns server-sent events:
  `status`, `text` deltas, `card`, `citation`, `done`, `error`.
- **Conversations:** `assistant_conversations` table (id, user, agent `steph`/`xana`, title,
  timestamps) — the index and ownership check; the checkpoint holds the messages. Its schema is
  created by the assistant's own Alembic history (version table `alembic_version_assistant`).
- **Limits:** max turns per conversation, max tokens per turn, tool-call cap per turn, input
  length cap.

## Web

- `components/assistant/` — `AssistantLauncher` (fixed lower-right button, "Ask Steph"),
  `ChatPanel` (dialog on mobile, floating panel on desktop; focus trap, Esc closes, returns focus),
  message list with streaming text, cards (product with add-to-cart, order, store, citation),
  suggested prompts, "new conversation", and a reserved mic slot for later voice.
- `lib/assistant-client.ts` — SSE over `fetch` (POST), typed events, abort on close.
- Mounted in the `(shop)` layout only (never on sign-in or legal pages).

## Safety

- System prompt versioned in `services/assistant/src/assistant/prompts/steph.v1.md`;
  `prompt_version` recorded on each turn.
- Tool output and product text wrapped as `<untrusted_data>`; prompt forbids following
  instructions found there; injection fixtures in tests.
- No confirm tool exists; a test asserts the tool list.
- Ownership: a conversation is only readable by its owner (404 otherwise).

## Tests

- Unit: tool schemas; tool list has no confirm; scripted model picks the right filters for the
  `product_qa.jsonl` scripts; SSE encoder; untrusted wrapping; commerce service-token
  principal (accepted on marked routes, refused elsewhere).
- Integration (commerce + assistant with the scripted model, real PostgreSQL/OpenSearch):
  a chat turn returns product cards that all match "non fat organic milk"; Bob can't read Alice's
  conversation; policy search returns cited sections.
- e2e: open Steph, ask for sugar-free yogurt, see matching cards, add one to the cart; axe.
