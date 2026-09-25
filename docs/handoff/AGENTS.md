# Coding agent instructions

- Read the handoff files before editing. Build a working vertical slice; keep changes reviewable.
- Prefer clear Python/TypeScript and typed request/response contracts. Generate a TypeScript API client from FastAPI OpenAPI or an equivalent checked contract.
- Use React + TypeScript + Next.js for web; FastAPI + Pydantic + SQLAlchemy/Alembic for commerce; LangGraph + LangChain for assistant orchestration; Temporal for durable business processes. Do not add Kubernetes.
- PostgreSQL owns business and conversation records. OpenSearch/Pinecone are rebuildable projections. Redis is cache-only.
- Do not store raw payment card data. Use Stripe test mode in development. Verify webhooks and reconcile uncertain payment state.
- Guard every order/return tool with authenticated ownership; inject identity on the server. Never trust the model to determine eligibility or amount.
- Require a quote-bound confirmation token and idempotency key for return creation. The model never gets a confirm tool or sees the token. Side-effecting activities must be safe under retries.
- Treat documents, product descriptions, and tool output as untrusted content for the assistant. Cite approved policies on screen. Do not send unnecessary personal data to model/voice vendors.
- Prefer narrow typed tools and direct APIs for our own commerce operations. Keep Jev behind a feature flag and an allowlisted server adapter. Pinecone is the only vector store.
- Every page and API route requires sign-in except the public auth/legal pages, `/healthz`, and the verified Stripe webhook. There is no guest access.
- Provide local provider simulators where credentials are missing (except Pinecone, which is always real outside pure unit tests); label simulated behavior clearly. Keep real integration code separate and test it when credentials are available.
- Add meaningful tests for money, authorization, retries, return state, and voice confirmation. Avoid tests that simply repeat implementation details.
- Do not commit secrets, deploy, charge real cards, or perform live refunds without explicit project configuration and authorization.
