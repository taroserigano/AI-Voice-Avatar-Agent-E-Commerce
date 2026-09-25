"""Shared OpenTelemetry setup for every Python service and worker.

Every service calls :func:`setup_telemetry` once at startup. It configures traces, metrics,
and JSON logs that carry the trace ID, all exported over OTLP/HTTP to the local OTel
Collector. The collector removes personal data and samples; this package is the first line
of defense (see :mod:`ai_commerce_telemetry.redaction`).
"""

from ai_commerce_telemetry.labels import SpanLabels, customer_hash, set_span_labels
from ai_commerce_telemetry.redaction import redact_text
from ai_commerce_telemetry.setup import TelemetryHandles, setup_telemetry

__all__ = [
    "SpanLabels",
    "TelemetryHandles",
    "customer_hash",
    "redact_text",
    "set_span_labels",
    "setup_telemetry",
]
