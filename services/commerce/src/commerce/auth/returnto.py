"""Keep post-sign-in redirects on our own site.

Mirrors ``apps/web/lib/return-to.ts``; both have unit tests with the same cases.
"""

from __future__ import annotations

from urllib.parse import urlsplit

DEFAULT_RETURN_TO = "/"
_AUTH_PAGES = ("/sign-in", "/sign-up")


def safe_return_to(value: str | None) -> str:
    """Return ``value`` if it is a same-site path, otherwise ``/``.

    Rejects absolute URLs, scheme-relative ``//host``, backslash tricks (browsers treat
    ``/\\host`` like ``//host``), control characters, and loops back to the auth pages.
    """
    if not value or len(value) > 2048:
        return DEFAULT_RETURN_TO
    if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in value):
        return DEFAULT_RETURN_TO
    if not value.startswith("/") or value.startswith("//") or "\\" in value:
        return DEFAULT_RETURN_TO
    parts = urlsplit(value)
    if parts.scheme or parts.netloc:
        return DEFAULT_RETURN_TO
    if any(parts.path == p or parts.path.startswith(p + "/") for p in _AUTH_PAGES):
        return DEFAULT_RETURN_TO
    return value
