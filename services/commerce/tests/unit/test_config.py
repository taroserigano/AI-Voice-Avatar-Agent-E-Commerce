"""Database settings: the shared .env must never point this app at another project's DB."""

from __future__ import annotations

import pytest

from commerce.config import Settings


def test_ignores_the_generic_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("COMMERCE_DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgres://other:pw@other-project.example/otherdb")
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert "other-project" not in settings.database_url


@pytest.mark.parametrize("scheme", ["postgres", "postgresql"])
def test_hosted_urls_use_the_psycopg_driver(monkeypatch: pytest.MonkeyPatch, scheme: str) -> None:
    monkeypatch.setenv(
        "COMMERCE_DATABASE_URL", f"{scheme}://u:pw@db.example.com:5432/postgres?sslmode=require"
    )
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.database_url == (
        "postgresql+psycopg://u:pw@db.example.com:5432/postgres?sslmode=require"
    )
