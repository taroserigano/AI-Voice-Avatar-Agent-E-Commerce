"""How fused search candidates are re-ranked and pruned by the words they share with the query.

The candidate lists below are in the order the two search legs actually fused them for these
queries (the Round 1 and 2 evaluations found each problem in the live store).
"""

from __future__ import annotations

import pytest

from commerce.search.ranking import Candidate, close_spelling, parse_query, rank_candidates, stem


def c(
    cid: str,
    title: str,
    product_type: str,
    *,
    tags: tuple[str, ...] = (),
    description: str = "",
    semantic: bool = False,
) -> Candidate:
    return Candidate(
        id=cid,
        title=title,
        product_type=product_type,
        brand="Larkspur",
        tag_labels=tags,
        description=description,
        semantic=semantic,
    )


MILK_FUSED = [
    # Typo tolerance put these into the keyword leg's 400 hits: "Mild", "Wild", "mix".
    c("puzzle", "Starry Canyon 2000-Piece Puzzle", "puzzle", description="A mild challenge."),
    c("whole", "Whole Milk", "milk", tags=("Whole milk",)),
    c("almond", "Original Almond Milk", "plant-milk", tags=("Dairy free",)),
    c("seed", "Wild Bird Seed Mix, 20 lb", "bird-seed"),
    c("skim", "Fat Free Skim Milk", "milk", tags=("Fat free",)),
    c("sausage", "Mild Italian Pork Sausage Links", "sausage"),
    c("bar", "Milk Chocolate Bar", "chocolate"),
    c("yogurt", "Low Fat Yogurt, Vanilla", "yogurt", description="Made with cultured milk."),
]


def test_milk_puts_milk_first_and_drops_fuzzy_spelling_matches() -> None:
    ranking = rank_candidates("milk", MILK_FUSED)

    assert ranking.ids[:2] == ["whole", "skim"]  # the product type asked for, in fused order
    assert ranking.ids[2:] == ["almond", "bar"]  # "milk" in the title, related type first
    assert {"puzzle", "seed", "sausage", "yogurt"}.isdisjoint(ranking.ids)
    assert ranking.dropped == 4
    assert ranking.exact


def test_diapers_size_3_ranks_diapers_above_things_labeled_size_or_3() -> None:
    fused = [
        c("towels", "Select-A-Size Paper Towels, Double Rolls", "paper-towels"),
        c("overnight", "Overnight Diapers", "diapers", description="Sizes 3 to 6."),
        c("tp", "Ultra Plush 3-Ply Toilet Paper, Mega Rolls", "toilet-paper"),
        c("everyday", "Everyday Diapers", "diapers"),
        c("swim", "Little Splashers Swim Diapers", "swim-diapers"),
        c("notes", "Sticky Notes, 3 x 3 in, Pastel, 12 Pads", "sticky-notes"),
    ]

    ranking = rank_candidates("diapers size 3", fused)

    assert ranking.ids == ["overnight", "everyday", "swim"]
    assert ranking.exact


def test_ipad_with_no_ipads_keeps_only_a_meaning_match() -> None:
    fused = [
        c("puppy", "Puppy Training Pads", "puppy-pads"),
        c("heat", "Electric Heating Pad, XL 12 x 24 in", "heating-pad"),
        c("tablet", "Lumen Tab 10 Tablet, 64 GB", "tablet", semantic=True),
    ]

    ranking = rank_candidates("ipad", fused)

    # "pad" is not "ipad": a 4-letter word has no typo tolerance. The tablet passed the
    # meaning leg's score cut, so it stays as a related item.
    assert not ranking.exact
    assert ranking.ids == ["tablet"]
    assert ranking.dropped == 2


def test_nothing_reasonably_matching_leaves_no_results() -> None:
    # What the keyword leg's old typo tolerance returned for "ipad" in the live store.
    fused = [
        c("puppy", "Puppy Training Pads, 100 Count", "puppy-pads"),
        c("thai", "Vegan Pad Thai", "frozen-meals"),
        c("heat", "Electric Heating Pad, XL 12 x 24 in", "heating-pad"),
        c("sleep", "Self-Inflating Sleeping Pad", "sleeping-pad"),
        c("notes", "Sticky Notes, 3 x 3 in, Pastel, 12 Pads", "sticky-notes"),
    ]
    ranking = rank_candidates("ipad", fused)
    assert ranking.ids == [] and ranking.dropped == 5 and not ranking.exact


def test_with_no_exact_match_a_word_in_the_description_still_counts() -> None:
    fused = [
        c("case", "Folio Tablet Case, 10 in", "tablet-case", description="Fits iPad and more."),
        c("puppy", "Puppy Training Pads", "puppy-pads"),
    ]
    ranking = rank_candidates("ipad", fused)
    assert ranking.ids == ["case"] and not ranking.exact


def test_meaning_match_that_passed_its_score_cut_stays_behind_word_matches() -> None:
    fused = [
        c("cream", "Heavy Whipping Cream", "cream", semantic=True),
        c("whole", "Whole Milk", "milk"),
    ]
    assert rank_candidates("milk", fused).ids == ["whole", "cream"]


def test_every_query_word_in_the_title_beats_matching_only_the_type() -> None:
    fused = [
        c("plain", "Whole Milk", "milk"),
        c("cups", "Milk Chocolate Peanut Butter Cups", "candy"),
        c("choc", "Whole Chocolate Milk", "milk"),
    ]
    assert rank_candidates("milk chocolate", fused).ids == ["choc", "cups", "plain"]


def test_synonyms_count_as_the_query_word() -> None:
    fused = [c("tv", "55-Inch 4K UHD Smart TV", "tv"), c("stand", "Wooden Plant Stand", "planter")]
    ranking = rank_candidates("television", fused)
    assert ranking.ids == ["tv"]
    assert ranking.exact

    shoes = rank_candidates("rain shoes", [c("boots", "Puddle Rain Boots", "boots")])
    assert shoes.ids == ["boots"] and shoes.exact


def test_typo_with_no_exact_match_keeps_the_close_spellings() -> None:
    fused = [
        c("bananas", "Bananas", "bananas"),
        c("muffins", "Banana Nut Muffins", "muffins"),
        c("pan", "Nonstick Loaf Pan, 9 x 5 in", "bakeware", description="For banana bread."),
        c("cabana", "Cabana Stripe Beach Towel", "beach-towels"),
    ]
    ranking = rank_candidates("bananna", fused)
    assert ranking.ids == ["bananas", "muffins"]
    assert ranking.dropped == 2
    assert not ranking.exact  # the page says these are the nearest items, not exact matches


@pytest.mark.parametrize(
    ("query", "keep", "drop"),
    [
        ("yoghurt", c("y", "Nonfat Greek Yogurt, Plain", "greek-yogurt"), c("h", "Yoga Mat", "x")),
        (
            "lactos",
            c("l", "Whole Lactose-Free Milk", "milk", tags=("Lactose free",)),
            c("t", "Latte Mugs, Set of 2", "mugs"),
        ),
        (
            "strawbery jam",
            c("s", "Strawberry Jam", "jam"),
            c("b", "Stationery Set", "stationery"),
        ),
    ],
)
def test_real_misspellings_of_longer_words_still_find_the_product(
    query: str, keep: Candidate, drop: Candidate
) -> None:
    ranking = rank_candidates(query, [drop, keep])
    assert ranking.ids == [keep.id]


def test_close_spelling_rules() -> None:
    assert close_spelling("bananna", "banana")
    assert close_spelling("yoghurt", "yogurt")
    assert close_spelling("choclate", "chocolate")
    assert close_spelling("cofee", "coffee")
    assert close_spelling("tomatoe", "tomato")
    assert close_spelling("chedar", "cheddar")
    assert close_spelling("lettcue", "lettuce")  # a swap is one edit
    # Short words must be spelled right, and a typo keeps the first letter.
    assert not close_spelling("ipad", "pad")
    assert not close_spelling("milk", "mild")
    assert not close_spelling("pads", "ipad")
    assert not close_spelling("yogurt", "bogurt")
    assert not close_spelling("bananna", "cabana")
    assert not close_spelling("chocolate", "cheese")


def test_query_of_only_stopwords_keeps_the_fused_order() -> None:
    fused = [c("a", "Alpha", "x"), c("b", "Beta", "y")]
    assert rank_candidates("the", fused).ids == ["a", "b"]


def test_query_parsing() -> None:
    assert stem("diapers") == "diaper"
    assert stem("berries") == "berry"
    assert stem("glasses") == "glass"
    concepts = parse_query("fat free milk, size 3")
    # "fat free" is one idea (with its synonyms); size and 3 only narrow it.
    assert [cn.weak for cn in concepts] == [False, False, True, True]
    assert ("skim",) in concepts[0].alternatives
