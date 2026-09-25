"""Remove personal data from telemetry before it leaves the process.

The OTel Collector applies the same rules again (``infra/otel/collector.yaml``). Doing it
here too means a misconfigured collector, or a test exporter, never sees raw emails or
card-like numbers.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from opentelemetry.context import Context
from opentelemetry.sdk.trace import Event, ReadableSpan, Span, SpanProcessor

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+(?:@|%40)[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# 13-19 digits, optionally separated by spaces or dashes: the shape of a payment card number.
CARD_RE = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")

REDACTED_EMAIL = "[REDACTED_EMAIL]"
REDACTED_CARD = "[REDACTED_NUMBER]"

# Attribute keys whose values are always dropped, whatever they contain.
SENSITIVE_KEYS = frozenset(
    {
        "enduser.id",
        "user.email",
        "user.name",
        "user.full_name",
        "http.request.header.cookie",
        "http.request.header.authorization",
        "http.response.header.set_cookie",
    }
)


def redact_text(value: str) -> str:
    return CARD_RE.sub(REDACTED_CARD, EMAIL_RE.sub(REDACTED_EMAIL, value))


def _redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        items = list(value)
        if items and all(isinstance(v, str) for v in items):
            return [redact_text(str(v)) for v in items]
    return value


def redact_attributes(attributes: Mapping[str, Any] | None) -> dict[str, Any]:
    if not attributes:
        return {}
    return {key: _redact_value(val) for key, val in attributes.items() if key not in SENSITIVE_KEYS}


class RedactingSpanProcessor(SpanProcessor):
    """Scrub span names, attributes, and event attributes when a span ends.

    It must be registered *before* the exporting processor so the exporter only ever sees
    the scrubbed copy.
    """

    def on_start(self, span: Span, parent_context: Context | None = None) -> None:
        return None

    def on_end(self, span: ReadableSpan) -> None:
        # The SDK passes one ReadableSpan instance to every processor in order, and its
        # attribute container is frozen once the span ends. Swapping in scrubbed copies of
        # the private fields is the only way to redact in-process before the exporter runs.
        span._attributes = redact_attributes(span.attributes)
        span._name = redact_text(span.name)
        if span.events:
            span._events = tuple(
                Event(e.name, redact_attributes(e.attributes), e.timestamp) for e in span.events
            )

    def shutdown(self) -> None:
        return None

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True
