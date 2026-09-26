# Larkspur: AI commerce demo

A portfolio-quality online store with an AI shopping assistant. Everything sits behind
sign-in: browse and search a catalog, keep a cart, and (in later milestones) check out with
Stripe test mode and return items by text or voice.

The build follows [docs/PLAN_ai-commerce-build.md](docs/PLAN_ai-commerce-build.md). The
requirements are in [docs/handoff/](docs/handoff/), and [HANDOFF.md](HANDOFF.md) has the
current status and every decision made so far.

**Status:** Milestone 1 (sign-in and shopping foundation) is built. Checkout, returns,
the assistant, and voice come next.

## What works now

- **Sign-in wall.** Every page except sign-in, create account, privacy, terms, and
  accessibility sends a signed-out visitor to `/sign-in?returnTo=…` and
  returns them afterward. Every private API also answers 401 on its own, and the API refuses
  to start if a route is missing the session check.
- **Simple sign-in:** the API checks the email and password and sets a session cookie.
  Nothing else: no rate limiting, password reset, or external identity provider.
- **Catalog:** 51 original products in 9 departments, with generated placeholder images.
- **Hybrid search:** OpenSearch (keywords, typos, SKUs) plus Pinecone (meaning), merged
  with reciprocal rank fusion. Price and stock always come from PostgreSQL. Filters,
  facets, sorting, and pagination.
- **Durable cart** per customer. Customers can't reach each other's carts or orders.
- **Outbox publisher** that keeps OpenSearch and Pinecone in sync with PostgreSQL.
- **OpenTelemetry everywhere:** one trace per page render, from Next.js through the API to
  PostgreSQL and OpenSearch. Personal data is removed in-process and again in the collector.
  A "Shopping" dashboard ships in Grafana.
- **Search evals v1:** 54 labeled queries with a recorded baseline.

## Prerequisites

- Docker Desktop with about 8 GB of RAM (OpenSearch needs about 2 GB)
- Node.js 20.9 or newer, and pnpm 10
- [uv](https://docs.astral.sh/uv/) (it installs Python 3.12 for you)
- Optional: a Pinecone API key, for meaning-based search

## Quick start

```bash
cp .env.example .env        # then edit: Pinecone key, SEARCH_ENV=dev-<yourname>
pnpm infra:up               # PostgreSQL, Redis, OpenSearch, Temporal, OTel Collector, Grafana
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
| Grafana (traces, logs, metrics, dashboards) | http://localhost:3001 |
| Temporal UI (used from Milestone 2) | http://localhost:8233 |

## Commands

| Command | What it does |
|---|---|
| `pnpm infra:up` / `infra:down` / `infra:reset` | Start, stop, or wipe the local services |
| `pnpm dev` | Run the API, outbox worker, and web app together |
| `pnpm db:migrate` / `pnpm db:seed` | Apply migrations / seed catalog and dev accounts (safe to repeat) |
| `pnpm reindex` | Rebuild OpenSearch and Pinecone from PostgreSQL |
| `pnpm contracts` | Regenerate `packages/contracts` from the API's OpenAPI schema |
| `pnpm lint` / `pnpm typecheck` | Ruff, ESLint, mypy (strict), tsc |
| `pnpm test` | Python unit and integration tests, plus web unit tests |
| `pnpm test:e2e` | Playwright browser tests (needs `pnpm dev` running) |
| `pnpm eval:search` | Score search quality against the baseline |

`make <target>` wrappers exist for the same commands on macOS and Linux.

Integration tests use a separate `commerce_test` database and Redis database 15, and
migrate the test database themselves.

## Layout

```
apps/web/              Next.js storefront (App Router, Tailwind, TanStack Query)
  proxy.ts             sign-in wall (convenience only; the API enforces 401)
services/commerce/     FastAPI: auth, catalog, cart, orders, search, outbox, seed
packages/telemetry/    shared Python OpenTelemetry setup and redaction
packages/contracts/    OpenAPI schema and generated TypeScript client
infra/                 Docker Compose, OTel Collector config, Grafana dashboards
evals/                 search queries, scorer, and baselines
tests/e2e/             Playwright browser tests
docs/                  build plan and handoff docs
```

`services/assistant`, `services/voice`, and `workers/workflows` arrive with their milestones.

## Connected vs. simulated (Milestone 1)

| Integration | State |
|---|---|
| PostgreSQL, Redis, OpenSearch, OTel Collector, Grafana | Real (local Docker) |
| Pinecone | Real service; code and guards tested, but the semantic path hasn't run end to end yet because the account had no free index slot |
| Sign-in | Email and password checked by the API (by design, no other layers) |
| Stripe, Temporal workflows, LLM, voice | Not used yet (Milestones 2-4) |
