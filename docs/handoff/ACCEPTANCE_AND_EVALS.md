# Acceptance, tests and evaluation

## Required automated checks

| Area | Cases that must pass |
|---|---|
| Identity | A signed-out visitor is sent to sign-in for every non-public page and returned afterward; a `returnTo` pointing off-site is ignored; every private API returns 401 with no session, even if the Next.js redirect is bypassed; Customer A cannot list, read, quote, confirm or view a return for customer B; staff role is separate |
| Money | Server ignores client-submitted price/refund amount; currency arithmetic is exact; Stripe Tax returns non-zero tax for the test state; tax/shipping assumptions are documented |
| Stock | Concurrent checkouts cannot oversell; expired reservations release stock; price/stock change creates a new quote |
| Payment | Verified signature, duplicate/out-of-order webhooks, a webhook that never arrives (timer + reconciliation), worker crash mid-checkout, provider timeout/reconciliation, payment failure, refund pending/failure/requires_action/canceled, a succeeded refund that later fails |
| Return | Ineligible category/date/quantity, repeat requests, stale or altered quote, quantity already returned, ambiguous item, required inspection, worker crash after the refund call |
| Confirmation | Exact item/amount/method bound to token; the model's tool list has no confirm tool; no confirmation token appears in model messages, tool results, or graph checkpoints; unknown or interrupted speech never confirms; repeated clicks yield same operation |
| Conversation | Policy answer citation; no policy hallucination when source absent; no cross-user conversation access; voice/text turn race controlled |
| Reliability | Worker retry after side effect, voice disconnect/resume, search index lag, cache eviction, model/provider timeout and human handoff |
| Privacy | A fake email sent through a request never appears in exported traces or logs |
| UI | WCAG 2.2 AA: keyboard navigation, labels, focus, target size, error/empty/loading states, responsive layout, captions and text fallback |

Use unit tests for domain rules, integration tests for database/workflow/provider adapters, and Playwright for the complete browser journey. Keep provider contract tests separate from simulators. A meaningful end-to-end test buys an item with Stripe test mode and returns it; when keys are unavailable, run the simulator path and label it. Pure unit tests may use a stand-in at the Pinecone adapter boundary; integration tests and evals use real Pinecone.

## Usage caps

Enforce per-user caps on voice minutes per day, concurrent voice sessions, and LLM tokens per conversation, and rate-limit `/v1/voice/token`. Record cap hits as a metric.

## Evaluation and monitoring system

### A. Monitoring with OpenTelemetry

Every customer action becomes one **trace**: a timeline of every service call it caused, from the click through the API, Temporal, and Stripe, and back.

| Part | What it does |
|---|---|
| **Instrumentation** | Next.js: `instrumentation.ts` with `registerOTel` from `@vercel/otel`. Python: `opentelemetry-instrumentation-fastapi`, `-sqlalchemy`, `-httpx`, and `-redis`. Temporal: `temporalio.contrib.opentelemetry.TracingInterceptor`. LiveKit: `livekit.agents.telemetry.set_tracer_provider(..., allow_pii=False)` (traces only). LangGraph/LangChain: `langsmith[otel]` with `LANGSMITH_OTEL_ENABLED=true`. Browser: `web-vitals` (`onLCP`, `onINP`); keep browser tracing minimal. |
| **One trace per action** | W3C trace headers pass between services. The trace ID also goes into outbox events and Stripe `metadata`, so webhooks join the same trace. |
| **Collector** | One OTel Collector (contrib build). Redaction, attributes, and transform processors remove personal data: emails, names, addresses, and card-like numbers. Tail sampling keeps 100% of errors, money operations, and voice confirmations, and 10% of normal traffic. |
| **Where data goes** | Locally: `grafana/otel-lgtm` (Grafana, Tempo, Loki, Prometheus), development only. Cloud: ADOT beside each ECS Fargate task, to X-Ray and CloudWatch. AI traces also go to LangSmith. |
| **Shared labels on every span** | `customer_hash` (never the raw ID), `conversation_id`, `operation_id`, `quote_id`, `order_id`, `policy_version`, `model_id`, `prompt_version`. LLM spans use the OTel GenAI names (`gen_ai.*`), which are still in "Development" status; pin the version. |
| **Logs** | JSON logs, each with a trace ID, and no personal data. |

**Metrics:**

| Group | Metrics |
|---|---|
| Shopping | Search speed (p50/p95), zero-result searches, add-to-cart rate, index lag |
| Sign-in | Successes and failures (never passwords or raw emails) |
| Money | Checkouts started, paid, failed, and expired; webhook delay; checkouts stuck in reconciliation; refunds by state; duplicate requests blocked; ownership denials |
| AI | Tokens and cost per conversation, tool calls per turn, tool errors, handoff rate, answers with no citation, cap hits |
| Voice | Time per stage (speech-to-text, first LLM token, first audio), end-of-speech to first audio, interruption stop time, session minutes, false-confirmation blocks |
| Platform | Request rate, errors, and duration per endpoint; outbox lag; Temporal workflow failures; Pinecone, OpenSearch, and LLM latency and errors |

**Dashboards (4):** Shopping and checkout · Returns and refunds (money) · Assistant quality and cost · Voice.

**Alerts:**

| Level | Fires when |
|---|---|
| **Page now** | Our refund records don't match Stripe's. A duplicate refund is detected. Ownership denials suddenly jump. Webhook signature failures jump. |
| **Warn** | Search p95 over 300 ms. Commerce availability below 99.9%. Outbox lag over 60 s. A checkout stuck over 15 min. LLM spend per hour over budget. Voice p95 over 2 s. Handoff rate jumps. Live eval scores drop. |

**Money audit trail:** every refund links quote → approval → return → refund attempt → Stripe refund ID → trace ID. A daily reconciliation job compares our records with Stripe and reports any gap.

### B. Evaluation system (including Ragas)

Test the AI the way we test code: fixed datasets, automatic scores, and gates that block bad changes. Safety checks use plain code, never an AI judge.

| Layer | What it checks | Tool | When it runs | Gate |
|---|---|---|---|---|
| **1. Safety and behavior checks** | Right tools in the right order; no tool used for another customer; no confirmation without a real approval; amounts match the backend exactly; each citation points to a real policy version | pytest with `langsmith[pytest]`, plus `agentevals` trajectory match | Every pull request (fast set of about 30), and nightly (full set) | **Hard gate: 100%** |
| **2. Policy answer quality (Ragas)** | `Faithfulness`, `AnswerRelevancy`, `ContextPrecision`, `ContextRecall`, `NoiseSensitivity` | Ragas 0.4.x, with Claude as the judge | Nightly, and on any change to prompts, embeddings, or policy text | Must not drop more than a set margin below the baseline |
| **3. Search quality** | Policies: right section in Pinecone's top 5? Products: top 10 results good for about 100 labeled queries? | Our own script | On any index, embedding, or ranking change | Must not drop below the baseline |
| **4. Conversation quality** | Task finished, right item picked, on topic, handed off when it should | Ragas agent metrics (`ToolCallAccuracy`, `ToolCallF1`, `AgentGoalAccuracyWithReference`, `TopicAdherence`) plus an LLM judge | Nightly | Must not drop below the baseline |
| **5. Voice audio replay** | Recorded audio (accents, noise, pauses, barge-in, "mm-hmm") through the real speech-to-text → graph → speech pipeline | Our own runner | Weekly and before a release | **False confirmations = 0**; latency reported per stage |
| **6. Red team** | Prompt injection in product and policy text; asking for another customer's data; "refund me $500"; jailbreak attempts | Scripted attack set | Every release | **Hard gate: 0 unsafe actions** |
| **7. Live evals** | Sampled pilot conversations (personal data removed), plus thumbs up/down | LangSmith online evaluation; a scheduled job pulls sampled traces, runs Ragas `Faithfulness`, and writes scores back | Continuously; hourly for the Ragas job | Alert when scores drop |

**Rules that keep evals honest:**

- Two datasets: a *dev* set for tuning and a *held-out* test set never used for tuning.
- Before an AI-judge score becomes a gate, compare it with human labels on 50 examples and record agreement.
- Soft gates start from a measured baseline; do not invent a success percentage from a small demonstration.
- Any change to the prompt, model, tools, embeddings, or policy text runs the full suite and a side-by-side comparison. Prompts are versioned in the repo, and their version is on every trace.
- A failed live conversation goes to a review queue and, after review, becomes a new eval scenario.
- Datasets use synthetic customers only. Personal data is removed from any pilot sample before an outside judge sees it.

**Wiring Ragas** (the API changed in 0.4): pin `ragas==0.4.*` and install `anthropic` separately. Use metrics from `ragas.metrics.collections`, the `@experiment` decorator, and `metric.ascore(...)`. Do not use the deprecated `evaluate()` function. Use Claude as the judge with `llm_factory(model, provider="anthropic", client=Anthropic())`. Convert LangGraph conversations with `ragas.integrations.langgraph.convert_to_ragas_messages`. Draft policy questions with `TestsetGenerator`; a person reviews every question. Keep all Ragas calls in `evals/ragas_runner.py`. `openevals` is a backup.

**Dataset files** (in `evals/`):

| File | Holds |
|---|---|
| `scenarios/*.jsonl` | One conversation per line: `id`, `category`, `input` or `audio_file`, `customer_id`, `expected_intent`, `expected_tools`, `must_not`, `expected_handoff`, `reference_answer`, `reference_policy_sections`, `split` (dev or test), `tags` |
| `policy_qa.jsonl` | About 100 policy questions with reference answers and correct section IDs |
| `search_queries.jsonl` | About 100 product queries with graded good results |
| `audio/` | Recorded audio for voice replay, with consent and no real customer data. Accent and noise cases require recorded audio here. |
| `redteam/` | Attack scripts |

## AI evaluation set

Create at least 200 labeled scenarios before a wider pilot, with examples across: simple policies, order status, one/multiple matching items, accents/noise, corrections, pauses, expired policies, exception requests, prompt injection in product/policy text, different customers, repeat confirmation, disconnection, failed tools, and status changes during conversation. Record expected intent, tool calls, identity boundary, policy evidence, user-visible response and whether handoff is needed.

Evaluate intent accuracy, return-item selection, policy citation correctness, false confirmations, unauthorized tool attempts, resolution rate, handoff rate, end-of-speech to meaningful audio, and cost per resolved task. Jev must be compared with the baseline router on the same set, including uncertainty calibration and fallback behavior.

## Proposed pilot service targets

These are targets to test, not claims of delivered performance:

- Product search p95 below 300 ms at the service boundary.
- Product page p75 Largest Contentful Paint below 2.5 s in real browser telemetry.
- Ordinary voice response: end of speech to first meaningful audio p50 below 1 s, p95 below 2 s.
- Tool-assisted voice response: end of speech to substantive answer p95 below 4 s when dependencies are healthy; report acknowledgments separately.
- Interruption: speech onset to stopped playback p95 below 300 ms.
- Commerce availability objective: 99.9% for the defined pilot request class.
- Zero unauthorized or duplicate refunds in adversarial release tests. Monitor and reconcile in production as well.

Load-test assumptions: 100k variants, 100k registered shoppers, 500 peak dynamic API requests/s, 20 checkout attempts/s and 50 simultaneous voice sessions. The build report must state hardware, data volume, provider quotas, actual achieved rate, p50/p95/p99, errors, and bottleneck. Do not imply the target was met without measurement.

## Human release review

Before a live pilot, a responsible owner must set real return rules, tax registrations, fulfillment provider behavior, merchant identity, privacy/retention policy, payment capture timing, fraud/manual-review criteria, support escalation, and production secrets. A coding agent may provide defaults for a sandbox only.
