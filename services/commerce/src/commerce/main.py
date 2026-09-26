"""Commerce API.

Every route requires a signed-in session except the ones in ``PUBLIC_ROUTES``. The check
lives on each router (``require_user``), and :func:`assert_routes_protected` refuses to
start the app if a new route forgets it.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from fastapi import Depends, FastAPI
from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from commerce.auth.deps import require_user
from commerce.auth.routes import router as auth_router
from commerce.cart.routes import router as cart_router
from commerce.catalog.routes import router as catalog_router
from commerce.config import get_settings
from commerce.orders.routes import router as orders_router

# (method, path) pairs reachable without a session. The Stripe webhook joins in Milestone 2.
PUBLIC_ROUTES: frozenset[tuple[str, str]] = frozenset(
    {
        ("GET", "/healthz"),
        ("POST", "/v1/auth/sign-in"),
        ("POST", "/v1/auth/sign-up"),
        ("POST", "/v1/auth/sign-out"),
    }
)


@dataclass(frozen=True)
class RouteInfo:
    path: str
    methods: frozenset[str]
    dependant: Dependant
    include_in_schema: bool


def iter_routes(app: FastAPI) -> Iterator[RouteInfo]:
    """Every API route with its *effective* dependencies, including router-level ones.

    FastAPI 0.14x keeps included routers as nested ``_IncludedRouter`` objects instead of
    flattening them into ``app.routes``; ``effective_candidates()`` resolves each route with
    the dependencies its routers add. That is private API, so :func:`assert_routes_protected`
    cross-checks the result against the public OpenAPI schema and fails loudly if a FastAPI
    upgrade changes it.
    """
    stack: list[Any] = list(app.routes)
    while stack:
        node = stack.pop()
        if isinstance(node, APIRoute) or (
            hasattr(node, "dependant") and hasattr(node, "methods") and hasattr(node, "path")
        ):
            yield RouteInfo(
                path=node.path,
                methods=frozenset(node.methods or ()),
                dependant=node.dependant,
                include_in_schema=bool(getattr(node, "include_in_schema", True)),
            )
        elif hasattr(node, "effective_candidates"):
            stack.extend(node.effective_candidates())


def route_requires_user(dependant: Dependant) -> bool:
    stack = list(dependant.dependencies)
    while stack:
        dep = stack.pop()
        if dep.call is require_user:
            return True
        stack.extend(dep.dependencies)
    return False


def assert_routes_protected(app: FastAPI) -> None:
    routes = list(iter_routes(app))
    walked = {(m, r.path) for r in routes if r.include_in_schema for m in r.methods}
    documented = {
        (method.upper(), path)
        for path, ops in app.openapi().get("paths", {}).items()
        for method in ops
    }
    if missing := documented - walked:
        raise RuntimeError(
            "Route enumeration is incomplete (FastAPI internals changed?): "
            + ", ".join(f"{m} {p}" for m, p in sorted(missing))
        )
    unprotected = sorted(
        f"{method} {r.path}"
        for r in routes
        for method in r.methods
        if (method, r.path) not in PUBLIC_ROUTES and not route_requires_user(r.dependant)
    )
    if unprotected:
        raise RuntimeError(f"Routes missing the session check: {', '.join(unprotected)}")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="AI Commerce API",
        version="0.1.0",
        description="Commerce API for the storefront and assistant. Every route requires a "
        "signed-in session except auth routes and /healthz.",
        # Interactive docs only in development; the OpenAPI JSON feeds the TS client.
        docs_url="/docs" if settings.is_dev else None,
        redoc_url=None,
    )

    @app.get("/healthz", tags=["ops"])
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    private = [Depends(require_user)]
    app.include_router(auth_router)
    app.include_router(catalog_router, dependencies=private)
    app.include_router(cart_router, dependencies=private)
    app.include_router(orders_router, dependencies=private)

    assert_routes_protected(app)
    return app


def build_instrumented_app() -> FastAPI:
    """The app uvicorn runs: telemetry first, then the instrumented app."""
    from commerce.telemetry import init_telemetry

    init_telemetry("commerce-api")
    app = create_app()
    FastAPIInstrumentor.instrument_app(app, excluded_urls="healthz")
    return app
