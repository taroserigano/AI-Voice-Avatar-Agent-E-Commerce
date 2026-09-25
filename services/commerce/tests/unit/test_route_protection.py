from __future__ import annotations

import pytest
from fastapi import APIRouter

from commerce.main import (
    PUBLIC_ROUTES,
    assert_routes_protected,
    create_app,
    iter_routes,
    route_requires_user,
)


def test_route_walk_sees_routes_inside_included_routers() -> None:
    # Guards against the walk passing vacuously (FastAPI 0.14x nests included routers).
    found = {(m, r.path) for r in iter_routes(create_app()) for m in r.methods}
    assert {
        ("GET", "/v1/cart"),
        ("PUT", "/v1/cart/items"),
        ("GET", "/v1/orders/{order_id}"),
    } <= found
    assert ("POST", "/v1/auth/sign-in") in found


def test_every_non_public_route_requires_a_session() -> None:
    checked = 0
    for route in iter_routes(create_app()):
        for method in route.methods:
            if (method, route.path) not in PUBLIC_ROUTES:
                assert route_requires_user(route.dependant), f"{method} {route.path}"
                checked += 1
    assert checked >= 7


def test_public_list_is_only_auth_and_health() -> None:
    for _, path in PUBLIC_ROUTES:
        assert path == "/healthz" or path.startswith("/v1/auth/")


@pytest.mark.parametrize("prefix", ["", "/v1/nested"])
def test_startup_fails_when_a_route_forgets_the_session_check(prefix: str) -> None:
    app = create_app()
    leaky = APIRouter()

    @leaky.get("/leaky")
    def leaky_route() -> dict[str, str]:
        return {}

    app.include_router(leaky, prefix=prefix or "/v1")
    with pytest.raises(RuntimeError, match="missing the session check"):
        assert_routes_protected(app)
