"""The shared span labels every service puts on its spans.

Names match the plan: ``customer_hash`` (never the raw ID), ``conversation_id``,
``operation_id``, ``quote_id``, ``order_id``, ``policy_version``, ``model_id``,
``prompt_version``.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import asdict, dataclass

from opentelemetry import trace


def customer_hash(customer_id: str, secret: str) -> str:
    """A stable, non-reversible label for a customer, safe to put on spans and logs."""
    digest = hmac.new(secret.encode(), customer_id.encode(), hashlib.sha256).hexdigest()
    return digest[:16]


@dataclass(frozen=True, slots=True)
class SpanLabels:
    customer_hash: str | None = None
    conversation_id: str | None = None
    operation_id: str | None = None
    quote_id: str | None = None
    order_id: str | None = None
    policy_version: str | None = None
    model_id: str | None = None
    prompt_version: str | None = None


def set_span_labels(labels: SpanLabels, span: trace.Span | None = None) -> None:
    target = span or trace.get_current_span()
    if not target.is_recording():
        return
    for key, value in asdict(labels).items():
        if value is not None:
            target.set_attribute(f"app.{key}", value)
