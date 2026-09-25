"""Same cases as apps/web/lib/return-to.test.ts: both sides must agree."""

from __future__ import annotations

import pytest

from commerce.auth.returnto import safe_return_to


@pytest.mark.parametrize(
    "value",
    ["/", "/cart", "/products/123?variant=abc", "/search?q=rain+boots#top", "/orders/9"],
)
def test_same_site_paths_are_kept(value: str) -> None:
    assert safe_return_to(value) == value


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "https://evil.example/phish",
        "http://localhost:3000/cart",
        "//evil.example",
        "/\\evil.example",
        "\\\\evil.example",
        "javascript:alert(1)",
        "cart",
        "/cart\nSet-Cookie: x=1",
        "/sign-in",
        "/sign-in?returnTo=/cart",
        "/sign-up",
        "/" + "a" * 3000,
    ],
)
def test_anything_else_falls_back_to_home(value: str | None) -> None:
    assert safe_return_to(value) == "/"
