"""Calls to the commerce API.

Two identities, kept apart on purpose:

- :func:`resolve_customer` uses the customer's session cookie once per request, only to ask
  the commerce API who is signed in.
- :class:`CommerceClient` acts for that customer with the assistant's service token and
  ``X-On-Behalf-Of``. The commerce API accepts it only on a short list of routes and refuses it
  on anything that confirms or pays. The cookie is never passed to tools or the model.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass
from typing import Any

import httpx

from assistant.config import Settings, get_settings


class CommerceError(RuntimeError):
    def __init__(self, status: int, detail: str, problems: list[dict[str, Any]] | None = None):
        super().__init__(f"commerce API {status}: {detail}")
        self.status = status
        self.detail = detail
        # Per-line reasons from the returns API (e.g. "final_sale", "perishable_reason").
        self.problems = problems or []


class NotSignedIn(RuntimeError):
    pass


@dataclass(frozen=True)
class Customer:
    id: uuid.UUID
    name: str
    email: str


_customer_cache: dict[str, tuple[float, Customer]] = {}
_CACHE_SECONDS = 30.0


def resolve_customer(session_token: str | None, settings: Settings | None = None) -> Customer:
    """Who is signed in, according to the commerce API. Raises NotSignedIn."""
    if not session_token:
        raise NotSignedIn
    settings = settings or get_settings()
    key = hashlib.sha256(session_token.encode()).hexdigest()
    hit = _customer_cache.get(key)
    if hit and time.monotonic() - hit[0] < _CACHE_SECONDS:
        return hit[1]
    resp = httpx.get(
        f"{settings.commerce_api_url}/v1/auth/me",
        cookies={settings.session_cookie_name: session_token},
        timeout=settings.commerce_timeout_s,
    )
    if resp.status_code == 401:
        _customer_cache.pop(key, None)
        raise NotSignedIn
    resp.raise_for_status()
    me = resp.json()
    customer = Customer(
        id=uuid.UUID(me["id"]), name=me.get("display_name") or "", email=me["email"]
    )
    _customer_cache[key] = (time.monotonic(), customer)
    return customer


class CommerceClient:
    """The commerce API, acting for one customer with the assistant's service identity."""

    def __init__(self, customer_id: uuid.UUID, settings: Settings | None = None) -> None:
        settings = settings or get_settings()
        self.customer_id = customer_id
        self._http = httpx.Client(
            base_url=settings.commerce_api_url,
            timeout=settings.commerce_timeout_s,
            headers={
                "Authorization": f"Bearer {settings.assistant_service_token}",
                "X-On-Behalf-Of": str(customer_id),
            },
        )

    def close(self) -> None:
        self._http.close()

    def _call(self, method: str, path: str, **kw: Any) -> Any:
        resp = self._http.request(method, path, **kw)
        if resp.status_code >= 400:
            problems: list[dict[str, Any]] = []
            try:
                body = resp.json()
                detail = body.get("detail", resp.text)
                problems = list(body.get("problems") or [])
            except ValueError:
                detail = resp.text
            raise CommerceError(resp.status_code, str(detail)[:300], problems)
        return resp.json() if resp.content else None

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return self._call("GET", path, params=params)

    def put(self, path: str, body: dict[str, Any]) -> Any:
        return self._call("PUT", path, json=body)

    def post(self, path: str, body: dict[str, Any]) -> Any:
        return self._call("POST", path, json=body)


_vocabulary: tuple[float, dict[str, Any]] | None = None


def catalog_vocabulary(client: CommerceClient) -> dict[str, Any]:
    """Product types and tags (cached for 10 minutes): the values search filters accept."""
    global _vocabulary
    if _vocabulary and time.monotonic() - _vocabulary[0] < 600:
        return _vocabulary[1]
    vocab = client.get("/v1/catalog/vocabulary")
    _vocabulary = (time.monotonic(), vocab)
    return dict(vocab)
