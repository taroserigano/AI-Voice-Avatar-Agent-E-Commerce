from __future__ import annotations

from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from ai_commerce_telemetry import TelemetryHandles, setup_telemetry
from assistant.config import get_settings

_handles: TelemetryHandles | None = None


def init_telemetry(service_name: str) -> TelemetryHandles:
    """Set up OTel once per process; commerce API calls carry the trace across services."""
    global _handles
    if _handles is not None:
        return _handles
    settings = get_settings()
    _handles = setup_telemetry(
        service_name,
        environment=settings.app_env,
        otlp_endpoint=settings.otel_exporter_otlp_endpoint,
        log_level=settings.log_level,
    )
    HTTPXClientInstrumentor().instrument()
    return _handles
