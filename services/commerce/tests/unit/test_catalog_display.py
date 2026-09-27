from __future__ import annotations

import re

import pytest

from commerce.catalog.display import bayesian_rating, type_label, unit_price
from commerce.seed.catalog import PRODUCTS


@pytest.mark.parametrize(
    ("raw", "label"),
    [
        ("milk", "Milk"),
        ("greek-yogurt", "Greek yogurt"),
        ("tv", "TV"),
        ("usb-c-charger", "USB-C charger"),
        ("hdmi-cable", "HDMI cable"),
        ("ssd", "SSD"),
        ("e-reader", "E-reader"),
        ("4k-tv", "4K TV"),
        ("vitamin-c", "Vitamin C"),
        ("vitamin-d", "Vitamin D"),
        ("vitamin-b12", "Vitamin B12"),
        ("omega-3", "Omega-3"),
        ("t-shirt", "T-shirt"),
        ("rc-car", "RC car"),
        ("stem-kit", "STEM kit"),
        ("all-purpose-cleaner", "All-purpose cleaner"),
        ("plant-based-meat", "Plant-based meat"),
        ("after-sun", "After-sun"),
    ],
)
def test_type_labels_read_naturally(raw: str, label: str) -> None:
    assert type_label(raw) == label


# Lower-case acronyms, or a hyphenated compound split into two words, read as mistakes.
_ACRONYMS = re.compile(r"\b(usb|hdmi|ssd|hdd|tv|spf|led|lcd|gps|bbq|rc|stem|diy|vr|pc)\b")
_SPLIT_COMPOUNDS = re.compile(
    r"\b(T shirt|Omega 3|All purpose|Plant based|After sun|E reader|USB C)\b", re.IGNORECASE
)


@pytest.mark.parametrize("product_type", sorted({p.product_type for p in PRODUCTS}))
def test_every_catalog_type_label_is_cased_like_a_shopper_would_write_it(
    product_type: str,
) -> None:
    label = type_label(product_type)
    assert label[0].isupper(), label
    assert not _ACRONYMS.search(label), f"lower-case acronym in {label!r}"
    assert not _SPLIT_COMPOUNDS.search(label), f"compound word split in {label!r}"
    # "Vitamin c", "Vitamin b12": a vitamin's letter is a capital.
    assert not re.search(r"\bVitamin [a-z]", label), label
    # A lone lower-case letter ("T shirt" -> "t"), or a letter-digit code like "b12".
    assert not re.search(r"(?<![\w-])[a-z](?![\w-])|\b[a-z]\d+\b", label), label
    # Every word after the first is lower case unless it's an acronym or a code.
    for word in label.split()[1:]:
        assert (
            word.islower()
            or word.isupper()
            or word[:-1].isupper()
            or any(c.isdigit() for c in word)
        ), f"{word!r} in {label!r}"


def test_unit_price_from_net_ounces() -> None:
    assert unit_price(329, {"net_oz": 128}) == "2.6¢/oz"
    assert unit_price(1299, {"net_oz": 8}) == "$1.62/oz"
    assert unit_price(329, {"size": "1 gallon"}) is None
    assert unit_price(329, {"net_oz": 0}) is None


def test_many_good_reviews_beat_a_few_perfect_ones() -> None:
    assert bayesian_rating(4.8, 40) > bayesian_rating(5.0, 3)
    assert bayesian_rating(5.0, 3) > bayesian_rating(None, 0)
