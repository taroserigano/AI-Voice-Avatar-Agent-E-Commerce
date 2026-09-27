# Handoff — AI Commerce Build

**Written:** 2026-09-25, on Taro's Mac, at the end of a planning session.

**Read this first** if you are continuing on another machine (for example, the Windows laptop). Claude's memory notes from the Mac do **not** move with the files, so every decision is written here.

---

## Where things stand

| Item | Status |
|---|---|
| Review of the original handoff package (8 docs) | ✅ Done |
| Research: fact check of all 22 sources, best practices, OTel and Ragas facts | ✅ Done. Results are built into the plan. |
| Build plan | ✅ Done: `docs/PLAN_ai-commerce-build.md` |
| Step 0: project folder, docs unzipped, `CLAUDE.md`, `.gitignore`, `.gitattributes` | ✅ Done |
| GitHub repo | ✅ 2026-09-26: **private** `https://github.com/taroserigano/ai-commerce` is `origin`; push here. (The first commits also went to an older public repo, `taroserigano777/ai-commerce`, which is no longer used.) |
| Step 1: fix the handoff docs | ✅ Done (2026-09-25, Windows laptop) |
| Step 2: Milestone 1 (sign-in and shopping foundation) | ✅ Built and tested locally (2026-09-25). Pinecone semantic search is waiting on a free index slot; see Open items. |
| Steps 3–8: build | ⬜ Not started |
| Application code | ✅ Milestone 1: see README.md |

---

## What's in this folder

```
ai-commerce/
├── HANDOFF.md                     ← this file
├── CLAUDE.md                      ← one line: @docs/handoff/AGENTS.md
├── .gitignore                     ← ignores .env, node_modules, .venv, etc.
├── .gitattributes                 ← forces Linux (LF) line endings
└── docs/
    ├── PLAN_ai-commerce-build.md  ← THE plan (steps 0–8, about 40 days)
    └── handoff/                   ← the 8 docs, updated in Step 1 to match the plan
        ├── README.md
        ├── MASTER_PROMPT.md
        ├── AGENTS.md
        ├── PRODUCT_REQUIREMENTS.md
        ├── TECHNICAL_SPEC.md
        ├── IMPLEMENTATION_PLAN.md
        ├── ACCEPTANCE_AND_EVALS.md
        └── ecommerce-architecture-plan.md
```

**Important:** where the plan and `docs/handoff/` disagree, **the plan wins**. Step 1 exists to update the handoff docs to match it.

---

## All decisions made (these override the original handoff)

| # | Topic | Decision |
|---|---|---|
| 1 | Vector database | **Pinecone only, no exceptions.** It holds both policy/help text and product "meaning" vectors. No pgvector, and no OpenSearch vectors. |
| 2 | Pinecone in development | A **real Pinecone account**, even locally. Each developer and environment gets its own namespace. |
| 3 | Pinecone in tests | Pure unit tests only may use a small stand-in, kept in `tests/unit/`. The app, integration tests, evals, and the demo always use real Pinecone. |
| 4 | Product search | OpenSearch handles keywords and filters. Pinecone handles meaning. The results are merged with reciprocal rank fusion (a standard way to combine two ranked lists). Price and stock always come from PostgreSQL. |
| 5 | Sales tax | **Stripe Tax**, inside Stripe Checkout Sessions. Our server does not calculate tax. |
| 6 | treg | **Dropped entirely.** Its data is other retailers' listings, including Walmart's and Amazon's. |
| 7 | Monitoring | **OpenTelemetry everywhere**, built from Milestone 1. |
| 8 | Evals | A strong 7-layer eval system that includes **Ragas**. Safety checks use plain code and block merges in CI. |
| 9 | Sign-in | **Sign-in comes first.** The sign-in screen is the first thing built. Every visitor must sign in before using any part of the site. |
| 10 | Guests | **No guest access at all**: no guest browsing, cart, or checkout. |
| 11 | Temporal | **Used in Milestone 2** for the checkout workflow, and in Milestone 3 for returns. |
| 12 | AWS | **Taro's personal AWS account only, never RealPage's.** Use a CLI profile named `personal`, and pin Terraform with `allowed_account_ids`. |
| 13 | Sign-in mechanism | **Extremely simple: check the email and password only, no additional layer.** No rate limiting, CAPTCHA, password reset, or Cognito/OIDC. The session cookie and the sign-in wall stay. Decided 2026-09-25. |
| 14 | Catalog size and detail | **A large catalog (about 2,000 products)** with enough detail for LLM product Q&A ("non fat organic milk, not regular milk", "sugar free yogurt"): product type, controlled diet/feature tags, nutrition facts, ingredients, allergens, specs. Plus scripted Q&A and return/refund conversations for the assistant evals. Decided 2026-09-26. |
| 15 | Stores | **10 Larkspur stores around Dallas, shown on a Google map.** Store locator only: online orders still ship from one warehouse and there's no store pickup. Decided 2026-09-26. |
| 16 | Local services | **No containers needed:** `pnpm local:up` runs PostgreSQL and OpenSearch natively. The app reads `COMMERCE_DATABASE_URL`, never the shared `.env`'s `DATABASE_URL` (another project's database). Decided 2026-09-26. |

| 17 | Sandbox policy additions | **Accepted by Taro (2026-09-26):** a *perishable* return class (fresh and frozen food isn't sent back; spoiled or damaged items reported within 7 days of delivery are refunded without a return), a store return drop-off counts as the carrier scan, and shipping is $5.99, free at $35 after discounts. In the sandbox policy table in `docs/handoff/PRODUCT_REQUIREMENTS.md` and in `content/policies/`. |
| 18 | Assistants | **Steph** (shopping, a chat button on every shop page, voice later) and **Xana** (customer support, voice-first `/support` page for returns and refunds) share one LangGraph in `services/assistant`. Requested by Taro 2026-09-26; plans in `docs/features/`. |
| 19 | Jev | **Used, not just an experiment** (Taro, 2026-09-26: "we will use Jev AI, especially for return refund feature"): intent routing, return reason and item disambiguation, escalation signals, and a second vote on spoken "yes". Behind `JEV_ENABLED`, with a labeled simulator when `TYPESAFE_API_KEY` is missing. Jev never decides eligibility or amounts. |
| 20 | Assistant identity | The assistant calls the commerce API with a **service token plus the signed-in customer's ID** on an allowlist of routes (`commerce.auth.deps.ASSISTANT_ROUTES`), never with the customer's cookie; return confirmation refuses that identity. |
| 21 | Return policy page | `/returns-policy` is **public** like terms and privacy (a refund policy must be readable before buying). It renders `content/policies/returns-and-refunds.md` and `returns-regulations.md`, whose section IDs (`rr-7-3`) are what the assistants cite. |
| 22 | Voice transport (interim) | Turn-based voice over HTTP until LiveKit keys exist: the browser detects the end of speech, uploads the clip (never stored), the server transcribes it (Deepgram, else Groq Whisper, else the browser), and Cartesia `sonic-3.6-2026-08-27` speaks the answer. The LiveKit worker in the plan's Step 6 stays the target. Decided 2026-09-26 (no LiveKit or Deepgram key; Groq and Cartesia keys work). |
| 23 | Refunds before Stripe | Return confirmation is real (quote hash, single-use token, idempotency, one return per quote); refunds are **simulated** until Milestone 2 connects Stripe, with the same records and states. Perishables refund at confirmation; other items at the development-only carrier scan, warehouse receipt, or inspection. |

**Defaults Taro accepted** (from the plan): Stripe Checkout Sessions with cards only; refunds go only to the original card; WCAG 2.2 AA; Jev as an optional flagged experiment; the sandbox return policy in Step 1.

---

## Open items

1. **Git email for commits.** This repo uses the GitHub no-reply address `275150514+taroserigano777@users.noreply.github.com`, set for this repo only, so the work email stays out of a personal repo. **Set it again after cloning on Windows**, because repo settings don't travel with `git clone`:

   ```bash
   git config user.email "275150514+taroserigano777@users.noreply.github.com"
   git config user.name  "taroserigano777"
   ```

   To use a different email, just set a different value.

2. **Pinecone index slot.** The Pinecone project is at its 5-index limit and none of the existing indexes uses hosted embeddings. Decision (2026-09-25): free one slot (delete an old index or upgrade), then set `PINECONE_INDEX_NAME=ai-commerce` in `.env` and run `pnpm reindex`; the app creates its own index. Until then search is keyword-only and says so. The app refuses to write to any index it didn't create.

3. **Personal AWS account ID** (12 digits). It is needed for Terraform's `allowed_account_ids`, but only in Step 7.

4. **Accounts and keys** to get before the steps that need them:
   - Stripe test mode, plus the Stripe CLI, and Stripe Tax with a test state registration.
   - Pinecone.
   - An LLM key (start with Claude Sonnet 5).
   - LiveKit, Deepgram, and Cartesia (Step 6).
   - Personal AWS (Step 7).

---

## Moving to the Windows laptop

The repo is on GitHub (public, personal account). On Windows, inside WSL:

```bash
gh auth login        # sign in as taroserigano777
gh repo clone taroserigano777/ai-commerce ~/ai-commerce
cd ~/ai-commerce
git config user.email "275150514+taroserigano777@users.noreply.github.com"
git config user.name  "taroserigano777"
```

### Windows setup (recommended)

| What | Why |
|---|---|
| **WSL2 with Ubuntu** | The stack (Docker, Python, Node, Temporal, shell scripts) runs much more smoothly on Linux. |
| Keep the repo **inside WSL** (for example `~/ai-commerce`), **not** under `C:\` or `/mnt/c/...` | Files under `/mnt/c` are slow for Docker and Node, and file watching is unreliable there. |
| **Docker Desktop** with the WSL2 backend turned on | Runs PostgreSQL, Redis, OpenSearch, the Temporal dev server, and the OTel/Grafana stack. |
| Give Docker at least 8 GB of RAM (16 GB is better) | OpenSearch alone needs about 2 GB or more. |
| Inside WSL, install Git, Node LTS with pnpm, Python 3.12 or newer with `uv`, the Stripe CLI, and later the AWS CLI | These are the build tools. |
| Line endings: the repo already has a `.gitattributes` with `* text=auto eol=lf`. Also run `git config --global core.autocrlf input` in WSL. | Stops Windows line endings from breaking shell scripts and Docker builds. |
| Install Claude Code inside WSL, and open the repo from there (or through VS Code's WSL extension) | Claude then sees the same Linux paths as the build. |

---

## Milestone 1 build notes (2026-09-25, Windows laptop)

Built natively on Windows (Git Bash/PowerShell, Docker Desktop), not inside WSL; everything ran fine from `C:\...`. Choices made while building, beyond the plan:

| Topic | Choice | Why |
|---|---|---|
| Outbox worker location | `services/commerce/src/commerce/outbox/`, run with `pnpm dev:outbox` | It shares the commerce models and database; a separate `workers/outbox` package would duplicate them. |
| SQLAlchemy | Pinned to 2.0.54, not 2.1 | The OTel SQLAlchemy instrumentation supports < 2.1; with 2.1 there were no database spans. |
| FastAPI route guard | Walks nested routers and cross-checks against the OpenAPI schema | FastAPI 0.141 no longer flattens included routers, so a naive check passed vacuously. |
| Sessions | Server-side sessions in PostgreSQL; the cookie holds a random token, only its SHA-256 is stored | Sign-out and password reset can end sessions immediately. |
| Back after sign-out | Inline script re-checks the session on back/forward loads | Next's dev server sends `no-cache` (not `no-store`), so Back could show a private page. Production sends `no-store`; the guard covers both. |
| Search latency | Pinecone gets a 250 ms budget (`SEMANTIC_TIMEOUT_MS`); after that, keyword results are returned | Keeps search p95 under the 300 ms target when Pinecone is slow. |
| Tracing start | Traces start at the Next.js server render, not the browser | The plan keeps browser tracing minimal; real-browser LCP/INP are sent as metrics instead. |
| Brand | "Larkspur": original name, logo, and placeholder art | README forbids copying another retailer. |

Known gaps to pick up later: the search baseline was recorded keyword-only and should be re-recorded once Pinecone is connected.

## Catalog, orders, and stores build notes (2026-09-26, branch `catalog-stores`)

| Topic | Choice | Why |
|---|---|---|
| Generated catalog | `services/commerce/src/commerce/seed/gen/`, one module per department, deterministic (randomness seeded by each product's slug) | Adding or editing one product never changes another's stock or SKU; the data is reviewable code. |
| Data correctness | `tests/unit/test_catalog_data.py` checks every tag against the nutrition facts and allergens (e.g. "fat free" means under 0.5 g fat; "vegan" means no milk, egg, honey, or gelatin) | The assistant will answer from this data, so a wrong tag is a wrong answer. |
| Tags | Controlled vocabulary in `catalog/tags.py`; stored as a PostgreSQL array with a GIN index; filters `tag` (all of) and `exclude_tag` (none of) | Exact answers for "organic fat free, not whole milk" instead of hoping keywords line up. |
| Keyword search | Custom English analyzer with search-time synonyms ("nonfat" = "fat free" = "skim"); a cross-field clause so "dairy free milk" matches a title plus a tag | Found by testing real questions against the data. |
| Dev order history | `seed/orders.py`: 14 scenario orders for alice and bob, updated in place on every seed with fresh relative dates and stable IDs (two of them, `alice-partly-returned` and `alice-return-in-progress`, get their return history from the returns milestone); simulated 8.25% Texas tax (food and gift cards exempt) until Stripe Tax exists | Return conversations need real orders in every policy branch. |
| Assistant scripts | `evals/assistant/*.jsonl`, checked against the seed data by `tests/unit/test_assistant_scenarios.py` (which recomputes every refund) | Two hand-computed refunds were wrong on the first draft; the test caught them. |
| Policy text | `content/policies/*.md`, versioned with effective dates | What the assistant will retrieve from Pinecone and cite. |
| Maps | Google's keyless embed (one store at a time) by default; with `GOOGLE_MAPS_API_KEY` set, the Maps JavaScript API shows all 10 pins | Works with no account; the key path upgrades it. |
| Search eval | 20 new attribute queries labeled by rule (type + tags), keyword-only nDCG@10 0.95; baseline re-recorded for the 2,358-product catalog (overall nDCG@10 0.79, keyword-only) | The 54 original hand labels only know the first 51 products, so new correct results count as misses (e.g. every top-5 hit for "noise cancelling headphones for travel" is right but only one is labeled). **Relabel those queries and re-record once Pinecone is connected.** |
| Parallel checkouts | `API_PORT` / `WEB_PORT` for `pnpm dev`; this worktree used 8200/3200, database `commerce_catalog`, `SEARCH_ENV=dev-catalog` | Another agent was running in another worktree at the same time. |

---

## Next steps, in order

1. ~~Clone on Windows.~~ Done. ~~Step 1 (fix the handoff docs).~~ Done. ~~Step 2 (Milestone 1).~~ Done.
2. **Free a Pinecone slot**, set `PINECONE_INDEX_NAME=ai-commerce`, run `pnpm reindex`, then `pnpm eval:search --record-baseline` to record the hybrid baseline.
3. **Step 3 (Milestone 2): checkout and orders.** Needs a Stripe test-mode account, the Stripe CLI, and Stripe Tax with a test state registration.

---

## Prompt to paste into Claude Code on Windows

```text
Read HANDOFF.md, then docs/PLAN_ai-commerce-build.md, then every file in docs/handoff/.
HANDOFF.md and the plan override docs/handoff where they differ.
Save the "All decisions made" table from HANDOFF.md to your memory for this project.
Step 0 is done and pushed. Do Step 1 (update docs/handoff to match the plan).
Stop after Step 1 and show me the diff before committing.
```

---

## Useful facts verified on 2026-09-25

These are already in the plan. Re-check the versions when you pin lockfiles.

- **Newest versions:** Next.js 16.3.6 · livekit-agents 1.8.3 · langgraph 1.2.12 · langchain 1.4.2 · temporalio 1.33.0 · fastapi 0.141.1 · ragas 0.4.3.
- **Ragas 0.4 changed its API.** Use `ragas.metrics.collections`, `@experiment`, and `ascore()`. **Don't use `evaluate()`**: it is deprecated and breaks with the new metrics. Claude can be the judge through `llm_factory(..., provider="anthropic")`, with the `anthropic` package installed separately.
- **Stripe:**
  - Checkout Sessions is Stripe's recommended option.
  - Refund states include `requires_action` and `canceled`, and a succeeded refund can still fail later.
  - Stripe forgets idempotency keys after 24 hours, so always check Stripe before retrying.
  - Test-mode tax is $0 until you add a test state registration.
- **The AI must never confirm a return itself.** The model has no confirm tool, and the confirmation token never enters model context or saved graph state.
- **LiveKit's OTel export covers traces only.** Turn its per-stage timing events into metrics with a small handler.
- **Cartesia:** pin `sonic-3.6-2026-08-27`. The LiveKit plugin otherwise defaults to `sonic-3`.
