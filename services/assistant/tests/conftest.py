"""Tests use their own database, never the development one.

``ASSISTANT_TEST_DATABASE_URL`` wins; otherwise the commerce test database (the assistant's
tables live beside the commerce tables, as in development).
"""

from __future__ import annotations

import os

os.environ["APP_ENV"] = "test"
os.environ["ASSISTANT_MODEL_MODE"] = "scripted"
# Tests use the Jev simulator; a real TYPESAFE_API_KEY in .env is never called from tests.
os.environ["TYPESAFE_API_KEY"] = ""
os.environ["ASSISTANT_DATABASE_URL"] = os.environ.get(
    "ASSISTANT_TEST_DATABASE_URL",
    os.environ.get(
        "COMMERCE_TEST_DATABASE_URL",
        "postgresql+psycopg://commerce:commerce@localhost:5432/commerce_test",
    ),
)
