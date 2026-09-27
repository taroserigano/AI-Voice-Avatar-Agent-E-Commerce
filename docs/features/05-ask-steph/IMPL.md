# 5. Ask Steph — implementation

Status: **done** (2026-09-26) — text chat. Voice lands in the same panel after item 6.

## Tasks

Commerce API
- [x] Service identity: `ASSISTANT_SERVICE_TOKEN`; `require_user` accepts `Authorization: Bearer` + `X-On-Behalf-Of` only on `ASSISTANT_ROUTES`; `require_browser_user` refuses it; the dev default token is refused outside dev (`test_assistant_identity.py`)
- [x] `GET /v1/catalog/vocabulary`: every product type and tag, for the tool schema and the scripted model
- [x] Policy sections: `commerce/policies/search.py` — OpenSearch `policies-<env>` loads itself and reloads when the files change (content hash); Pinecone namespace `policies-<env>` via `pnpm reindex` when connected; RRF merge; `GET /v1/policies/search`, `GET /v1/policies/{id}` (`test_policies_api.py`)
- [x] Seed: retired scenario keys are deleted on reseed (`RETIRED_ORDER_KEYS`), so a renamed scenario doesn't leave a duplicate order

Assistant service (`services/assistant`)
- [x] Package in the uv workspace; settings; FastAPI app; `/healthz`; `pnpm dev` process (`ASSISTANT_PORT`, default 8001); `pnpm db:migrate` runs `assistant-migrate`
- [x] Alembic history (`alembic_version_assistant`) with `assistant_conversations`; LangGraph Postgres checkpointer (sync, so it works on Windows' event loop)
- [x] Commerce client (service identity); customer resolved from the cookie once per request
- [x] Tools: search_products, get_product_details, add_to_cart, list_my_orders, get_order_status, list_stores, search_policies, handoff_to_person; output wrapped in `<untrusted_data>`; cards from tool results
- [x] Graph: route → agent ⇄ tools; tool-call cap per turn; history window that never splits a tool call from its result; cached system prompt
- [x] Models: Claude (`langchain-anthropic`, key checked at startup) or the labeled scripted model
- [x] Routes: status, create/list/get conversation, post message (SSE: status, text, card, citations, done, error); 404 for someone else's conversation
- [x] Citations: `[[cite:doc#section]]` markers are valid only if that turn's `search_policies` returned the section
- [x] Prompt `prompts/steph.v1.md`; `prompt_version` in run metadata
- [x] Tests: 16 unit (tool list has no confirm/pay/refund and no identity arguments, untrusted wrapping, scripted parsing incl. the eval scripts' filters, routing, citation checking, history) + 3 integration (streamed turn with cards and citations, Bob can't read Alice's conversation, sign-in required)

Web
- [x] Rewrite `/api/assistant/*` → assistant service (before the commerce rewrite)
- [x] `lib/assistant-client.ts` (SSE parser), `lib/assistant-text.ts` (citations → numbered sources, lists), `lib/use-assistant.ts` (conversation hook, cart refresh, race-safe history load) + tests
- [x] `components/assistant/`: launcher, panel (dialog; focus into input, Esc closes and returns focus; full screen on phones), thread shared with Xana, cards (product with Add, order, store, cart, handoff), sources, suggestions, screen-reader announcement of finished answers, "Simulated" badge with reason, disabled mic reserved for voice
- [x] Mounted in the `(shop)` layout
- [x] e2e `ask-steph.spec.ts`: sugar-free yogurt → every card is a sugar-free yogurt → Add → header cart updates; cited policy answer links to `/returns-policy#rr-2-1`; Esc and focus return; conversation survives reload; axe on the panel

Docs
- [x] README, HANDOFF decisions 18–21, `.env.example`

## Log

- The Anthropic key in the shared `.env` is rejected (401), so everything was verified with the
  scripted model. With a working key the same graph runs on Claude with no code change.
- Merged the other agent's branch (`design-ratings-sitemap`, fast-forward) mid-way, since Xana
  builds on its returns engine; took its redesigned layouts and re-added the policy links there
  (legal sidebar, footer, sign-in legal nav, sitemap, "How returns work", product-page return
  summary).
- Found and fixed: "no sugar added" read as sugar-free (test from the eval scripts); a history
  load finishing after "New conversation" overwrote the new messages (e2e); requested tags
  now come first on product cards.
- Home page hero still says the assistant is "coming next" (the other agent's copy): fix in
  item 4.
