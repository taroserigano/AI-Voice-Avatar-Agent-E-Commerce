"""One-call OpenTelemetry setup: traces, metrics, and JSON logs with trace IDs."""

from __future__ import annotations

import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import MetricReader, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter

from ai_commerce_telemetry.redaction import RedactingSpanProcessor, redact_text


@dataclass
class TelemetryHandles:
    tracer_provider: TracerProvider
    meter_provider: MeterProvider

    def shutdown(self) -> None:
        self.tracer_provider.shutdown()
        self.meter_provider.shutdown()


class JsonLogFormatter(logging.Formatter):
    """One JSON object per line, with the active trace and span IDs, and no personal data."""

    def __init__(self, service_name: str) -> None:
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        span_ctx = trace.get_current_span().get_span_context()
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname.lower(),
            "service": self.service_name,
            "logger": record.name,
            "msg": redact_text(record.getMessage()),
        }
        if span_ctx.is_valid:
            payload["trace_id"] = format(span_ctx.trace_id, "032x")
            payload["span_id"] = format(span_ctx.span_id, "016x")
        extra = getattr(record, "fields", None)
        if isinstance(extra, dict):
            payload.update(
                {k: redact_text(v) if isinstance(v, str) else v for k, v in extra.items()}
            )
        if record.exc_info:
            payload["exc"] = redact_text(self.formatException(record.exc_info))
        return json.dumps(payload, default=str)


def configure_json_logging(service_name: str, level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter(service_name))
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
    # Uvicorn installs its own handlers; route them through ours instead.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        lg = logging.getLogger(name)
        lg.handlers[:] = []
        lg.propagate = True


def setup_telemetry(
    service_name: str,
    *,
    environment: str = "dev",
    otlp_endpoint: str | None = None,
    span_exporter: SpanExporter | None = None,
    extra_span_processors: list[SpanProcessor] | None = None,
    metric_readers: list[MetricReader] | None = None,
    log_level: str = "INFO",
    json_logs: bool = True,
) -> TelemetryHandles:
    """Configure global tracer and meter providers.

    ``span_exporter`` / ``metric_readers`` override the OTLP exporters (tests pass in-memory
    ones). With neither an override nor an endpoint, spans are created but not exported.
    """
    resource = Resource.create(
        {
            "service.name": service_name,
            "deployment.environment.name": environment,
        }
    )
    endpoint = otlp_endpoint or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")

    tracer_provider = TracerProvider(resource=resource)
    # Redaction first, so every later processor and exporter sees the scrubbed span.
    tracer_provider.add_span_processor(RedactingSpanProcessor())
    for proc in extra_span_processors or []:
        tracer_provider.add_span_processor(proc)
    if span_exporter is not None:
        tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    elif endpoint:
        tracer_provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{endpoint.rstrip('/')}/v1/traces"))
        )
    trace.set_tracer_provider(tracer_provider)

    readers: list[MetricReader] = list(metric_readers or [])
    if not readers and endpoint:
        readers.append(
            PeriodicExportingMetricReader(
                OTLPMetricExporter(endpoint=f"{endpoint.rstrip('/')}/v1/metrics"),
                export_interval_millis=15000,
            )
        )
    meter_provider = MeterProvider(resource=resource, metric_readers=readers)
    metrics.set_meter_provider(meter_provider)

    if json_logs:
        configure_json_logging(service_name, log_level)
    return TelemetryHandles(tracer_provider=tracer_provider, meter_provider=meter_provider)
