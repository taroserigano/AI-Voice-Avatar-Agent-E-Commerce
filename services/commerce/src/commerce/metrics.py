"""Application metrics. Names follow the plan's metric groups; no personal data in labels."""

from __future__ import annotations

from opentelemetry import metrics

_meter = metrics.get_meter("commerce")

signin_attempts = _meter.create_counter(
    "commerce.signin.attempts",
    description="Sign-in attempts by outcome (success, failure, rate_limited)",
)
search_requests = _meter.create_counter(
    "commerce.search.requests",
    description="Product searches, labeled by whether they returned results",
)
search_duration = _meter.create_histogram(
    "commerce.search.duration",
    unit="ms",
    description="Product search time at the service boundary",
)
search_leg_duration = _meter.create_histogram(
    "commerce.search.leg.duration",
    unit="ms",
    description="Time per search backend (opensearch, pinecone, postgres)",
)
search_leg_errors = _meter.create_counter(
    "commerce.search.leg.errors",
    description="Search backend failures by backend",
)
cart_adds = _meter.create_counter(
    "commerce.cart.adds",
    description="Cart line additions (for add-to-cart rate)",
)
ownership_denials = _meter.create_counter(
    "commerce.ownership.denials",
    description="Requests for a resource owned by someone else (answered with 404)",
)
outbox_published = _meter.create_counter(
    "commerce.outbox.published",
    description="Outbox events published, by topic and outcome",
)
index_lag = _meter.create_histogram(
    "commerce.search.index_lag",
    unit="ms",
    description="Time from a committed product change to it being searchable",
)
