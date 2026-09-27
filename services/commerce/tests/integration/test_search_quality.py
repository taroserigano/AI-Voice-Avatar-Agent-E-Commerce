"""Search relevance and typeahead against the seeded catalog (PostgreSQL + OpenSearch).

These pin the Round 1 evaluation's findings: "milk" listed a puzzle, bird seed, and sausage;
"diapers size 3" put paper towels first; "ipad" showed puppy pads without saying they're
only related; "400 matches" was really the keyword leg's cap; typing "lact" suggested nothing.
And Round 2's: "ipad" still showed pads and Pad Thai; typing "bananna" suggested nothing.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from commerce.config import get_settings

pytestmark = pytest.mark.integration


def _search(client: TestClient, q: str, **params: object) -> dict:  # type: ignore[type-arg]
    resp = client.get("/v1/products", params={"q": q, "page_size": 60, **params})
    assert resp.status_code == 200, resp.text
    return resp.json()  # type: ignore[no-any-return]


def _all_items(client: TestClient, q: str) -> list[dict]:  # type: ignore[type-arg]
    items, page = [], 1
    while True:
        body = _search(client, q, page=page)
        items += body["items"]
        if page * 60 >= body["total"]:
            return items
        page += 1


def test_milk_lists_milk_and_nothing_merely_spelled_like_it(alice: TestClient) -> None:
    page = _search(alice, "milk")
    items = _all_items(alice, "milk")

    assert {i["product_type"] for i in page["items"][:12]} == {"milk"}
    titles = " ".join(i["title"] for i in items).lower()
    for unrelated in ("puzzle", "bird seed", "sausage links"):
        assert unrelated not in titles
    assert all("milk" in f"{i['title']} {i['type_label']}".lower() or i["tags"] for i in items)
    assert page["search"]["exact_match"] is True
    assert page["search"]["notice"] is None


def test_diapers_size_3_puts_diapers_first(alice: TestClient) -> None:
    items = _search(alice, "diapers size 3")["items"]

    assert items[0]["product_type"] == "diapers"
    top_types = [i["product_type"] for i in items[:4]]
    assert top_types == ["diapers"] * 4
    assert not {"paper-towels", "toilet-paper", "sticky-notes"} & {i["product_type"] for i in items}


def test_ipad_with_no_ipads_returns_nothing_instead_of_pads(alice: TestClient) -> None:
    # Round 2: the typo tolerance turned "ipad" into "pad" (Puppy Training Pads, Vegan Pad
    # Thai, heating and sleeping pads). With nothing reasonably matching, the page shows its
    # empty state (departments, popular searches) instead of junk.
    page = _search(alice, "ipad")

    assert page["total"] == 0 and page["items"] == []
    assert page["search"]["notice"] is None  # that notice is only for a degraded search
    assert page["search"]["exact_match"] is False


@pytest.mark.parametrize("q", ["pad", "pads"])
def test_the_word_itself_still_finds_pads(alice: TestClient, q: str) -> None:
    items = _search(alice, q)["items"]
    assert items and all("pad" in i["title"].lower() for i in items[:5])


@pytest.mark.parametrize(
    ("q", "expect"),
    [
        ("bananna", "banana"),
        ("yoghurt", "yogurt"),
        ("lactos", "lactose"),
        ("greek yoghurt", "greek yogurt"),
    ],
)
def test_misspellings_of_longer_words_still_find_the_product(
    alice: TestClient, q: str, expect: str
) -> None:
    items = _all_items(alice, q)
    assert items, q
    titles = [i["title"].lower() for i in items]
    assert all(expect in t for t in titles[:5]), titles[:5]
    # Every result has the word it was misspelled from, in its title, type, or labels: nothing
    # that merely shares a fragment or has it only in the description.
    word = expect.split()[-1]
    labels = [
        " ".join([i["title"], i["type_label"], *(t["label"] for t in i["tags"])]).lower()
        for i in items
    ]
    assert all(word in text for text in labels), [t for t in labels if word not in t]


def test_a_search_that_fills_the_keyword_limit_reports_a_lower_bound(
    alice: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(get_settings(), "keyword_top_k", 10)
    capped = _search(alice, "milk")
    assert capped["total"] == 10
    assert capped["search"]["total_capped"] is True

    monkeypatch.setattr(get_settings(), "keyword_top_k", 400)
    exact = _search(alice, "diapers size 3")
    assert exact["search"]["total_capped"] is False


def test_typeahead_completes_lact(alice: TestClient) -> None:
    resp = alice.get("/v1/search/suggest", params={"q": "lact"})
    assert resp.status_code == 200
    body = resp.json()

    assert "lactose-free milk" in body["completions"]
    assert body["products"], "top products for the typed word"
    for p in body["products"]:
        assert "lactose" in p["title"].lower()
        assert p["price_minor"] > 0 and p["currency"] == "USD"


@pytest.mark.parametrize(("q", "word"), [("bananna", "banana"), ("yoghur", "yogurt")])
def test_typeahead_tolerates_a_typo_in_a_longer_word(alice: TestClient, q: str, word: str) -> None:
    body = alice.get("/v1/search/suggest", params={"q": q}).json()
    assert body["query"] == q
    assert body["products"] and all(word in p["title"].lower() for p in body["products"])
    assert body["completions"][0].startswith(word)


def test_typeahead_does_not_guess_at_short_words(alice: TestClient) -> None:
    body = alice.get("/v1/search/suggest", params={"q": "ipad"}).json()
    assert body["products"] == [] and body["completions"] == []


def test_typeahead_offers_types_and_departments(alice: TestClient) -> None:
    body = alice.get("/v1/search/suggest", params={"q": "diap"}).json()
    types = {t["value"]: t for t in body["product_types"]}
    assert "diapers" in types
    assert types["diapers"]["category_slug"] == "baby"
    assert types["diapers"]["count"] >= 1

    dept = alice.get("/v1/search/suggest", params={"q": "dairy"}).json()["departments"]
    assert [d["slug"] for d in dept] == ["dairy-eggs"]


def test_typeahead_ignores_a_single_character_and_regex_syntax(alice: TestClient) -> None:
    one = alice.get("/v1/search/suggest", params={"q": "m"}).json()
    assert one["completions"] == one["products"] == one["product_types"] == []

    odd = alice.get("/v1/search/suggest", params={"q": "(.*"})
    assert odd.status_code == 200
    assert odd.json()["products"] == []


def test_typeahead_requires_sign_in(client: TestClient) -> None:
    assert client.get("/v1/search/suggest", params={"q": "milk"}).status_code == 401
