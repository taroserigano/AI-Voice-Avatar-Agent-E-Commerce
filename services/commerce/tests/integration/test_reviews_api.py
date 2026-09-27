from __future__ import annotations

import re
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce.auth.models import User
from commerce.catalog.models import Product
from commerce.reviews.models import Review
from commerce.seed.reviews import SAMPLE_REVIEWERS, seed_sample_reviews

from .test_orders_api import _make_order

pytestmark = pytest.mark.integration

ARC = "sonora-arc-wireless-headphones"
CHAIR = "summit-forge-camp-chair"


def _pid(db: Session, slug: str) -> str:
    pid = db.scalar(select(Product.id).where(Product.slug == slug))
    assert pid is not None
    return str(pid)


def _review(client: TestClient, product_id: str, **body: object) -> dict:  # type: ignore[type-arg]
    resp = client.put(f"/v1/products/{product_id}/reviews/mine", json=body)
    assert resp.status_code == 200, resp.text
    return resp.json()  # type: ignore[no-any-return]


def test_reviews_require_sign_in(app, db: Session) -> None:  # type: ignore[no-untyped-def]
    anon = TestClient(app)
    url = f"/v1/products/{_pid(db, ARC)}/reviews"
    assert anon.get(url).status_code == 401
    assert anon.put(f"{url}/mine", json={"rating": 5}).status_code == 401
    assert anon.delete(f"{url}/mine").status_code == 401


def test_review_updates_product_rating_everywhere(
    alice: TestClient, bob: TestClient, db: Session
) -> None:
    pid = _pid(db, ARC)
    _review(alice, pid, rating=5, title="Great", body="Lovely sound.")
    _review(bob, pid, rating=2)

    detail = alice.get(f"/v1/products/{pid}").json()
    assert (detail["rating_average"], detail["rating_count"]) == (3.5, 2)

    listing = alice.get(
        "/v1/products", params={"category": "electronics", "brand": "Sonora Audio"}
    ).json()
    arc = next(i for i in listing["items"] if i["id"] == pid)
    assert (arc["rating_average"], arc["rating_count"]) == (3.5, 2)
    unrated = next(i for i in listing["items"] if i["id"] != pid)
    assert (unrated["rating_average"], unrated["rating_count"]) == (None, 0)

    summary = alice.get(f"/v1/products/{pid}/reviews").json()["summary"]
    assert summary["average"] == 3.5
    assert summary["distribution"] == [
        {"stars": 5, "count": 1},
        {"stars": 4, "count": 0},
        {"stars": 3, "count": 0},
        {"stars": 2, "count": 1},
        {"stars": 1, "count": 0},
    ]


def test_resubmitting_edits_the_one_review_instead_of_adding_another(
    alice: TestClient, db: Session
) -> None:
    pid = _pid(db, ARC)
    first = _review(alice, pid, rating=3, body="Fine.")
    # A retry or double submit, then an edit: still exactly one review.
    _review(alice, pid, rating=3, body="Fine.")
    edited = _review(alice, pid, rating=4, body="Grew on me.")

    assert edited["id"] == first["id"]
    page = alice.get(f"/v1/products/{pid}/reviews").json()
    assert page["total"] == 1
    assert page["my_review"]["rating"] == 4
    assert page["my_review"]["body"] == "Grew on me."


def test_author_comes_from_the_session_not_the_body(
    alice: TestClient, bob: TestClient, db: Session
) -> None:
    pid = _pid(db, ARC)
    bob_user_id = str(
        db.scalar(
            select(Review.user_id).where(Review.id == uuid.UUID(_review(bob, pid, rating=1)["id"]))
        )
    )
    # Alice tries to write as Bob and to mark her review as seeded sample content.
    mine = _review(alice, pid, rating=5, user_id=bob_user_id, is_sample=True, author_name="Bob C.")

    assert mine["author_name"] == "Alice R."
    assert mine["is_sample"] is False
    bobs = next(r for r in bob.get(f"/v1/products/{pid}/reviews").json()["items"] if r["is_mine"])
    assert bobs["rating"] == 1


def test_a_shopper_can_only_delete_their_own_review(
    alice: TestClient, bob: TestClient, db: Session
) -> None:
    pid = _pid(db, ARC)
    _review(alice, pid, rating=5)

    assert bob.delete(f"/v1/products/{pid}/reviews/mine").status_code == 204
    page = alice.get(f"/v1/products/{pid}/reviews").json()
    assert page["total"] == 1 and page["items"][0]["is_mine"] is True
    assert bob.get(f"/v1/products/{pid}/reviews").json()["items"][0]["is_mine"] is False

    assert alice.delete(f"/v1/products/{pid}/reviews/mine").status_code == 204
    assert alice.get(f"/v1/products/{pid}/reviews").json()["total"] == 0
    assert alice.get(f"/v1/products/{pid}").json()["rating_count"] == 0


@pytest.mark.parametrize(
    "body",
    [
        {"rating": 0},
        {"rating": 6},
        {"rating": 4.5},
        {},
        {"rating": 5, "title": "x" * 121},
        {"rating": 5, "body": "x" * 2001},
    ],
)
def test_invalid_reviews_are_rejected(alice: TestClient, db: Session, body: dict) -> None:  # type: ignore[type-arg]
    resp = alice.put(f"/v1/products/{_pid(db, ARC)}/reviews/mine", json=body)
    assert resp.status_code == 422


def test_blank_text_is_stored_as_no_text(alice: TestClient, db: Session) -> None:
    review = _review(alice, _pid(db, ARC), rating=4, title="   ", body="\n  ok \x07 ")
    assert review["title"] is None
    assert review["body"] == "ok"


def test_unknown_product_is_404(alice: TestClient) -> None:
    missing = uuid.uuid4()
    assert alice.get(f"/v1/products/{missing}/reviews").status_code == 404
    assert alice.put(f"/v1/products/{missing}/reviews/mine", json={"rating": 5}).status_code == 404


def test_verified_purchase_reflects_paid_orders(
    alice: TestClient, bob: TestClient, db: Session
) -> None:
    pid = _pid(db, ARC)
    _make_order(db, "alice@example.com")  # Alice bought the Arc headphones; Bob didn't.
    assert _review(alice, pid, rating=5)["verified_purchase"] is True
    assert _review(bob, pid, rating=5)["verified_purchase"] is False


def test_top_rated_sort_puts_best_reviewed_first(
    alice: TestClient, bob: TestClient, db: Session
) -> None:
    _review(alice, _pid(db, CHAIR), rating=5)
    _review(bob, _pid(db, CHAIR), rating=4)
    _review(alice, _pid(db, "summit-forge-headlamp"), rating=3)

    items = alice.get("/v1/products", params={"category": "outdoor", "sort": "top_rated"}).json()[
        "items"
    ]
    assert [i["title"] for i in items[:2]] == [
        "Folding Camp Chair",
        "Trailbeam Rechargeable Headlamp",
    ]
    assert items[2]["rating_count"] == 0


def test_review_sort_orders(alice: TestClient, bob: TestClient, db: Session) -> None:
    pid = _pid(db, ARC)
    _review(alice, pid, rating=2)
    _review(bob, pid, rating=5)
    url = f"/v1/products/{pid}/reviews"
    assert [r["rating"] for r in alice.get(url, params={"sort": "highest"}).json()["items"]] == [
        5,
        2,
    ]
    assert [r["rating"] for r in alice.get(url, params={"sort": "lowest"}).json()["items"]] == [
        2,
        5,
    ]


def test_reviews_can_be_filtered_to_one_star_rating(
    alice: TestClient, bob: TestClient, db: Session
) -> None:
    pid = _pid(db, ARC)
    _review(alice, pid, rating=2)
    _review(bob, pid, rating=5)
    url = f"/v1/products/{pid}/reviews"
    fives = alice.get(url, params={"rating": 5}).json()
    assert [r["rating"] for r in fives["items"]] == [5]
    assert fives["total"] == 1 and fives["summary"]["count"] == 2  # the summary stays whole
    assert alice.get(url, params={"rating": 3}).json()["items"] == []
    assert alice.get(url, params={"rating": 6}).status_code == 422


def test_sample_reviews_are_labeled_and_seeding_is_repeatable(
    alice: TestClient, db: Session
) -> None:
    created = seed_sample_reviews(db)
    db.commit()
    assert created > 0
    assert seed_sample_reviews(db) == 0
    db.commit()

    pid = _pid(db, ARC)
    page = alice.get(f"/v1/products/{pid}/reviews", params={"page_size": 50}).json()
    assert page["total"] >= 2
    assert all(r["is_sample"] and not r["is_mine"] for r in page["items"])
    assert alice.get(f"/v1/products/{pid}").json()["rating_count"] == page["total"]
    # Shown as "First L.", and a seeded row never reads as edited.
    assert all(re.fullmatch(r"[A-Z][a-z]+ [A-Z]\.", r["author_name"]) for r in page["items"])
    assert all(r["created_at"] == r["updated_at"] for r in page["items"])


def _samples(db: Session) -> dict[tuple[uuid.UUID, uuid.UUID], tuple[object, ...]]:
    db.expire_all()
    return {
        (r.product_id, r.user_id): (r.id, r.rating, r.title, r.body, r.created_at)
        for r in db.scalars(select(Review).where(Review.is_sample.is_(True)))
    }


def test_reseeding_refreshes_sample_reviews_in_place_and_never_touches_real_ones(
    alice: TestClient, db: Session
) -> None:
    seed_sample_reviews(db)
    db.commit()
    before = _samples(db)
    pid = uuid.UUID(_pid(db, ARC))
    mine = _review(alice, str(pid), rating=2, title="Mine", body="My own words.")

    # Make the table look like an older seed: stale template text on one row, a row that
    # is missing, and a sample row the current seed doesn't produce.
    arc = sorted(k for k in before if k[0] == pid)
    stale, missing = (db.get(Review, before[k][0]) for k in arc[:2])
    assert stale is not None and missing is not None
    stale.rating, stale.body = 5, "The item feels well made and it arrived quickly."
    db.delete(missing)
    reviewers = {k[1] for k in arc}
    spare = db.scalar(
        select(User.id).where(
            User.email.in_([email for email, _ in SAMPLE_REVIEWERS]), User.id.not_in(reviewers)
        )
    )
    db.add(Review(product_id=pid, user_id=spare, rating=5, body="Five stars.", is_sample=True))
    db.commit()

    assert seed_sample_reviews(db) == 1  # only the missing row is created again
    db.commit()
    after = _samples(db)
    assert after.keys() == before.keys()  # the extra sample row is gone, no duplicates
    for key, (review_id, *content) in after.items():
        assert content[:3] == list(before[key][1:4])  # text and rating restored
        if key != arc[1]:
            assert review_id == before[key][0]  # refreshed in place, not re-inserted

    real = db.get(Review, uuid.UUID(mine["id"]))
    assert real is not None and not real.is_sample
    assert (real.rating, real.title, real.body) == (2, "Mine", "My own words.")

    # Running it again changes nothing.
    assert seed_sample_reviews(db) == 0
    db.commit()
    assert _samples(db) == after


def test_sample_reviews_suit_the_product(alice: TestClient, db: Session) -> None:
    seed_sample_reviews(db)
    db.commit()
    milk = db.scalar(select(Product.id).where(Product.slug == "serigan-mart-kitchen-whole-milk"))
    page = alice.get(f"/v1/products/{milk}/reviews", params={"page_size": 50}).json()
    text = " ".join(f"{r['title']} {r['body']}" for r in page["items"]).lower()
    assert page["total"] >= 5
    assert "milk" in text
    assert not re.search(r"colors|well made|device|fabric|battery", text)
