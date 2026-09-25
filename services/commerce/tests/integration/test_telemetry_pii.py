"""Exit check: a fake email sent through requests never appears in exported traces or logs."""

from __future__ import annotations

import io
import json
import logging

import pytest
from fastapi.testclient import TestClient

from ai_commerce_telemetry.setup import JsonLogFormatter

from .conftest import SPANS

pytestmark = pytest.mark.integration

FAKE_EMAIL = "pii.canary.7731@example.com"


def test_email_never_reaches_exported_spans_or_logs(client: TestClient, alice: TestClient) -> None:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonLogFormatter("commerce-api-test"))
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    try:
        client.post("/v1/auth/sign-in", json={"email": FAKE_EMAIL, "password": "wrong"})
        client.post(
            "/v1/auth/sign-up",
            json={"email": FAKE_EMAIL, "password": "long-enough-pw", "display_name": FAKE_EMAIL},
        )
        client.post("/v1/auth/forgot-password", json={"email": FAKE_EMAIL})
        alice.get("/v1/products", params={"q": FAKE_EMAIL})
        alice.get(f"/v1/products?q={FAKE_EMAIL.replace('@', '%40')}")
    finally:
        root.removeHandler(handler)

    spans = SPANS.get_finished_spans()
    assert spans, "expected the instrumented app to export spans"
    exported = "\n".join(span.to_json() for span in spans)
    logs = stream.getvalue()

    for blob in (exported, logs):
        assert FAKE_EMAIL not in blob
        assert "pii.canary" not in blob
        assert "pii.canary.7731%40" not in blob

    # The spans are still useful: routes, the hashed customer label, and database and
    # OpenSearch client spans are present (one trace covers API -> PostgreSQL/OpenSearch).
    assert "/v1/products" in exported
    assert "app.customer_hash" in exported
    assert any(
        span.attributes and span.attributes.get("db.system") == "postgresql" for span in spans
    )
    assert any(span.name == "search.opensearch" for span in spans)
    for line in filter(None, logs.splitlines()):
        json.loads(line)
