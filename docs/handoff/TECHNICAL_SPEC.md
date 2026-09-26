# Technical specification

## Stack and service boundaries

| Concern | Choice | Ownership |
|---|---|---|
| Web | React, TypeScript, Next.js App Router, Tailwind, shadcn/ui, TanStack Query for interactive server state | Storefront and voice UI |
| Commerce | Python, FastAPI, Pydantic, SQLAlchemy, Alembic | Catalog, pricing, cart, stock, checkout, orders, returns |
| Data | PostgreSQL; Redis only as cache | Source of truth and expendable read cache |
| Product discovery | OpenSearch for keywords, filters, and facets; Pinecone (namespace `products-<env>`) for meaning-based search; results merged with reciprocal rank fusion. Price and stock always come from PostgreSQL. | Rebuildable catalog projections |
| Assistant | FastAPI, LangGraph, LangChain, PostgreSQL checkpointer | Text and voice conversational state, narrow tools |
| Policy retrieval | Pinecone with version/effective-date metadata; a real Pinecone account in every environment, one namespace per environment (`policies-<env>`) | Approved policy text and citations |
| Voice | LiveKit Cloud + Python LiveKit Agents + Deepgram Flux + Cartesia | WebRTC session, transcript, speech, interruption |
| Business process | Temporal Python workers | Checkout/return wait states, label and refund retries |
| Payment | Stripe test mode during development; Stripe Checkout Sessions with `automatic_tax` (Stripe Tax) | Checkout session, tax, and provider refund |
| Events | PostgreSQL transactional outbox; a polling publisher locally, EventBridge/SQS in AWS | Search projection and notifications |
| Identity | Email and password checked by the commerce API, in every environment; no external identity provider, rate limiting, or password reset | Authenticated subject and server-side roles |
| Runtime | Docker Compose locally; AWS ECS Fargate + ALB, S3/CloudFront, RDS/Aurora for cloud | Independent web/API/voice/worker scaling |
| Telemetry | OpenTelemetry in every service; one OTel Collector that removes personal data and keeps all money and error traces; Grafana (`grafana/otel-lgtm`) locally; CloudWatch/X-Ray via ADOT in the cloud; LangSmith for AI traces | Request, workflow, and assistant diagnostics |

Use a monorepo such as `apps/web`, `services/commerce`, `services/assistant`, `services/voice`, `workers/workflows`, `packages/contracts`, `infra`, `tests`. A different clean layout is acceptable if justified. Use current compatible stable releases and pin them in lockfiles; do not hardcode version claims from the research date.

Pinecone is the only vector store. Pure unit tests may use a small stand-in at the Pinecone adapter boundary; it lives only in `tests/unit/`, and no app setting can select it. The running app, integration tests, evals, and the demo use real Pinecone.

## Request paths

Every page and API route requires sign-in except the public pages listed in PRODUCT_REQUIREMENTS.md, the auth routes, `/healthz`, and the Stripe webhook (which verifies its signature instead). The Next.js sign-in redirect is a convenience only; every FastAPI route checks the session itself and returns 401 when signed out.

Shopping: browser → Next.js → commerce API → PostgreSQL. Product search reads OpenSearch and Pinecone, merges the lists, then loads current price and stock from PostgreSQL; checkout rechecks authoritative PostgreSQL state. AI text: browser → assistant API (stream response via SSE) → LangGraph → authorized typed commerce tool/policy retrieval. Voice: browser ↔ LiveKit ↔ Python voice worker → shared LangGraph package → the same tools. LiveKit media does not travel through the HTTP load balancer. Temporal workers poll their task queues; they do not expose a public HTTP endpoint.

## Suggested tables and invariants

- `users`, `sessions`, `products` (with `product_type`, controlled-vocabulary `tags`, and `details`: nutrition, ingredients, allergens, specs), `variants`, `categories`, `prices`, `stock_locations`, `inventory_balances`, `inventory_reservations`, `stores` (store locator only).
- `carts`, `cart_items`, `checkout_attempts`, `orders`, `order_lines`, `payment_attempts`, `shipments`.
- `return_quotes`, `return_requests`, `return_items`, `refund_attempts`, `support_cases`, `policy_versions`.
- `conversations`, `messages`, `graph_checkpoints`, `tool_audit`, `outbox_events`, `provider_webhook_events`.

Use integer minor currency units and ISO currency codes. Store purchase-time price, tax, discount, merchant, and applicable policy reference with each order line; tax and discount come from Stripe's line items after payment. Constrain return quantity to purchased minus already returned. Add unique business-operation keys to checkout, return, refund and webhook records. Keep one current inventory balance per variant/location and reserve atomically. Do not treat search/cache as authoritative.

## API contract sketch

All routes require a verified identity except the auth routes, `/healthz`, and the Stripe webhook. Enforce ownership on every lookup and mutation. IDs are opaque. Publish actual OpenAPI schemas and generate the TypeScript client.

| Method and path | Input | Output/behavior |
|---|---|---|
| `POST /v1/auth/sign-in` / `sign-up` / `sign-out` | credentials | Session cookie (HttpOnly, Secure, `SameSite=Lax`, fixed expiry); sign-out ends the server session |
| `GET /v1/products` | query; filters: category, brand, `product_type` (any of), `tag` (all of), `exclude_tag` (none of), price, in stock; pagination (signed in) | Product summaries (with type and tags) and facets (categories, brands, types, tags); search-backed |
| `GET /v1/products/{id}` | product ID (signed in) | Variants, description, nutrition, ingredients, allergens, specs; fresh price/stock fields |
| `GET /v1/stores` | signed in | Store locations with hours, services, and open-now status (America/Chicago) |
| `GET /v1/cart` / `PUT /v1/cart/items` | variant, quantity | Durable cart; server-side current estimate |
| `POST /v1/checkout/quote` | cart/version | Server totals and stock validation, "tax calculated at payment", quote expiry |
| `POST /v1/checkout/start` | quote ID, idempotency key | Checkout attempt (Temporal workflow ID = attempt ID) and Stripe Checkout Session URL |
| `GET /v1/orders` / `GET /v1/orders/{id}` | authenticated customer | Own orders only |
| `POST /v1/returns/quote` | order line, quantity, reason, condition | Structured eligibility result and exact quote |
| `GET /v1/returns/quotes/{id}` | quote ID | The quote and its single-use confirmation token, for the signed-in owner's browser only |
| `POST /v1/returns/confirm` | quote ID, bound confirmation token, idempotency key | One return ID and workflow status |
| `GET /v1/returns/{id}` | return ID | Authorized return plus separate refund state |
| `POST /v1/assistant/messages` | conversation, text | SSE text/event stream and structured UI cards |
| `POST /v1/voice/token` | authenticated request | Short-lived, room-scoped LiveKit token |
| `POST /v1/webhooks/stripe` | verified provider payload | Persist and deduplicate event; acknowledge promptly; signal the workflow |
| `GET /healthz` | none | Liveness |

Return quotes should include `quote_id`, `order_line_id`, `quantity`, `refund_amount_minor`, `currency`, `deductions`, `refund_destination` (original payment method only), `inspection_required`, `policy_version`, `expires_at`, `status`, and a quote hash that binds the confirmation. Expired, changed, or already consumed quotes require a new quote.

### Model-facing tools and confirmation

Model-facing tools are `list_my_orders`, `get_order_status`, `get_return_options`, `propose_return(quote_id)`, `search_products`, `get_product_details`, and `create_support_case`, through typed wrappers; never a free-form SQL/refund tool. The server injects the customer's identity into every call.

The model has **no confirm tool**. `propose_return(quote_id)` pauses the conversation with LangGraph `interrupt()` and shows the quote card. Only the browser's Confirm button, or the app-controlled voice-confirmation step, may call `POST /v1/returns/confirm`. The confirmation token is **never** put in the model's context or in saved graph state: the tool result the model sees holds only a quote summary, and the browser gets the token from its own signed-in call, `GET /v1/returns/quotes/{id}`. The graph resumes only from application code after the confirm endpoint answers; any side effect after the interrupt is safe to repeat.

## State and retries

Checkout-attempt states (one Temporal workflow per attempt): CREATED → STOCK_RESERVED → PAYMENT_PENDING → PAID, with explicit FAILED/EXPIRED/CANCELED branches that release the stock. The Stripe session's `expires_at` matches the reservation hold and the workflow timer. When the timer fires without a payment signal, query Stripe for the session's real status before expiring.

Order states are separate: an order row is created only after a verified `checkout.session.completed` with `payment_status = paid`, or `checkout.session.async_payment_succeeded`. Orders then move PAID → FULFILLING → DELIVERED. Capture is automatic in the sandbox.

Return states: REQUESTED/AUTHORIZED → IN_TRANSIT → RECEIVED → INSPECTED → CLOSED, or REVIEW/REJECTED/CANCELED. Refund states: NOT_REQUESTED → REQUESTED → PENDING → SUCCEEDED, FAILED, REQUIRES_ACTION, or CANCELED. A SUCCEEDED refund can later fail, so keep listening for `refund.updated` and `refund.failed`. Status labels must reflect observed provider/business state.

Persist business change plus outbox event in the same PostgreSQL transaction. Repeated webhooks and workflow deliveries are expected. Every external action gets a deterministic operation ID. After an ambiguous timeout, query Stripe/shipping state before retrying. Before **every** refund retry, check Stripe first: Stripe forgets idempotency keys after 24 hours. Temporal coordinates waits and retries but does not itself guarantee exactly-once external effects. A voice disconnect or interrupted LangGraph node must not repeat a committed return.

## Voice and assistant details

Issue short-lived room tokens from the authenticated server. Deepgram Flux supplies transcripts and turn completion; LiveKit supports media and interruption; Cartesia synthesizes the approved response. Share LangGraph definitions/tools between text and voice. Persist a conversation ID and serialize simultaneous text/voice turns. Preemptive work may perform read-only retrieval; never trigger side effects before intent and confirmation are settled. On barge-in, stop output and reconcile any in-flight operation before speaking again.

Separate response types: `assistant_text`, `policy_citation`, `product_card`, `order_card`, `return_quote_card`, `operation_status`, `handoff`. The client renders structured amounts and statuses from backend data. For a public question, retrieve versioned policy content and cite it. For a live fact, use an authenticated API. If evidence conflicts or the user asks for an exception, escalate.

Jev can be tried behind a feature flag for bounded intent choices and support triage after a baseline exists. Its probabilities are signals, not authorization. It is not on the critical purchase/refund path. Compare latency, accuracy, spend, and reliability before adopting it.

## Local and cloud operations

Local Compose provides PostgreSQL, Redis, OpenSearch, the Temporal dev server, the OTel Collector, and `grafana/otel-lgtm`; web/API/worker commands must be documented. Pinecone is always the real cloud service, with a per-developer namespace. The outbox publisher is a polling worker using `SELECT … FOR UPDATE SKIP LOCKED`; locally it feeds OpenSearch and Pinecone directly, and EventBridge/SQS are used in the cloud only. A transcript simulator exercises voice flows without voice accounts. Stripe test mode is required for a connected checkout demonstration; a clearly labeled payment simulator may exercise early development/tests only. Seed products, stock, policies and test customers.

Cloud proposal: CloudFront/WAF → Next.js ECS and ALB → FastAPI commerce/assistant ECS; separate voice and Temporal workers; Aurora/RDS PostgreSQL, managed Redis, managed OpenSearch, Pinecone, LiveKit, Stripe, S3, EventBridge/SQS. Use Taro's personal AWS account only, with Terraform pinned by `allowed_account_ids`. Keep credentials in a secrets manager. Configure backups, health checks, draining, provider quotas, and separate scaling for voice and HTTP workloads. Do not deploy without a reviewed environment and real account ownership.
