"""The assistant reads reviews, and a customer's own support cases, activity, and cart, on that
customer's behalf: only theirs, and read-only."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.integration.conftest import variant_id_for
from tests.integration.test_assistant_identity import _as_assistant, _user
from tests.integration.test_reviews_api import ARC, _pid, _review

pytestmark = pytest.mark.integration


def _open_case(client: TestClient, subject: str) -> str:
    resp = client.post(
        "/v1/support/cases", json={"subject": subject, "summary": f"{subject}, please help"}
    )
    assert resp.status_code == 201, resp.text
    return str(resp.json()["reference"])


def test_assistant_sees_only_the_customers_own_support_cases_and_activity(
    app: FastAPI, db: Session, alice: TestClient, bob: TestClient
) -> None:
    alice_case = _open_case(alice, "Alice's crushed box")
    bob_case = _open_case(bob, "Bob's late parcel")
    as_alice = _as_assistant(app, _user(db, "alice@example.com"))

    cases = as_alice.get("/v1/support/cases")
    assert cases.status_code == 200, cases.text
    assert [c["reference"] for c in cases.json()] == [alice_case]

    activity = as_alice.get("/v1/activity", params={"limit": 10})
    assert activity.status_code == 200, activity.text
    references = [e["data"].get("reference") for e in activity.json()]
    assert alice_case in references and bob_case not in references

    # Bob's assistant gets Bob's, never Alice's.
    as_bob = _as_assistant(app, _user(db, "bob@example.com"))
    assert [c["reference"] for c in as_bob.get("/v1/support/cases").json()] == [bob_case]


def test_assistant_reads_the_customers_own_cart(
    app: FastAPI, db: Session, alice: TestClient
) -> None:
    vid = variant_id_for(db, "sonora-arc-wireless-headphones", "MID")
    assert alice.put("/v1/cart/items", json={"variant_id": vid, "quantity": 2}).status_code == 200

    alice_cart = _as_assistant(app, _user(db, "alice@example.com")).get("/v1/cart").json()
    assert [(i["variant_id"], i["quantity"]) for i in alice_cart["items"]] == [(vid, 2)]
    bob_cart = _as_assistant(app, _user(db, "bob@example.com")).get("/v1/cart").json()
    assert bob_cart["items"] == []


def test_assistant_reads_reviews_but_cannot_write_them(
    app: FastAPI, db: Session, alice: TestClient
) -> None:
    pid = _pid(db, ARC)
    _review(alice, pid, rating=5, title="Great", body="Lovely sound.")
    as_bob = _as_assistant(app, _user(db, "bob@example.com"))

    page = as_bob.get(f"/v1/products/{pid}/reviews", params={"sort": "highest"})
    assert page.status_code == 200, page.text
    body = page.json()
    assert body["summary"]["count"] == 1 and body["my_review"] is None
    assert body["items"][0]["is_mine"] is False
    # The review shows a shortened name, never the author's email.
    assert "alice@example.com" not in page.text

    url = f"/v1/products/{pid}/reviews/mine"
    assert as_bob.put(url, json={"rating": 1}).status_code == 401
    assert as_bob.delete(url).status_code == 401
    assert alice.get(f"/v1/products/{pid}/reviews").json()["summary"]["count"] == 1


def test_top_rated_ranks_every_search_match_not_just_the_first_page(
    app: FastAPI, db: Session, alice: TestClient, bob: TestClient
) -> None:
    as_alice = _as_assistant(app, _user(db, "alice@example.com"))
    params = {"q": "headphones", "page_size": 60}
    matches = as_alice.get("/v1/products", params=params).json()["items"]
    assert len(matches) >= 3
    # The weakest text match gets the best reviews; another gets a poor one.
    best, poor = matches[-1]["id"], matches[0]["id"]
    _review(alice, best, rating=5)
    _review(bob, best, rating=5)
    _review(alice, poor, rating=2)

    top = as_alice.get(
        "/v1/products", params={"q": "headphones", "sort": "top_rated", "page_size": 1}
    ).json()
    assert [i["id"] for i in top["items"]] == [best]
    assert (top["items"][0]["rating_average"], top["items"][0]["rating_count"]) == (5.0, 2)
    assert top["total"] == len(matches)

    ranked = as_alice.get(
        "/v1/products", params={"q": "headphones", "sort": "top_rated", "page_size": 60}
    ).json()["items"]
    assert ranked[0]["id"] == best
    reviewed = [i["id"] for i in ranked if i["rating_count"]]
    assert set(reviewed) == {best, poor}
