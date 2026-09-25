from __future__ import annotations

import io
import json
import logging

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from ai_commerce_telemetry.redaction import RedactingSpanProcessor, redact_text
from ai_commerce_telemetry.setup import JsonLogFormatter

EMAIL = "jane.doe+test@example.com"


def test_redact_text_masks_emails_encoded_emails_and_card_numbers() -> None:
    text = f"q={EMAIL} alt=jane%40example.org card=4242 4242 4242 4242 order=12345"
    out = redact_text(text)
    assert "jane" not in out
    assert "4242" not in out
    assert "order=12345" in out  # short numbers are not card-like


def test_span_processor_scrubs_before_the_exporter_sees_the_span() -> None:
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(RedactingSpanProcessor())
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("test")

    with tracer.start_as_current_span(f"GET /search {EMAIL}") as span:
        span.set_attribute("url.query", f"q={EMAIL}")
        span.set_attribute("user.email", EMAIL)
        span.set_attribute("tags", ["ok", EMAIL])
        span.add_event("note", {"detail": f"reset for {EMAIL}"})
        try:
            raise ValueError(f"no account for {EMAIL}")
        except ValueError as exc:
            span.record_exception(exc)

    dumped = exporter.get_finished_spans()[0].to_json()
    assert EMAIL not in dumped
    assert "jane.doe" not in dumped
    assert "user.email" not in dumped


def test_json_logs_carry_no_email_and_are_one_object_per_line() -> None:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonLogFormatter("test-svc"))
    logger = logging.getLogger("redaction-test")
    logger.addHandler(handler)
    logger.propagate = False
    logger.warning("sign-in failed for %s", EMAIL, extra={"fields": {"who": EMAIL, "n": 3}})

    line = stream.getvalue().strip()
    record = json.loads(line)
    assert EMAIL not in line
    assert record["service"] == "test-svc" and record["n"] == 3
