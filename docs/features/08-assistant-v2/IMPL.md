# 8. Assistant v2 — implementation

Status: **P3 retrieval package, P4 planner service, and the P0/P1 streaming package are done**
(2026-09-26). Wiring them into `services/assistant` (P0-P2) and the commerce side of P3/P4
wait for the catalog-stores commit.

## Tasks

P3 retrieval: `packages/retrieval` (`ai_commerce_retrieval`), a new uv workspace member
- [x] `config.py`: `QDRANT_URL` (default is the local server), `QDRANT_API_KEY`, which is sent only over https, and `OPEN_AI_API` / `OPENAI_API_KEY`, `RETRIEVAL_EMBED_MODEL`, `SEARCH_ENV`, `SEMANTIC_TIMEOUT_MS`
- [x] `records.py`: `Record(id, text, metadata)`
  - The content hash covers both text and metadata.
  - Point IDs are UUIDv5 values derived from the record ID, since Qdrant needs UUIDs.
  - Only the text is embedded; metadata is excluded from the embed input.
  - The `record_id` and `content_hash` keys are reserved.
- [x] `qdrant_collections.py`: collections are named `aic-<corpus>-<env>`.
  - Each carries `metadata.owner = "ai-commerce"` plus its embedding model and dimensions.
  - The app refuses collections it didn't create, and refuses to mix embedding models.
  - Deleting is limited to its own collections.
- [x] `index.py`: `VectorIndex`
  - Writes go through LlamaIndex `IngestionPipeline` into `QdrantVectorStore`.
  - `sync()` is incremental by hash: it embeds only changed records and deletes removed ones.
  - `clear()` rebuilds the collection; `search()` supports metadata filters and returns app record IDs and metadata.
- [x] `hybrid.py`: `HybridRetriever(BaseRetriever)`
  - The keyword and vector legs run in parallel and are merged by RRF.
  - The vector leg has a time budget. If it's off, times out or fails, the keyword results still answer, and `last_legs` records why.
- [x] `fusion.py`: the same RRF as `commerce.search.rrf`, checked by a parity test
- [x] `embeddings.py` / `factory.py`: the OpenAI embedder is always passed explicitly, never taken from LlamaIndex's global `Settings`
- [x] `pnpm local:up` now also runs native Qdrant 1.19.1 (localhost, no key, telemetry off, data in `%LOCALAPPDATA%\ai-commerce\qdrant-storage`)
- [x] Scripts: `pnpm test:retrieval`, added to `pnpm test`; the package is added to `pnpm typecheck`
- [x] Tests: 31 in total.
  - Unit tests cover fusion (including commerce parity), records, hybrid fallbacks, settings, and a boundary check: no test fakes, no other vector store, no `VectorStoreIndex.from_documents`.
  - Integration tests run on real Qdrant:
    - incremental sync
    - meaning ranking
    - policy filters (drafts and future versions excluded)
    - the ownership guard
    - the embedding-mix guard
    - rebuild
    - no fallback to LlamaIndex globals
    - hybrid with real Qdrant
  - One live OpenAI test is opt-in with `RETRIEVAL_LIVE_EMBED=1`.
- [x] `AGENTS.md` and `.env.example` now say Qdrant
- [x] Qdrant Cloud connected (cluster in AWS us-east-2, server 1.19.1)
  - `QDRANT_CLUSTER` is accepted as `QDRANT_URL`.
  - The whole integration suite, including the live OpenAI test, passes against it with `RETRIEVAL_TEST_QDRANT_URL` and `RETRIEVAL_TEST_QDRANT_API_KEY` set.
- [x] Strict mode: Cloud refuses filters on unindexed fields.
  - Every collection is now created in strict mode, locally too, and indexes the fields its corpus filters on (`CORPUS_FILTERS`).
  - Reopening a collection adds indexes that were declared later.
  - Tests cover both behaviors.

P0/P1 streaming: `packages/assistant-stream` (`ai_commerce_stream`), a new uv workspace member
- [x] `events.py`: typed v2 events.
  - Types: `turn.start`, `signals`, `agent.handoff`, `plan`, `tool.start`, `tool.progress`, `tool.end`, `text.delta`, `card`, `quote`, `ask`, `citations`, `done`, `error`, `resumed`.
  - Every event carries `v`, `turn_id`, `agent` and `ts`.
  - The JSON schema is exported for `packages/contracts`.
- [x] `sse.py`: v2 encoding with `id:` and a `: ping` heartbeat.
  - `to_v1` / `encode_v1` produce **exactly** the bytes of today's `turns.sse()`, checked by a golden test.
  - Clients opt in with `X-Assistant-Stream: 2`.
- [x] `store.py`: `assistant_turns` and `assistant_turn_events` in PostgreSQL.
  - A partial unique index allows only one running turn per conversation.
  - Turns left running by a dead process are reaped after 10 minutes.
  - Finished turns are purged after 30 days.
- [x] `runner.py`: `TurnRunner`.
  - Turns run in a worker thread, detached from the HTTP connection.
  - `follow()` replays events after `Last-Event-ID` (a `resumed` event comes first), then tails live ones with heartbeats. A follower in another process polls the store.
  - A second turn on the same conversation gets `TurnInProgress` (409, with the running turn's ID).
  - `cancel()` ends the turn with `done(status="canceled")`, and failures end it with a generic `error`.
  - Another customer gets `TurnNotFound`.
- [x] `responses.py`: `sse_response()` (Starlette `StreamingResponse` with no-store and no-buffering headers)
- [x] Tests: 14 against real PostgreSQL.
  - Resuming continues exactly where the client left off, and a disconnect doesn't stop the turn.
  - One running turn per conversation, cross-customer isolation, cancel, failure, stale reaping, heartbeats, the v1 view, purge, and the v1 golden bytes.
- [x] `ai_commerce_planner.stream_bridge`: `planner_producer()` turns a planner run into a turn.
  - It streams `plan`, `tool.*`, a basket `card`, `text.delta` and `done`.
  - `reverify_basket()` re-checks the planner's basket with the gateway's own catalog view, so tampered prices and injected items are fixed or dropped.
  - Tested end to end over both transports through PostgreSQL.
- [ ] Alembic: the assistant's migration history creates these two tables (after the merge)

P4 shopping planner: `services/planner` (`ai_commerce_planner`), a new uv workspace member
- [x] `constraints.py`: code parses budget, allergens, required tags and servings from the goal.
  - The rules are bound into the tools, so the model can tighten them but never loosen them.
  - "Peanut allergy" rules out peanuts only; "nut-free" rules out peanuts and tree nuts.
- [x] `catalog.py`: `CatalogPort`, plus `CommerceCatalog`, which reads `/v1/products` and `/v1/products/{id}` using the planner's own identity (service token + `X-On-Behalf-Of`).
- [x] `basket.py`: `check_basket` re-reads every line from the catalog.
  - Lines are dropped, with a reason, for a banned allergen, missing label data, a missing required tag, out of stock, or too little stock.
  - Totals come only from catalog prices, and the budget is checked on the subtotal.
  - The $5.99 / free-from-$35 shipping figure is only an estimate.
- [x] `tools.py`: `search_products`, `check_basket` and `propose_basket`.
  - Search results are pre-filtered by the shopper's rules.
  - Every result is wrapped in `<untrusted_data>`.
  - There's no cart, order, return, payment or handoff tool, and no identity argument.
- [x] `agent.py`: `create_deep_agent` with:
  - `TodoListMiddleware`, plus model and tool call limits (12 and 40)
  - `StateBackend` scratch files
  - a read-only `general-purpose` helper that replaces the default one
  - `PlannerState.basket`
- [x] `scripted.py`: a labeled `ScriptedPlannerModel` that drives the same graph without a key (plan, search, check, trim to budget, propose)
- [x] `runner.py` / `events.py`: graph stream → `plan`, `tool.start`, `tool.end`, `basket`, `text` and `done` events, with a 90 s budget, `stop` for cancel, and helper steps kept internal
- [x] `delegation.py`: gateway delegation JWTs (HS256)
  - Claims: aud `shopping-planner`, iss `assistant-gateway`, a scope, and a `jti` that works only once.
  - Lifetime is at most 5 minutes.
  - The token rides in the HTTP header only.
- [x] `a2a_server.py`: an A2A 1.0 server built on `a2a-sdk` 1.1.5 (JSON-RPC, streaming, no push)
  - Every route except `/healthz` needs a delegation token, including the Agent Card.
  - Tasks are owned by the customer, so another customer gets `TaskNotFoundError`.
  - It binds to localhost (`pnpm dev:planner`, :8302).
- [x] `port.py`: `PlannerPort` with `InProcessPlanner` and `A2APlanner`.
  - `A2APlanner` signs a fresh token on each HTTP request and streams through a queue for the assistant's worker thread.
  - Both adapters yield the same events.
- [x] Tests: 30, plus 1 opt-in live test.
  - Parsing, the basket rules, and the tool surface (no `execute`, no forbidden tools, no identity arguments).
  - A scripted end-to-end run whose basket obeys every rule.
  - A **hostile-model test**: the model proposes an injected peanut product and an item that doesn't exist, and code drops both.
  - Untrusted wrapping, and delegation (9 kinds of bad token, plus replay).
  - A2A: 401s, the same events as the in-process run, and cross-customer task isolation.
- [x] Live run on `gpt-5.5` (`PLANNER_LIVE_MODEL=1`): it planned with todos and proposed a nut-free basket under $30 that code accepted, in 37 s.

- [x] Planner eval (`pnpm eval:planner`, `evals/planner_eval.py`, 12 scenarios in `evals/assistant/planner.jsonl`).
  - It runs on the **real 2,358-product seed catalog** held in memory.
  - Hard gates (plain code): rules, budget, totals, tools, and honesty (no basket when the goal can't be met).
  - Quality: coverage, compared with `evals/baselines/planner-scripted.json`.
  - Scripted baseline: every hard gate passes; coverage is 92%, because it finds no kosher items for its dinner slots.
  - `--provider openai` scores the real model.

Next in P4 (needs catalog-stores merged)
- [ ] Commerce: a `PLANNER_ROUTES` allowlist for `PLANNER_SERVICE_TOKEN` (catalog reads only), `POST /v1/cart/estimate`, and `POST /v1/cart/items:bulk` with an `Idempotency-Key` and expected prices (409 if stale)
- [ ] Assistant: route `plan_shopping` to `PlannerPort`, re-emit the planner events as SSE v2, and rebuild the basket card from commerce data before it's sent
- [ ] A2A task store in PostgreSQL (`DatabaseTaskStore`) once async PostgreSQL works on Windows' event loop; `InMemoryTaskStore` for now, since tasks are short and the assistant stores the events
- [ ] Web: `PlanCard`, `BasketCard`, `AllergenLine`, workspace mode

Next in P3
- [ ] Commerce product search: replace `commerce/search/semantic.py` (Pinecone) with `ai_commerce_retrieval`, reuse `fusion.py`, update `test_no_other_vector_store_in_app_code`, and have `pnpm reindex` sync Qdrant
- [ ] Policy search: once catalog-stores lands, move `commerce/policies/search.py` to records with `cite`, `version`, `effective_from` and `status`
- [ ] Search eval: add synonym cases (see the log), then compare hybrid with and without the vector leg
- [ ] Optional reranker experiment, off by default

## Log

- The live OpenAI run passed ("yoghurt without sugar" found the sugar-free yogurt; "a dairy
  drink" found milk). "Skim milk" ranked whole milk above fat free milk with
  `text-embedding-3-small`. The keyword leg and tags must cover synonyms like that, so add
  them to the search eval.
- The first run against Qdrant Cloud failed on the policy filter: "Index required but not found
  for effective_from". Cloud collections are strict, while the local server's default isn't.
  That's why collections are now strict everywhere.
- The old 91-character key (now `QDRANT` in the main .env) gets 403 on the cluster. `QDRANT_API_KEY` works.
- The worktree has its own gitignored `.env`, with the two keys copied from the main
  checkout, `SEARCH_ENV=assistant-v2`, and the :8300-range ports. It points at Qdrant Cloud, while tests default to the local Qdrant.
- deepagents 0.7.19 registers `execute` even with `StateBackend`, and only hides it from the
  model at runtime. The tool-surface test caught it, so the planner now passes its own
  `FilesystemMiddleware(tools=[...])`, which replaces the default by name.
- A2A 1.0 in `a2a-sdk` 1.1.5: task ownership comes from `request.user.display_name`, which is
  set to the customer ID, so other customers' tasks are simply "not found".
- The planner eval caught the scripted planner meeting "a week of dinners for 6 under $5" by
  cutting quantities to $4.95. It now swaps pricier options for cheaper ones but never cuts
  what the plan needs, and says how far over the cheapest full basket is.
