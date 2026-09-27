"""Seeded sample reviews have to read like real reviews of *this* product.

Milk must not be praised for its colors, headphones must not taste fresh, a product only
gets called "organic" or "gluten-free" when the catalog says so, and one product's reviews
never repeat a sentence. These run over the whole seed catalog.
"""

from __future__ import annotations

import re
from collections import Counter

import pytest

from commerce.reviews.service import author_name
from commerce.seed.catalog import PRODUCTS
from commerce.seed.data import ProductSeed
from commerce.seed.review_text import REVIEWERS
from commerce.seed.review_text_families import FAMILIES
from commerce.seed.reviews import (
    MAX_REVIEWS,
    ProductFacts,
    SampleReview,
    compose_sample_reviews,
    family_of,
    noun_for,
    parse_line,
)

FOOD = {
    "dairy-eggs", "produce", "meat-seafood", "bakery", "frozen", "pantry", "snacks", "beverages",
}  # fmt: skip
REVIEWS: list[tuple[ProductSeed, list[SampleReview]]] = [
    (p, compose_sample_reviews(ProductFacts.from_seed(p))) for p in PRODUCTS
]
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")

# Phrases that only belong on electronics or clothing, and phrases that only belong on food.
NOT_FOR_FOOD = re.compile(
    r"\b(batter(y|ies)|charg\w*|bluetooth|wi-?fi|set ?up|pair(s|ed|ing)?|fabric|stitch\w*|"
    r"seams?|sizing|true to size|runs (way |slightly |a half size )?(small|large|big)|"
    r"waistband|bass|volume|screen|pixels?|zipper|sleeves?|washing machine|well made|"
    r"colou?rs?)\b",
    re.IGNORECASE,
)
NOT_FOR_ELECTRONICS_OR_CLOTHING = re.compile(
    r"\b(tast\w*|flavou?r\w*|delicious|ripe|crunchy|creamy|recipes?|snacks?|expir\w*|"
    r"best-by|stale|juicy|bland|grocer(y|ies)|fridge|freezer|kids devoured)\b",
    re.IGNORECASE,
)

# A claim in review text -> the tags that allow it.
CLAIMS: dict[str, tuple[str, ...]] = {
    r"\borganic\b": ("organic",),
    r"gluten-free": ("gluten-free",),
    r"\bvegan\b": ("vegan",),
    r"can't have dairy": ("dairy-free",),
    r"lactose": ("lactose-free",),
    r"no added sugar": ("no-added-sugar",),
    r"sugar-free": ("sugar-free",),
    r"lower in sugar": ("low-sugar",),
    r"low-carb": ("keto",),
    r"\bdecaf\b": ("decaf",),
    r"fair trade": ("fair-trade",),
    r"wild-caught": ("wild-caught",),
    r"grass-fed": ("grass-fed",),
    r"no caffeine": ("caffeine-free",),
    r"sodium": ("low-sodium", "no-salt-added"),
    r"whole grain": ("whole-grain",),
    r"\bunsweetened\b": ("unsweetened",),
    r"zero calories": ("zero-calorie",),
    r"antibiotics": ("antibiotic-free",),
    r"non-gmo": ("non-gmo",),
    r"farming practices": ("pasture-raised", "free-range", "cage-free"),
    r"whole milk should": ("whole-milk",),
    r"skim milk": ("fat-free",),
    r"washing machine": ("machine-washable",),
    r"dishwasher,": ("dishwasher-safe",),
    r"bpa-free": ("bpa-free",),
    r"usb-c": ("usb-c",),
    r"noise cancel": ("noise-cancelling",),
    r"cruelty-free": ("cruelty-free",),
    r"no perfume": ("fragrance-free",),
    r"sulfate-free": ("sulfate-free",),
    r"aluminum-free": ("aluminum-free",),
    r"tear-free": ("tear-free",),
    r"biodegradable": ("biodegradable",),
    r"recycled": ("recycled-materials",),
    r"grain-free": ("grain-free",),
    r"\bHE washer": ("he-compatible",),
    r"cordless": ("cordless",),
    r"wicks sweat": ("moisture-wicking",),
    r"dye-free": ("dye-free",),
    r"sensitive skin had|allergies haven't": ("sensitive-skin", "hypoallergenic"),
    r"having to buy batteries|charges? over usb": ("rechargeable",),
    r"very little power": ("energy-efficient",),
    r"kept me dry in a downpour|stayed dry through an overnight storm|kept my feet dry": (
        "waterproof",
    ),
}


def _sentences(review: SampleReview) -> list[str]:
    return SENTENCE_END.split(review.body)


def test_no_sentence_repeats_within_a_product() -> None:
    for product, reviews in REVIEWS:
        counts = Counter(s for r in reviews for s in _sentences(r))
        repeated = [s for s, n in counts.items() if n > 1]
        assert not repeated, f"{product.slug}: {repeated}"


def test_titles_and_reviewers_do_not_repeat_within_a_product() -> None:
    for product, reviews in REVIEWS:
        titles = [r.title for r in reviews if r.title]
        assert len(titles) == len(set(titles)), product.slug
        assert len({r.reviewer for r in reviews}) == len(reviews), product.slug


def test_reviews_are_complete_and_fit_the_columns() -> None:
    for product, reviews in REVIEWS:
        for r in reviews:
            assert 1 <= r.rating <= 5
            assert r.title and len(r.title) <= 120, product.slug
            assert len(_sentences(r)) >= 2 and len(r.body) <= 2000, (product.slug, r.body)
            assert not re.search(r"[{}\[\]]", r.body + r.title), (product.slug, r.body)
            assert r.body[0].isupper() and r.body[-1] in ".!", (product.slug, r.body)


def test_food_reviews_never_talk_like_electronics_or_clothing() -> None:
    for product, reviews in REVIEWS:
        if product.category in FOOD:
            for r in reviews:
                match = NOT_FOR_FOOD.search(f"{r.title} {r.body}")
                assert match is None, (product.slug, match.group(0), r.body)


def test_electronics_and_clothing_reviews_never_talk_about_food() -> None:
    for product, reviews in REVIEWS:
        if product.category in ("electronics", "clothing-shoes"):
            for r in reviews:
                match = NOT_FOR_ELECTRONICS_OR_CLOTHING.search(f"{r.title} {r.body}")
                assert match is None, (product.slug, match.group(0), r.body)


@pytest.mark.parametrize(("claim", "tags"), CLAIMS.items(), ids=list(CLAIMS))
def test_claims_only_appear_when_the_product_has_them(claim: str, tags: tuple[str, ...]) -> None:
    pattern = re.compile(claim, re.IGNORECASE)
    for product, reviews in REVIEWS:
        # The claim may also come straight from the catalog: a spec such as "100% recycled
        # polyester", or the brand's own name.
        catalog = " ".join([product.title, *product.specs.values()])
        if pattern.search(catalog):
            continue
        for r in reviews:
            text = f"{r.title} {r.body}".replace(product.brand, "")
            if pattern.search(text):
                assert set(tags) & set(product.tags), (product.slug, r.body)


def test_named_flavors_and_scents_are_the_products_own() -> None:
    named = re.compile(r"The ([\w &'-]+?) (flavor|scent)")
    for product, reviews in REVIEWS:
        for r in reviews:
            for m in named.finditer(r.body):
                spec = product.specs.get(m.group(2).title(), "").lower()
                assert m.group(1).lower() in spec, (product.slug, r.body)


def test_every_catalog_product_type_has_a_review_family() -> None:
    missing = {
        (p.category, p.product_type)
        for p in PRODUCTS
        if family_of(p.category, p.product_type) not in FAMILIES
    }
    assert not missing


def test_nouns_read_naturally() -> None:
    facts = {p.slug: ProductFacts.from_seed(p) for p in PRODUCTS}
    assert noun_for(facts["larkspur-kitchen-navel-oranges"]) == "oranges"
    assert noun_for(facts["sonora-arc-wireless-headphones"]) == "headphones"
    assert noun_for(facts["larkspur-kitchen-romaine-hearts"]) == "romaine"
    arc = next(r for p, rs in REVIEWS if p.slug == "sonora-arc-wireless-headphones" for r in rs)
    assert "this headphones" not in arc.body.lower()


def test_composition_is_deterministic() -> None:
    for product, reviews in REVIEWS[::50]:
        assert compose_sample_reviews(ProductFacts.from_seed(product)) == reviews


def test_ratings_are_mostly_positive_with_some_honest_lows() -> None:
    ratings = Counter(r.rating for _, reviews in REVIEWS for r in reviews)
    total = sum(ratings.values())
    mean = sum(stars * n for stars, n in ratings.items()) / total
    assert 4.0 <= mean <= 4.5
    assert 0.03 <= (ratings[1] + ratings[2]) / total <= 0.12
    assert 0.05 <= ratings[3] / total <= 0.15
    # Products differ: not every reviewed product averages the same.
    averages = {round(sum(r.rating for r in rs) / len(rs), 1) for _, rs in REVIEWS if len(rs) >= 5}
    assert len(averages) >= 10


def test_review_counts_vary_and_popular_types_get_more() -> None:
    counts = [len(rs) for _, rs in REVIEWS]
    assert min(counts) == 0 and max(counts) == MAX_REVIEWS
    milk = [len(rs) for p, rs in REVIEWS if p.product_type == "milk"]
    staples = [len(rs) for p, rs in REVIEWS if p.product_type == "staples"]
    assert min(milk) >= 5
    assert sum(milk) / len(milk) > sum(counts) / len(counts) > sum(staples) / len(staples)


def test_bodies_rarely_repeat_across_products_of_the_same_type() -> None:
    by_type: dict[str, Counter[str]] = {}
    for product, reviews in REVIEWS:
        by_type.setdefault(product.product_type, Counter()).update(r.body for r in reviews)
    total = sum(sum(c.values()) for c in by_type.values())
    repeats = sum(n - 1 for c in by_type.values() for n in c.values() if n > 1)
    assert repeats / total < 0.01


def test_sample_reviewers_look_like_people() -> None:
    emails = [email for email, _ in REVIEWERS]
    assert len(emails) == len(set(emails)) and len(emails) >= MAX_REVIEWS
    assert all(e.endswith(".sample@example.com") for e in emails)
    for _, name in REVIEWERS:
        assert re.fullmatch(r"[A-Z][a-z]+ [A-Z][\w']+", name), name
        assert re.fullmatch(r"[A-Z][a-z]+ [A-Z]\.", author_name(name))


def test_line_syntax_is_checked() -> None:
    line = parse_line("[tag:organic;!type:milk;spec:Flavor=vanilla;#taste] Great {noun}.")
    assert (line.text, line.topic, line.fields) == ("Great {noun}.", "taste", {"noun"})
    with pytest.raises(ValueError, match="placeholder"):
        parse_line("Love the {colour}.")
    with pytest.raises(ValueError, match="condition"):
        parse_line("[brand:x] Nice.")
