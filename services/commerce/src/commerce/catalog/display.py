"""How catalog facts read to a shopper: product-type names, unit prices, and ranking scores."""

from __future__ import annotations

from typing import Any

# Words that aren't simply capitalized ("tv" -> "TV", "usb-c-charger" -> "USB-C charger").
_WORDS = {
    "tv": "TV",
    "tvs": "TVs",
    "usb": "USB",
    "usb-c": "USB-C",
    "hdmi": "HDMI",
    "ssd": "SSD",
    "hdd": "HDD",
    "led": "LED",
    "lcd": "LCD",
    "gps": "GPS",
    "e-reader": "E-reader",
    "bbq": "BBQ",
    "diy": "DIY",
    "spf": "SPF",
    "4k": "4K",
    "vr": "VR",
    "pc": "PC",
    "he": "HE",
    "rc": "RC",
    "stem": "STEM",
    "b12": "B12",
}

# Compound words that keep their hyphen ("t-shirt" -> "T-shirt", not "T shirt").
_COMPOUNDS = (
    "usb-c", "e-reader", "t-shirt", "omega-3", "after-sun", "all-purpose", "plant-based",
    "half-and-half",
)  # fmt: skip


def type_label(product_type: str) -> str:
    """A product type as shoppers read it: 'usb-c-charger' -> 'USB-C charger'.

    Acronyms stay upper case (TV, HDMI, RC, STEM), compound words keep their hyphen
    (T-shirt, Omega-3, All-purpose), and a vitamin's letter is a capital (Vitamin B12).
    """
    text = product_type
    for compound in _COMPOUNDS:  # protect the hyphen from the split below
        text = text.replace(compound, compound.replace("-", "‑"))
    words: list[str] = []
    for raw in text.split("-"):
        key = raw.replace("‑", "-")
        if key in _WORDS:
            word = _WORDS[key]
        elif words and words[-1].lower() == "vitamin":
            word = key.upper()  # vitamin-c -> Vitamin C, vitamin-d -> Vitamin D
        else:
            word = key
        words.append(word)
    label = " ".join(words)
    return label[0].upper() + label[1:] if label else label


def unit_price(price_minor: int, attributes: dict[str, Any] | None) -> str | None:
    """Price per ounce when the variant states its net ounces, e.g. '2.6¢/oz' or '$1.20/oz'."""
    net_oz: Any = (attributes or {}).get("net_oz")
    try:
        oz = float(net_oz) if net_oz is not None else 0.0
    except (TypeError, ValueError):
        return None
    if oz <= 0:
        return None
    cents = price_minor / oz
    return f"{cents:.1f}¢/oz" if cents < 100 else f"${cents / 100:.2f}/oz"


# Ranking by rating: a product with 3 five-star reviews shouldn't outrank one with 40 reviews
# averaging 4.8. Blend each average with the catalog-wide prior, weighted like PRIOR_WEIGHT reviews.
PRIOR_MEAN = 4.0
PRIOR_WEIGHT = 8


def bayesian_rating(average: float | None, count: int) -> float:
    if not count or average is None:
        return PRIOR_MEAN - 0.5  # unreviewed items rank below the typical reviewed one
    return (average * count + PRIOR_MEAN * PRIOR_WEIGHT) / (count + PRIOR_WEIGHT)
