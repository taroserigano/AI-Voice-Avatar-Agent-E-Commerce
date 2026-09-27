"""Return quotes and confirmation: exact money, one return per quote, and only the customer.

The scenario test prices every seeded return conversation through the API and compares it with
the reference policy in the assistant eval oracle, to the cent.
"""

from __future__ import annotations

import json
import uuid
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from commerce.auth.models import User
from commerce.config import get_settings
from commerce.db import utcnow
from commerce.payments.models import PaymentAttempt
from commerce.returns.models import RefundAttempt, ReturnQuote, ReturnRequest
from commerce.seed.catalog import PRODUCTS
from commerce.seed.orders import DEV_ORDERS, order_id
from commerce.seed.run import seed_dev_orders
from tests.integration.test_order_history_api import seed_history
from tests.unit import test_assistant_scenarios as oracle

pytestmark = pytest.mark.integration

RETURNS = [
    json.loads(line)
    for line in (Path(__file__).resolve().parents[4] / "evals" / "assistant" / "returns.jsonl")
    .read_text(encoding="utf-8")
    .splitlines()
    if line.strip()
]
PERISHABLE = {
    p.slug
    for p in PRODUCTS
    if p.category in ("dairy-eggs", "produce", "meat-seafood", "bakery", "frozen")
}


@pytest.fixture
def seeded(db: Session) -> None:
    seed_dev_orders(db)
    db.commit()
    seed_history(db)


def _line_id(order_key: str, slug: str) -> str:
    built = oracle.ORDERS[order_key]
    return str(next(ln.id for ln in built.lines if ln.product.slug == slug))


def _quote(client: TestClient, order_key: str, lines: list[tuple[str, int]], reason: str) -> Any:
    return client.post(
        "/v1/returns/quote",
        json={
            "order_id": str(order_id(order_key)),
            "lines": [{"order_line_id": _line_id(order_key, s), "quantity": q} for s, q in lines],
            "reason": reason,
        },
    )


def _client_for(app, email: str) -> TestClient:  # type: ignore[no-untyped-def]
    from tests.integration.conftest import sign_in

    return sign_in(TestClient(app), email)


def _scenarios() -> list[dict[str, Any]]:
    return [
        s
        for s in RETURNS
        if "outcome" in s
        and s["outcome"]["reason"] != "invalid_request"
        and (s["outcome"].get("lines") or s["outcome"].get("line"))
    ]


@pytest.mark.parametrize("scenario", _scenarios(), ids=lambda s: s["id"])
def test_quotes_match_the_reference_policy(app, seeded: None, scenario: dict[str, Any]) -> None:  # type: ignore[no-untyped-def]
    outcome = scenario["outcome"]
    slugs = outcome.get("lines") or [outcome["line"]]
    qty = outcome.get("quantity", 1)
    reason = "spoiled_or_expired" if set(slugs) <= PERISHABLE else "no_longer_needed"
    client = _client_for(app, scenario["user"])
    resp = _quote(client, scenario["order"], [(s, qty) for s in slugs], reason)
    if outcome["eligible"]:
        assert resp.status_code == 201, resp.text
        quote = resp.json()
        assert quote["total_refund_minor"] == outcome["refund_minor"], scenario["id"]
        assert (quote["shipping_refund_minor"] > 0) == outcome["shipping_refunded"], scenario["id"]
        if outcome.get("refund_timing") and len(slugs) == 1:
            assert quote["lines"][0]["refund_timing"] == outcome["refund_timing"]
        assert quote["status"] == "open" and quote["refund_destination"]["card_last4"]
    elif outcome["reason"] == "not_owner":
        assert resp.status_code == 404
    else:
        assert resp.status_code == 422, resp.text
        assert {p["reason"] for p in resp.json()["problems"]} == {outcome["reason"]}, scenario["id"]


def _mint(client: TestClient, quote_id: str) -> str:
    resp = client.post(f"/v1/returns/quotes/{quote_id}/confirmation")
    assert resp.status_code == 200, resp.text
    return str(resp.json()["confirmation_token"])


def _confirm(client: TestClient, quote_id: str, token: str, key: str | None = None) -> Any:
    return client.post(
        "/v1/returns/confirm",
        json={"quote_id": quote_id, "confirmation_token": token},
        headers={"Idempotency-Key": key or f"idem-{uuid.uuid4()}"},
    )


def test_confirming_twice_creates_one_return(alice: TestClient, db: Session, seeded: None) -> None:
    quote = _quote(alice, "alice-pens", [("quillmark-gel-pens-12pk", 1)], "no_longer_needed").json()
    token = _mint(alice, quote["id"])
    first = _confirm(alice, quote["id"], token, "idem-double-click")
    assert first.status_code == 201, first.text
    again = _confirm(alice, quote["id"], token, "idem-double-click")
    assert again.status_code == 200
    assert again.json()["return"]["id"] == first.json()["return"]["id"]
    assert first.json()["label"]["simulated"] is True
    assert (
        db.scalar(
            select(func.count())
            .select_from(ReturnRequest)
            .where(ReturnRequest.operation_key == f"quote:{quote['id']}")
        )
        == 1
    )


def test_tampered_expired_and_stale_quotes_create_nothing(
    alice: TestClient, db: Session, seeded: None
) -> None:
    q1 = _quote(alice, "alice-apparel", [("driftwood-organic-tee", 1)], "no_longer_needed").json()
    _mint(alice, q1["id"])
    assert _confirm(alice, q1["id"], "x" * 43).status_code == 403  # wrong token

    q2 = _quote(alice, "alice-apparel", [("driftwood-organic-tee", 1)], "no_longer_needed").json()
    token2 = _mint(alice, q2["id"])
    db.execute(
        update(ReturnQuote)
        .where(ReturnQuote.id == q2["id"])
        .values(expires_at=utcnow() - timedelta(seconds=1))
    )
    db.commit()
    assert _confirm(alice, q2["id"], token2).status_code == 410  # expired

    # Two quotes for all 3 tees: confirming one changes what the other would refund.
    qa = _quote(alice, "alice-apparel", [("driftwood-organic-tee", 3)], "no_longer_needed").json()
    qb = _quote(alice, "alice-apparel", [("driftwood-organic-tee", 3)], "no_longer_needed").json()
    ta, tb = _mint(alice, qa["id"]), _mint(alice, qb["id"])
    assert _confirm(alice, qa["id"], ta).status_code == 201
    stale = _confirm(alice, qb["id"], tb)
    assert stale.status_code == 409, stale.text
    # A token only works for its own quote.
    qc = _quote(alice, "alice-pens", [("quillmark-gel-pens-12pk", 1)], "no_longer_needed").json()
    _mint(alice, qc["id"])
    assert _confirm(alice, qc["id"], tb).status_code == 403
    assert (
        db.scalar(
            select(func.count())
            .select_from(ReturnRequest)
            .where(ReturnRequest.operation_key.like("quote:%"))
        )
        == 1
    )


def test_the_assistant_can_quote_but_never_confirm(
    app,
    alice: TestClient,
    db: Session,
    seeded: None,  # type: ignore[no-untyped-def]
) -> None:
    user = db.scalar(select(User).where(User.email == "alice@example.com"))
    assert user is not None
    assistant = TestClient(
        app,
        headers={
            "Authorization": f"Bearer {get_settings().assistant_service_token}",
            "X-On-Behalf-Of": str(user.id),
        },
    )
    quote = _quote(assistant, "alice-pens", [("quillmark-gel-pens-12pk", 1)], "no_longer_needed")
    assert quote.status_code == 201
    qid = quote.json()["id"]
    assert db.get(ReturnQuote, uuid.UUID(qid)).created_via == "assistant"  # type: ignore[union-attr]
    assert assistant.post(f"/v1/returns/quotes/{qid}/confirmation").status_code == 401
    token = _mint(alice, qid)
    assert _confirm(assistant, qid, token).status_code == 401
    assert _confirm(alice, qid, token).status_code == 201


def test_customers_cannot_touch_each_others_returns(
    alice: TestClient, bob: TestClient, seeded: None
) -> None:
    assert _quote(bob, "alice-pens", [("quillmark-gel-pens-12pk", 1)], "other").status_code == 404
    quote = _quote(alice, "alice-pens", [("quillmark-gel-pens-12pk", 1)], "other").json()
    assert bob.get(f"/v1/returns/quotes/{quote['id']}").status_code == 404
    assert bob.post(f"/v1/returns/quotes/{quote['id']}/confirmation").status_code == 404
    token = _mint(alice, quote["id"])
    assert _confirm(bob, quote["id"], token).status_code == 404


def test_perishables_need_a_quality_reason_and_refund_at_once(
    alice: TestClient, db: Session, seeded: None
) -> None:
    built = oracle.ORDERS["alice-groceries-recent"]
    slug = next(ln.product.slug for ln in built.lines if ln.product.slug in PERISHABLE)
    bad = _quote(alice, "alice-groceries-recent", [(slug, 1)], "no_longer_needed")
    assert bad.status_code == 422 and bad.json()["problems"][0]["reason"] == "perishable_reason"
    quote = _quote(alice, "alice-groceries-recent", [(slug, 1)], "spoiled_or_expired").json()
    assert quote["needs_shipping"] is False
    done = _confirm(alice, quote["id"], _mint(alice, quote["id"])).json()
    assert done["refunded_now_minor"] == quote["total_refund_minor"]
    assert done["return"]["status"] == "closed" and done["label"] is None


def test_simulated_journey_refunds_each_stage_once(
    alice: TestClient, db: Session, seeded: None
) -> None:
    quote = _quote(alice, "alice-headphones", [("sonora-arc-wireless-headphones", 1)], "defective")
    assert quote.status_code == 201, quote.text
    q = quote.json()
    assert q["lines"][0]["refund_timing"] == "after_inspection"
    ret = _confirm(alice, q["id"], _mint(alice, q["id"])).json()["return"]
    payment_before = db.scalar(
        select(PaymentAttempt.refunded_minor).where(
            PaymentAttempt.order_id == order_id("alice-headphones")
        )
    )

    scan = alice.post(f"/v1/returns/{ret['id']}/dev-advance", json={"event": "carrier_scan"}).json()
    assert scan["status"] == "in_transit" and scan["refund"] is None
    done = alice.post(f"/v1/returns/{ret['id']}/dev-advance", json={"event": "inspect_pass"}).json()
    assert done["status"] == "closed" and done["refund"]["amount_minor"] == q["total_refund_minor"]
    # Repeating (or going back) refunds nothing more.
    alice.post(f"/v1/returns/{ret['id']}/dev-advance", json={"event": "inspect_pass"})
    alice.post(f"/v1/returns/{ret['id']}/dev-advance", json={"event": "warehouse_receive"})
    db.expire_all()
    refunds = db.scalars(select(RefundAttempt).where(RefundAttempt.return_id == ret["id"])).all()
    assert sum(r.amount_minor for r in refunds) == q["total_refund_minor"]
    payment_after = db.scalar(
        select(PaymentAttempt.refunded_minor).where(
            PaymentAttempt.order_id == order_id("alice-headphones")
        )
    )
    assert (payment_after or 0) - (payment_before or 0) == q["total_refund_minor"]
    returns = alice.get("/v1/returns").json()
    listed = {r["id"]: r for r in returns}
    assert listed[ret["id"]]["order_id"] == str(order_id("alice-headphones"))


def test_every_scenario_order_is_covered() -> None:
    assert {s["order"] for s in _scenarios()} <= {spec.key for spec in DEV_ORDERS}
