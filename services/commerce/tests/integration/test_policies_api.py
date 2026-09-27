"""Policy search: the assistant's source for cited answers."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("how long do I have to return a blender", "returns-and-refunds#rr-2-1"),
        ("can I drop off my return at the Plano store", "returns-and-refunds#rr-6-2"),
        ("do I get my shipping money back if I return something", "returns-and-refunds#rr-7-3"),
        ("can I return a gift card", "returns-and-refunds#rr-3-1"),
        ("store credit instead of a refund to my card", "returns-and-refunds#rr-11-2"),
        ("what does fat free mean", "product-labels"),
    ],
)
def test_policy_search_finds_the_right_section(
    alice: TestClient, query: str, expected: str
) -> None:
    resp = alice.get("/v1/policies/search", params={"q": query, "limit": 3})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    cites = [r["cite"] for r in body["results"]]
    assert expected in cites, cites
    first = body["results"][0]
    assert first["version"] == "sandbox-2026-09" and first["body"]
    if first["doc_id"] == "returns-and-refunds":
        assert first["url"] == f"/returns-policy#{first['section_id']}"


def test_policy_document_and_sign_in(alice: TestClient, client: TestClient) -> None:
    doc = alice.get("/v1/policies/returns-and-refunds").json()
    assert doc["url"] == "/returns-policy" and len(doc["sections"]) > 30
    assert alice.get("/v1/policies/nope").status_code == 404
    assert client.get("/v1/policies/search", params={"q": "returns"}).status_code == 401
