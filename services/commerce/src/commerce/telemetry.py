from __future__ import annotations

from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.urllib3 import URLLib3Instrumentor
from opentelemetry.sdk.trace import SpanProcessor

from ai_commerce_telemetry import TelemetryHandles, setup_telemetry
from commerce.config import get_settings
from commerce.db import get_engine

_handles: TelemetryHandles | None = None


def init_telemetry(
    service_name: str, extra_span_processors: list[SpanProcessor] | None = None
) -> TelemetryHandles:
    """Set up OTel once per process and instrument the libraries we call out through."""
    global _handles
    if _handles is not None:
        return _handles
    settings = get_settings()
    _handles = setup_telemetry(
        service_name,
        environment=settings.app_env,
        otlp_endpoint=settings.otel_exporter_otlp_endpoint,
        extra_span_processors=extra_span_processors,
        log_level=settings.log_level,
    )
    SQLAlchemyInstrumentor().instrument(engine=get_engine())
    HTTPXClientInstrumentor().instrument()
    RedisInstrumentor().instrument()
    # opensearch-py and parts of the Pinecone client go through urllib3.
    URLLib3Instrumentor().instrument()
    return _handles
