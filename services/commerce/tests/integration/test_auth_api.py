from __future__ import annotations

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from commerce.auth.models import AuthSession
from commerce.auth.sessions import hash_token
from commerce.db import utcnow

pytestmark = pytest.mark.integration


def test_sign_in_sets_a_hardened_session_cookie(client: TestClient) -> None:
    resp = client.post(
        "/v1/auth/sign-in", json={"email": "Alice@Example.com ", "password": "alice-dev-password"}
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "alice@example.com"
    cookie = resp.headers["set-cookie"].lower()
    assert "ac_session=" in cookie
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert "max-age=" in cookie
    assert client.get("/v1/auth/me").status_code == 200


def test_wrong_password_and_unknown_account_get_the_same_answer(client: TestClient) -> None:
    wrong = client.post("/v1/auth/sign-in", json={"email": "alice@example.com", "password": "x"})
    unknown = client.post("/v1/auth/sign-in", json={"email": "who@example.com", "password": "x"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json() == {"detail": "Wrong email or password."}


def test_repeated_failures_are_rate_limited_even_with_the_right_password(
    client: TestClient,
) -> None:
    for _ in range(5):
        client.post("/v1/auth/sign-in", json={"email": "bob@example.com", "password": "nope"})
    resp = client.post(
        "/v1/auth/sign-in", json={"email": "bob@example.com", "password": "bob-dev-password"}
    )
    assert resp.status_code == 429
    assert "retry-after" in resp.headers
    # Other accounts are unaffected.
    ok = client.post(
        "/v1/auth/sign-in", json={"email": "alice@example.com", "password": "alice-dev-password"}
    )
    assert ok.status_code == 200


def test_sign_out_ends_the_session_on_the_server(alice: TestClient) -> None:
    token = alice.cookies.get("ac_session")
    assert alice.post("/v1/auth/sign-out").status_code == 204
    # Replaying the old cookie must not work, even if a browser kept it.
    replay = TestClient(alice.app, cookies={"ac_session": token})
    assert replay.get("/v1/cart").status_code == 401


def test_expired_session_is_rejected(alice: TestClient, db) -> None:  # type: ignore[no-untyped-def]
    token = alice.cookies.get("ac_session")
    db.execute(
        update(AuthSession)
        .where(AuthSession.token_hash == hash_token(token))
        .values(expires_at=utcnow() - timedelta(seconds=1))
    )
    db.commit()
    assert alice.get("/v1/cart").status_code == 401


def test_session_tokens_are_stored_only_as_hashes(alice: TestClient, db) -> None:  # type: ignore[no-untyped-def]
    token = alice.cookies.get("ac_session")
    rows = db.scalars(select(AuthSession.token_hash)).all()
    assert token not in rows
    assert hash_token(token) in rows


def test_sign_up_creates_a_customer_and_signs_in(client: TestClient) -> None:
    resp = client.post(
        "/v1/auth/sign-up",
        json={"email": "new@example.com", "password": "long-enough-pw", "display_name": "New"},
    )
    assert resp.status_code == 201
    assert resp.json()["role"] == "customer"
    assert client.get("/v1/cart").status_code == 200

    dup = TestClient(client.app).post(
        "/v1/auth/sign-up",
        json={"email": "NEW@example.com", "password": "long-enough-pw", "display_name": "Dup"},
    )
    assert dup.status_code == 409


def test_sign_up_rejects_short_passwords(client: TestClient) -> None:
    resp = client.post(
        "/v1/auth/sign-up",
        json={"email": "s@example.com", "password": "short", "display_name": "S"},
    )
    assert resp.status_code == 422


def test_password_reset_flow_is_single_use_and_ends_old_sessions(
    alice: TestClient, client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    import logging

    caplog.set_level(logging.INFO)
    same = client.post("/v1/auth/forgot-password", json={"email": "nobody@example.com"})
    resp = client.post("/v1/auth/forgot-password", json={"email": "alice@example.com"})
    assert resp.status_code == same.status_code == 202
    assert resp.json() == same.json()

    record = next(r for r in caplog.records if "password reset link" in r.getMessage())
    token = record.fields["reset_url"].split("token=")[1]  # type: ignore[attr-defined]

    done = client.post("/v1/auth/reset-password", json={"token": token, "password": "brand-new-pw"})
    assert done.status_code == 204
    again = client.post(
        "/v1/auth/reset-password", json={"token": token, "password": "other-pw-123"}
    )
    assert again.status_code == 400

    assert alice.get("/v1/cart").status_code == 401  # old session ended
    signed = client.post(
        "/v1/auth/sign-in", json={"email": "alice@example.com", "password": "brand-new-pw"}
    )
    assert signed.status_code == 200


def test_auth_config_labels_development_sign_in(client: TestClient) -> None:
    assert client.get("/v1/auth/config").json()["development_sign_in"] is True
