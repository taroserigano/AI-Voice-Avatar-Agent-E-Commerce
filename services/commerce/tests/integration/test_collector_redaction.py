"""The OTel Collector itself strips personal data (the second, central layer).

Runs the real collector image with infra/otel/collector.yaml plus a small override that
writes to a file instead of Grafana, sends it a span and a log containing an email and a
card-like number, and checks what the collector exports. Needs Docker or Podman.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import time
import uuid
from pathlib import Path

import httpx
import pytest

pytestmark = pytest.mark.integration

REPO = Path(__file__).resolve().parents[4]
COLLECTOR_IMAGE = "otel/opentelemetry-collector-contrib:0.161.0"
EMAIL = "canary.person@example.com"
CARD = "4242 4242 4242 4242"
OVERRIDE = """
exporters:
  file/test:
    path: /out/export.jsonl
service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, attributes/drop-pii, transform/redact, batch]
      exporters: [file/test]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, attributes/drop-pii, transform/redact, batch]
      exporters: [file/test]
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [file/test]
"""


def _container_engine() -> str | None:
    """CONTAINER_ENGINE if set, else the first of Docker or Podman that is running."""
    if chosen := os.environ.get("CONTAINER_ENGINE"):
        return chosen
    for engine in ("docker", "podman"):
        if (
            shutil.which(engine)
            and subprocess.run([engine, "info"], capture_output=True).returncode == 0
        ):
            return engine
    return None


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.fixture
def collector(tmp_path: Path):  # type: ignore[no-untyped-def]
    engine = _container_engine()
    if engine is None:
        pytest.skip("neither Docker nor Podman is running")
    (tmp_path / "override.yaml").write_text(OVERRIDE, encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    port = _free_port()
    name = f"otel-redaction-test-{uuid.uuid4().hex[:8]}"
    subprocess.run(
        [
            engine, "run", "-d", "--rm", "--name", name,
            "-e", "OTEL_BASELINE_SAMPLING_PERCENT=100",
            "-p", f"{port}:4318",
            "-v", f"{REPO / 'infra' / 'otel' / 'collector.yaml'}:/etc/otelcol/config.yaml:ro",
            "-v", f"{tmp_path / 'override.yaml'}:/etc/otelcol/override.yaml:ro",
            "-v", f"{out}:/out",
            "--user", "0:0",
            COLLECTOR_IMAGE,
            "--config=/etc/otelcol/config.yaml", "--config=/etc/otelcol/override.yaml",
        ],
        check=True,
        capture_output=True,
    )  # fmt: skip
    base = f"http://127.0.0.1:{port}"
    try:
        for _ in range(60):
            try:
                httpx.post(f"{base}/v1/traces", json={"resourceSpans": []}, timeout=1)
                break
            except httpx.TransportError:
                time.sleep(0.5)
        yield base, out / "export.jsonl"
    finally:
        subprocess.run([engine, "rm", "-f", name], capture_output=True)


def _attr(key: str, value: str) -> dict:  # type: ignore[type-arg]
    return {"key": key, "value": {"stringValue": value}}


def test_collector_removes_emails_and_card_numbers(collector) -> None:  # type: ignore[no-untyped-def]
    base, export_file = collector
    now = time.time_ns()
    span = {
        "traceId": uuid.uuid4().hex,
        "spanId": uuid.uuid4().hex[:16],
        "name": f"lookup {EMAIL}",
        "kind": 2,
        "startTimeUnixNano": str(now),
        "endTimeUnixNano": str(now + 1000),
        "attributes": [
            _attr("url.query", f"q={EMAIL}"),
            _attr("user.email", EMAIL),
            _attr("note", f"card {CARD}"),
            _attr("http.route", "/v1/products"),
        ],
        "events": [{"name": "e", "timeUnixNano": str(now), "attributes": [_attr("detail", EMAIL)]}],
    }
    resource = {"attributes": [_attr("service.name", "redaction-test")]}
    traces = {"resourceSpans": [{"resource": resource, "scopeSpans": [{"spans": [span]}]}]}
    logs = {
        "resourceLogs": [
            {
                "resource": resource,
                "scopeLogs": [
                    {
                        "logRecords": [
                            {
                                "timeUnixNano": str(now),
                                "body": {"stringValue": f"reset for {EMAIL} card {CARD}"},
                                "attributes": [_attr("who", EMAIL)],
                            }
                        ]
                    }
                ],
            }
        ]
    }
    assert httpx.post(f"{base}/v1/traces", json=traces, timeout=5).status_code == 200
    assert httpx.post(f"{base}/v1/logs", json=logs, timeout=5).status_code == 200

    content = ""
    for _ in range(40):
        if export_file.exists():
            content = export_file.read_text(encoding="utf-8")
            if (
                "redaction-test" in content
                and "logRecords" in content
                and "resourceSpans" in content
            ):
                break
        time.sleep(0.5)
    assert "redaction-test" in content, "collector exported nothing"
    assert EMAIL not in content
    assert "canary.person" not in content
    assert "4242" not in content
    assert "user.email" not in content
    assert "[REDACTED_EMAIL]" in content and "[REDACTED_NUMBER]" in content
    assert "/v1/products" in content  # ordinary data passes through
    for line in filter(None, content.splitlines()):
        json.loads(line)
