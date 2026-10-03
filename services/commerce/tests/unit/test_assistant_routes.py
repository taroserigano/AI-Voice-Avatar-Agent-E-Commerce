"""The assistant's allowlist names real routes, and its customer-data reads are read-only."""

from __future__ import annotations

from commerce.auth.deps import ASSISTANT_ROUTES
from commerce.main import create_app, iter_routes, route_requires_user


def test_every_allowlisted_route_exists_and_requires_a_signed_in_customer() -> None:
    routes = {(m, r.path): r for r in iter_routes(create_app()) for m in r.methods}
    for key in ASSISTANT_ROUTES:
        # A typo here would silently lock the assistant out (or in, after a rename).
        assert key in routes, key
        assert route_requires_user(routes[key].dependant), key


def test_the_assistant_reads_reviews_cases_activity_and_cart_but_never_writes_them() -> None:
    assert {
        ("GET", "/v1/products/{product_id}/reviews"),
        ("GET", "/v1/support/cases"),
        ("GET", "/v1/activity"),
        ("GET", "/v1/cart"),
    } <= ASSISTANT_ROUTES
    # Writing or deleting a review stays the customer's own browser action.
    assert not {(m, p) for m, p in ASSISTANT_ROUTES if p.startswith("/v1/products/") and m != "GET"}
    assert not {(m, p) for m, p in ASSISTANT_ROUTES if p.startswith("/v1/activity") and m != "GET"}
