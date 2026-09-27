"""Typeahead completions, built from the titles that matched what the shopper has typed."""

from __future__ import annotations

from collections import Counter

from commerce.search.suggest import build_completions, correct_tokens, query_tokens

LACT_TITLES = [
    ("Whole Lactose-Free Milk", "milk"),
    ("1% Low Fat Lactose-Free Milk", "milk"),
    ("Fat Free Skim Lactose-Free Milk", "milk"),
    ("Lactose-Free Cottage Cheese", "cheese"),
]


def test_lact_completes_to_the_word_and_the_products_it_is_on() -> None:
    completions = build_completions(LACT_TITLES, ["lact"], limit=5)
    assert completions[:2] == ["lactose-free", "lactose-free milk"]
    assert "lactose-free cheese" in completions


def test_earlier_words_are_kept_and_an_already_typed_type_is_not_repeated() -> None:
    rows = [("Organic Whole Milk", "milk"), ("Organic 2% Reduced Fat Milk", "milk")]
    assert build_completions(rows, ["organic", "mi"], limit=3) == ["organic milk"]
    assert build_completions(LACT_TITLES[:1], ["milk", "lact"], limit=3) == ["milk lactose-free"]


def test_a_word_on_its_own_type_offers_that_type() -> None:
    rows = [("Original Almond Milk", "plant-milk"), ("Vanilla Oat Milk", "plant-milk")]
    assert build_completions(rows, ["mil"], limit=3) == ["milk", "plant milk"]


def test_the_exact_query_is_not_offered_back() -> None:
    assert "milk" not in build_completions([("Whole Milk", "milk")], ["milk"], limit=3)


def test_tokens_are_regex_safe() -> None:
    assert query_tokens("Lact.*(ose)+ [a-z]") == ["lact", "ose", "a", "z"]
    assert query_tokens("  ") == []


VOCAB = Counter(
    {"banana": 9, "bananas": 4, "bandana": 1, "yogurt": 30, "yoga": 6, "lactose": 12, "milk": 40}
)


def test_a_typo_in_a_longer_word_is_corrected_once() -> None:
    assert correct_tokens(["bananna"], VOCAB) == ["banana"]
    assert correct_tokens(["yoghurt"], VOCAB) == ["yogurt"]
    assert correct_tokens(["lactos"], VOCAB) == ["lactose"]
    # Still being typed: it can match the start of a longer word.
    assert correct_tokens(["banann"], VOCAB) == ["banana"]
    assert correct_tokens(["yoghur"], VOCAB) == ["yogurt"]
    assert correct_tokens(["milk", "yoghurt"], VOCAB) == ["milk", "yogurt"]


def test_short_words_known_words_and_far_spellings_are_left_alone() -> None:
    assert correct_tokens(["ipad"], VOCAB) is None  # under 5 letters: no guessing
    assert correct_tokens(["mlik"], VOCAB) is None
    assert correct_tokens(["banana"], VOCAB) is None  # already a word
    assert correct_tokens(["cabana"], VOCAB) is None  # a typo keeps the first letter
    assert correct_tokens(["xylophone"], VOCAB) is None
