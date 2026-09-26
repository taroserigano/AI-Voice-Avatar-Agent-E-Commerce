"""Test environment. Set before anything reads retrieval settings."""

from __future__ import annotations

import os
import uuid

# Always the local Qdrant from `pnpm local:up` unless a test server is named explicitly:
# integration tests create and drop collections, so they never touch QDRANT_URL's server.
os.environ["QDRANT_URL"] = os.environ.get("RETRIEVAL_TEST_QDRANT_URL", "http://127.0.0.1:6333")
os.environ["QDRANT_API_KEY"] = os.environ.get("RETRIEVAL_TEST_QDRANT_API_KEY", "")
# A throwaway suffix per run: its own collections.
os.environ["SEARCH_ENV"] = f"test-{uuid.uuid4().hex[:8]}"
