# Serigan Mart: AI commerce demo

A portfolio-quality online store with an AI shopping assistant. Everything sits behind
sign-in: browse and search a catalog, keep a cart, and (in later milestones) check out with
Stripe test mode and return items by text or voice.

The build follows [docs/PLAN_ai-commerce-build.md](docs/PLAN_ai-commerce-build.md). The
requirements are in [docs/handoff/](docs/handoff/), and [HANDOFF.md](HANDOFF.md) has the
current status and every decision made so far.

**Status:** Milestone 1 (sign-in and shopping foundation) is built, plus the redesign,
reviews, order tracking, the return and refund policy, **Ask Steph** (the shopping
assistant), **Xena** (voice and text returns and refunds on `/support`), return quotes and
confirmation, and **Jev** decision signals. Stripe checkout and Temporal workflows come next. The current feature
batch is planned in [docs/features/](docs/features/README.md).

## What works now

- **Sign-in wall.** Every page except sign-in, create account, privacy, terms, and
  accessibility sends a signed-out visitor to `/sign-in?returnTo=…` and
  returns them afterward. Every private API also answers 401 on its own, and the API refuses
  to start if a route is missing the session check.
- **Simple sign-in:** the API checks the email and password and sets a session cookie.
  Nothing else: no rate limiting, password reset, or external identity provider.
- **Catalog:** about 2,000 original products in 21 departments, mostly grocery. Every
  product has a type and diet/feature tags (organic, fat free, sugar free, lactose free,
  vegan, wireless, ...); food has nutrition facts, ingredients, and allergens. It's generated
  deterministically (`services/commerce/src/commerce/seed/gen/`), and a test checks every tag
  against the facts, since the assistant will answer from this data.
- **Hybrid search:** OpenSearch (keywords, typos, SKUs, synonyms such as "nonfat" = "skim")
  plus Pinecone (meaning), merged with reciprocal rank fusion. Price and stock always come
  from PostgreSQL. Filters for type, tags (required or excluded), brand, and price; facets,
  sorting, and pagination.
- **Store locator:** 10 demo stores around Dallas-Fort Worth on a Google map, with hours,
  open-now status, and directions.
- **Order history for the dev accounts:** 14 orders covering every return case (inspection,
  perishables, partial returns with cent rounding, final sale, late, not delivered, ...),
  reset to fresh dates on every `pnpm db:seed`.
- **Ask Steph:** a shopping assistant behind the button at the bottom right of every shop
  page (`services/assistant`, LangGraph with Claude or OpenAI). It searches the catalog with exact filters
  ("non fat organic milk, not regular milk"), shows product, order, store, and cart cards,
  adds to the cart, checks orders, and answers policy questions with numbered citations it
  can only take from sections it actually retrieved. Conversations are saved per customer.
  It calls the commerce API with its own service identity for the signed-in customer (never
  the customer's cookie), and it has no tool that can confirm, pay, or refund. Without a
  working `ANTHROPIC_API_KEY` or `OPEN_AI_API`, a scripted model answers from the same tools
  and the chat says **Simulated**.
- **Support with Xena (`/support`):** talk (or type) to Xena about products, returns, and refunds. She
  searches the same live catalog as Steph and opens product details for ingredient, allergen,
  nutrition, specification, and variant questions. Unknown filters return no recommendation.
  She finds the order and item, explains eligibility from the store's return options, prices the
  return, and shows a quote card. The customer confirms with the **Confirm return** button, or
  by voice: Xena reads the quote back (built by code, not the model) and only a clear, final
  "yes" after the full read-back counts, checked by the app (a strict rule, plus Jev's vote
  when enabled). The browser then confirms directly with the store using a single-use token the
  assistant never sees; the conversation resumes and re-checks the outcome with the store.
  Voice is turn-based over HTTP: Groq Whisper (or Deepgram, or the browser) for speech-to-text
  and Cartesia `sonic-3.6-2026-08-27` (or the browser) for speech; talking over Xena stops her.
  In development a "simulated speech" box drives the same path without a microphone. Order pages'
  **Start a return** opens Xena on that item.
- **Return quotes and confirmation (commerce API):** `POST /v1/returns/quote` prices a return
  from the order's saved amounts (every seeded scenario matches the eval oracle to the cent);
  `POST /v1/returns/quotes/{id}/confirmation` and `POST /v1/returns/confirm` (with an
  `Idempotency-Key`) need the customer's own browser session, create exactly one return per
  quote, and refuse altered, expired, stale, or reused quotes. Refunds are simulated until Stripe
  is connected: perishables at confirmation, others at the (development-only) carrier scan,
  warehouse receipt, or inspection, one refund per stage.
- **Jev (TypeSafe):** one typed request per turn reads the intent, return reason, which order
  line, escalation, and rule-bypass attempts; confident answers steer the assistant, and Jev can
  veto (never cause) a spoken confirmation. A labeled simulator answers until `TYPESAFE_API_KEY`
  is set; `pnpm eval:jev` compares the two.
- **Return and refund policy:** a detailed, versioned policy plus the rules every channel
  (site, Steph, Xena, staff) follows, public at `/returns-policy` with citable section anchors.
  Its numbers are machine-readable and tested against the code.
- **Assistant scripts:** scripted product Q&A and return conversations with known-right
  answers in `evals/assistant/`, and the policy text they cite in `content/policies/`.
- **Durable cart** per customer. Customers can't reach each other's carts or orders.
- **Outbox publisher** that keeps OpenSearch and Pinecone in sync with PostgreSQL.
- **OpenTelemetry everywhere:** one trace per page render, from Next.js through the API to
  PostgreSQL and OpenSearch. Personal data is removed in-process and again in the collector.
  A "Shopping" dashboard ships in Grafana.
- **Search evals v1:** 54 labeled queries with a recorded baseline.

## Prerequisites

- Either an installed PostgreSQL 16 or newer (see [Without containers](#without-containers)),
  or Docker Desktop / Podman with about 8 GB of RAM (OpenSearch needs about 2 GB)
- Node.js 20.9 or newer, and pnpm 10
- [uv](https://docs.astral.sh/uv/) (it installs Python 3.12 for you)
- Optional: a Pinecone API key, for meaning-based search

## Quick start

```bash
cp .env.example .env        # then edit: Pinecone key, SEARCH_ENV=dev-<yourname>
pnpm local:up               # PostgreSQL + OpenSearch on this machine (or: pnpm infra:up)
pnpm bootstrap              # install deps, migrate, seed, build the search indexes
pnpm dev                    # API :8000, outbox worker, web :3000
```

Open http://localhost:3000 and sign in with a development account:

| Account | Password | Role |
|---|---|---|
| `alice@example.com` | `alice-dev-password` | customer |
| `bob@example.com` | `bob-dev-password` | customer |
| `staff@example.com` | `staff-dev-password` | staff |

These accounts exist only when `APP_ENV` is `dev`, `test`, or `ci`.

### Without containers

`pnpm local:up` runs just what the app needs, directly on your machine:

- **PostgreSQL** from your own installation (`PG_BIN`, the newest
  `C:\Program Files\PostgreSQL\<n>\bin`, or `pg_ctl` on your PATH). It uses a private data
  folder with a `commerce` user and the `commerce` and `commerce_test` databases, so an
  existing PostgreSQL service and its data are left alone. Port 5432 must be free.
- **OpenSearch**, downloaded on first use (about 1 GB), localhost only.

Both live in `%LOCALAPPDATA%\ai-commerce` (or `~/.local/share/ai-commerce`), outside the
repo. `pnpm local:status` shows what's running; `pnpm local:down` stops both. Redis,
Temporal, and the telemetry stack aren't needed to run the app yet; `pnpm dev` notices
there's no OTel Collector and simply doesn't export telemetry.

### Two checkouts at once (git worktrees)

Give each checkout its own database, search indexes, and ports, so they never touch
each other's data. In that checkout's `.env`:

```bash
COMMERCE_DATABASE_URL=postgresql+psycopg://commerce:commerce@localhost:5432/commerce_mybranch
SEARCH_ENV=dev-mybranch
```

Create the database once (`CREATE DATABASE commerce_mybranch`), run `pnpm db:migrate`,
`pnpm db:seed`, and `pnpm reindex`, then start it on other ports:
`API_PORT=8200 WEB_PORT=3200 pnpm dev`. For its integration tests, set
`COMMERCE_TEST_DATABASE_URL` to a separate test database.

### Podman

The `infra:*` scripts use whichever of Docker or Podman is running; set
`CONTAINER_ENGINE=podman` (or `docker`) to choose. With Podman, create a **rootful** machine
once, because OpenSearch asks for unlimited locked memory, which rootless containers can't
grant:

```bash
podman machine init --cpus 4 --memory 8192 --rootful --now
```

`podman compose` runs the `docker-compose` or `podman-compose` program, so one of them must
be installed.

### Pinecone

Pinecone is the only vector store and is always the real service; there is no local
substitute. Set `PINECONE_API_KEY` and `PINECONE_INDEX_NAME` (default `ai-commerce`). The
app creates that index with Pinecone's hosted embedding model if it doesn't exist, which
needs a free index slot in your Pinecone project. It refuses to use an index it didn't
create, so it can't write into another project's data. Each developer uses their own
namespace through `SEARCH_ENV`.

Without a working Pinecone setup, the app still runs: search is keyword-only and the page
says so. After fixing the settings, run `pnpm reindex`.

## Useful URLs

| What | URL |
|---|---|
| Storefront | http://localhost:3000 |
| API docs (development only) | http://localhost:8000/docs |
| Assistant API docs (development only) | http://localhost:8001/docs |
| Return and refund policy (public) | http://localhost:3000/returns-policy |
| Grafana (traces, logs, metrics, dashboards) | http://localhost:3001 |
| Temporal UI (used from Milestone 2) | http://localhost:8233 |

## Commands

| Command | What it does |
|---|---|
| `pnpm local:up` / `local:down` / `local:status` | Start, stop, or check PostgreSQL and OpenSearch without containers |
| `pnpm infra:up` / `infra:down` / `infra:reset` | Start, stop, or wipe all local services in containers (Docker or Podman) |
| `pnpm dev` | Run the commerce API, assistant API, outbox worker, and web app together |
| `pnpm db:migrate` / `pnpm db:seed` | Apply migrations (commerce, then the assistant's tables and checkpoints) / seed catalog and dev accounts (safe to repeat) |
| `pnpm reindex` | Rebuild OpenSearch and Pinecone from PostgreSQL |
| `pnpm contracts` | Regenerate `packages/contracts` from the API's OpenAPI schema |
| `pnpm lint` / `pnpm typecheck` | Ruff, ESLint, mypy (strict), tsc |
| `pnpm test` | Python unit and integration tests, plus web unit tests |
| `pnpm test:e2e` | Playwright browser tests (needs `pnpm dev` running) |
| `pnpm eval:search` | Score search quality against the baseline |
| `pnpm eval:jev` | Score Jev (or its simulator) on the labeled routing set |

`make <target>` wrappers exist for the same commands on macOS and Linux.

The app reads its database from `COMMERCE_DATABASE_URL`, never `DATABASE_URL`, so a `.env`
shared with another project can't point it at that project's database. Integration tests
always use a separate `commerce_test` database (`COMMERCE_TEST_DATABASE_URL`) and migrate it
themselves.

## Layout

```
apps/web/              Next.js storefront (App Router, Tailwind, TanStack Query)
  proxy.ts             sign-in wall (convenience only; the API enforces 401)
services/commerce/     FastAPI: auth, catalog, cart, orders, returns, policies, search, outbox, seed
services/assistant/    FastAPI + LangGraph: Steph (and Xena), tools, scripted model, prompts
packages/telemetry/    shared Python OpenTelemetry setup and redaction
packages/contracts/    OpenAPI schema and generated TypeScript client
infra/                 Docker Compose, OTel Collector config, Grafana dashboards
evals/                 search queries, scorer, and baselines
tests/e2e/             Playwright browser tests
docs/                  build plan and handoff docs
```

`services/voice` and `workers/workflows` arrive with their milestones.

## Connected vs. simulated (Milestone 1)

| Integration | State |
|---|---|
| PostgreSQL, Redis, OpenSearch, OTel Collector, Grafana | Real (local Docker or Podman) |
| Pinecone | Real service; code and guards tested, but the semantic path hasn't run end to end yet because the account had no free index slot |
| Sign-in | Email and password checked by the API (by design, no other layers) |
| Text assistant LLM | Claude when `ANTHROPIC_API_KEY` works; otherwise OpenAI `gpt-6-sol` when `OPEN_AI_API` works; otherwise the labeled scripted model |
| Policy search | OpenSearch keyword search over policy sections; Pinecone joins when its index slot is free |
| Jev (TypeSafe) | Real when `TYPESAFE_API_KEY` is set; otherwise the labeled simulator |
| Speech-to-text / text-to-speech | Real: Groq Whisper and Cartesia with the keys in `.env` (Deepgram if keyed); the browser's own voice features otherwise. LiveKit (the plan's streaming voice) isn't connected yet |
| Refunds | Simulated (records and states as Stripe will use them); Stripe checkout comes next |
| Stripe, Temporal workflows | Not used yet |
