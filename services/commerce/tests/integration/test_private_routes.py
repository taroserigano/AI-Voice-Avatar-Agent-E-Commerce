"""Every private API answers 401 without a session, whatever the web app's redirect does."""

from __future__ import annotations

import re
import uuid

import pytest
from fastapi.testclient import TestClient

from commerce.main import PUBLIC_ROUTES, iter_routes

pytestmark = pytest.mark.integration


def _private_routes(app) -> list[tuple[str, str]]:  # type: ignore[no-untyped-def]
    out = []
    for route in iter_routes(app):
        for method in route.methods:
            if method != "HEAD" and (method, route.path) not in PUBLIC_ROUTES:
                out.append((method, route.path))
    return sorted(out)


def test_there_are_private_routes_to_check(app) -> None:  # type: ignore[no-untyped-def]
    assert len(_private_routes(app)) >= 7


@pytest.mark.parametrize("cookie", [None, "forged-or-stale-token"])
def test_no_valid_session_means_401_on_every_private_route(app, cookie: str | None) -> None:  # type: ignore[no-untyped-def]
    client = TestClient(app, cookies={"ac_session": cookie} if cookie else None)
    for method, path in _private_routes(app):
        url = re.sub(r"\{[^}]+\}", str(uuid.uuid4()), path)
        resp = client.request(method, url, json={})
        assert resp.status_code == 401, f"{method} {path} -> {resp.status_code}"
        assert "Alice" not in resp.text
