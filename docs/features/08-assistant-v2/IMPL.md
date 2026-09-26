# 8. Assistant v2 — implementation

Status: **P3 retrieval package done** (2026-09-26). P0 waits for the catalog-stores commit.

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
