"""Test environment. Set before any ``commerce`` import reads settings."""

from __future__ import annotations

import os
import uuid

os.environ["APP_ENV"] = "test"
# Always the test database (integration tests truncate tables), never the dev database,
# even when COMMERCE_DATABASE_URL points at a hosted one.
os.environ["COMMERCE_DATABASE_URL"] = os.environ.get(
    "COMMERCE_TEST_DATABASE_URL",
    "postgresql+psycopg://commerce:commerce@localhost:5432/commerce_test",
)
os.environ.setdefault("OPENSEARCH_URL", "http://localhost:9200")
# A throwaway suffix per run: its own OpenSearch index and (if configured) Pinecone namespace.
os.environ["SEARCH_ENV"] = f"test-{uuid.uuid4().hex[:8]}"
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = ""
os.environ["SESSION_SECRET"] = "test-session-secret-0123456789"
