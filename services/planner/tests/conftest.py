"""Test environment: never call a real model unless a test opts in."""

from __future__ import annotations

import os

os.environ["APP_ENV"] = "test"
os.environ["PLANNER_PROVIDER"] = os.environ.get("PLANNER_TEST_PROVIDER", "scripted")
