"""Search-as-you-type suggestions, from PostgreSQL alone.

Every keystroke must answer fast, so this only does word-prefix matching in SQL ("lact"
matches "Lactose-Free"): no OpenSearch fuzziness and never a Pinecone call. When nothing
starts with what was typed, a word of 5 letters or more is corrected once against the
catalog's title words, with the same typo rule as search ("bananna" -> "banana"). It offers:

- completions: finished queries built from matching titles, e.g. "lactose-free milk"
  (the completed word plus the product type it's on);
- product types and departments whose names start with the typed words;
- a few matching products, with the live lowest price and stock from PostgreSQL.
"""

from __future__ import annotations

import re
import threading
import time
from collections import Counter
from typing import Any

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import Session

from commerce.catalog.display import type_label
from commerce.catalog.models import Category, Product
from commerce.catalog.schemas import (
    SearchSuggestions,
    SuggestedDepartment,
    SuggestedProduct,
    SuggestedType,
)
from commerce.catalog.service import product_offers
from commerce.money import DEFAULT_CURRENCY
from commerce.search.ranking import close_spelling, typo_edits

MIN_CHARS = 2
MAX_TOKENS = 6
TITLE_SCAN = 300  # matching titles read to build completions
PRODUCT_SCAN = 40  # matching products read before picking the best few
_TOKEN = re.compile(r"[a-z0-9]+")
# Words as shoppers read them in a title: "lactose-free" stays one word.
_TITLE_WORD = re.compile(r"[a-z0-9]+(?:['’-][a-z0-9]+)*")


VOCABULARY_TTL_S = 300.0
_vocabulary: tuple[float, Counter[str]] | None = None
_vocabulary_lock = threading.Lock()


def title_vocabulary(db: Session) -> Counter[str]:
    """Every word in active product titles and types, with how many products use it.
    Cached for a few minutes: a couple of thousand short rows, read only for corrections."""
    global _vocabulary
    now = time.monotonic()
    with _vocabulary_lock:
        if _vocabulary and now - _vocabulary[0] < VOCABULARY_TTL_S:
            return _vocabulary[1]
    rows = db.execute(
        select(Product.title, Product.product_type).where(Product.is_active.is_(True))
    ).all()
    counts: Counter[str] = Counter()
    for title, product_type in rows:
        counts.update(set(_TOKEN.findall(f"{title} {product_type}".lower())))
    with _vocabulary_lock:
        _vocabulary = (now, counts)
    return counts


def correct_tokens(tokens: list[str], vocabulary: Counter[str]) -> list[str] | None:
    """The tokens with typos fixed ("bananna" -> "banana"), or None if nothing changed.

    Only words of 5+ letters, same first letter, within search's typo rule. The last token
    may still be being typed, so it can also match the start of a longer word ("banann" ->
    "banana", "yoghur" -> "yogurt")."""
    fixed = list(tokens)
    for i, token in enumerate(tokens):
        if token in vocabulary or not typo_edits(token):
            continue
        typing = i == len(tokens) - 1
        best: tuple[int, int, str] | None = None
        for word, count in vocabulary.items():
            if word[0] != token[0]:
                continue
            if close_spelling(token, word):
                rank = (0, -count, word)
            elif typing and any(
                close_spelling(token, word[:n])
                for n in range(len(token) - 1, len(token) + 2)
                if n < len(word)
            ):
                rank = (1, -count, word)
            else:
                continue
            if best is None or rank < best:
                best = rank
        if best is not None:
            fixed[i] = best[2]
    return fixed if fixed != tokens else None


def query_tokens(query: str) -> list[str]:
    """Lowercase letters and digits only, so each token is safe inside a regex."""
    return _TOKEN.findall(query.lower())[:MAX_TOKENS]


def _word_prefixes(column: Any, tokens: list[str]) -> list[ColumnElement[bool]]:
    # PostgreSQL's \m is "start of a word": "lact" matches "Lactose-Free", not "Galactic".
    return [column.op("~*")(rf"\m{t}") for t in tokens]


def completed_word(title: str, last: str) -> str | None:
    """The first word of `title` that starts with the word being typed."""
    return next((w for w in _TITLE_WORD.findall(title.lower()) if w.startswith(last)), None)


def build_completions(rows: list[tuple[str, str]], tokens: list[str], limit: int) -> list[str]:
    """Completed queries from (title, product type) pairs that matched `tokens`.

    The last token is the word being typed. Each title offers the word it completes to
    ("lactose-free"), and that word with the product's type ("lactose-free milk"); the
    ones most titles agree on win.
    """
    head, last = tokens[:-1], tokens[-1]
    prefix = " ".join(head)
    counts: Counter[str] = Counter()
    for title, product_type in rows:
        label = type_label(product_type).lower()
        label_words = label.split()
        for segment in title.split(","):
            word = completed_word(segment, last)
            if word is None:
                continue
            counts[f"{prefix} {word}".strip()] += 1
            if word in label_words or word.rstrip("s") in label_words:
                phrase = label  # "milk" on a product of type "plant milk": offer "plant milk"
            elif not all(w in head for w in label_words):
                phrase = f"{word} {label}"
            else:
                break  # the type was already typed: "milk lact" -> just "milk lactose-free"
            counts[f"{prefix} {phrase}".strip()] += 1
            break
    typed = " ".join(tokens)
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], len(kv[0]), kv[0]))
    return [text for text, _ in ranked if text != typed][:limit]


def suggest(
    db: Session,
    query: str,
    *,
    completions: int = 5,
    product_types: int = 3,
    departments: int = 2,
    products: int = 4,
) -> SearchSuggestions:
    tokens = query_tokens(query)
    empty = SearchSuggestions(
        query=query, completions=[], product_types=[], departments=[], products=[]
    )
    if not tokens or len("".join(tokens)) < MIN_CHARS:
        return empty
    result = _suggest(db, query, tokens, completions, product_types, departments, products)
    if result.completions or result.products or result.product_types or result.departments:
        return result
    fixed = correct_tokens(tokens, title_vocabulary(db))
    if fixed is None:
        return result
    result = _suggest(db, query, fixed, completions, product_types, departments, products)
    corrected = " ".join(fixed)
    if (result.products or result.completions) and corrected not in result.completions:
        # "yoghur" offers "yogurt" itself first, not just longer phrases.
        result.completions = [corrected, *result.completions][:completions]
    return result


def _suggest(
    db: Session,
    query: str,
    tokens: list[str],
    completions: int,
    product_types: int,
    departments: int,
    products: int,
) -> SearchSuggestions:
    active = Product.is_active.is_(True)
    type_words = func.replace(Product.product_type, "-", " ")

    title_rows = db.execute(
        select(Product.title, Product.product_type)
        .where(active, *_word_prefixes(Product.title, tokens))
        .order_by(func.length(Product.title), Product.title)
        .limit(TITLE_SCAN)
    ).all()

    type_rows = db.execute(
        select(Product.product_type, Category.slug, Category.name, func.count())
        .join(Category, Category.id == Product.category_id)
        .where(active, *_word_prefixes(type_words, tokens))
        .group_by(Product.product_type, Category.slug, Category.name)
        .order_by(func.count().desc(), Product.product_type)
    ).all()
    types: dict[str, SuggestedType] = {}
    for value, slug, name, count in type_rows:
        if value in types:  # a type in two departments: link the bigger one, count both
            types[value].count += count
        else:
            types[value] = SuggestedType(
                value=value, label=type_label(value), category_slug=slug, category_name=name,
                count=count,
            )  # fmt: skip

    dept_rows = db.execute(
        select(Category.slug, Category.name)
        .where(*_word_prefixes(Category.name, tokens))
        .order_by(Category.sort_order)
        .limit(departments)
    ).all()

    # Products: every typed word starts a word of the title, brand, or type.
    haystack = func.concat_ws(" ", Product.title, Product.brand, type_words)
    is_type = type_words.op("~*")(rf"\m{' '.join(tokens)}")
    product_rows = db.execute(
        select(Product.id, Product.title, Product.brand, Product.image_path)
        .where(active, *_word_prefixes(haystack, tokens))
        .order_by(is_type.desc(), func.length(Product.title), Product.title)
        .limit(PRODUCT_SCAN)
    ).all()
    offers = product_offers(db, {r.id for r in product_rows})
    # In stock first, then products with the word most titles complete to ("mi": milk before
    # mint); otherwise the SQL order (type matches, then the shortest titles).
    popular = Counter(w for title, _ in title_rows if (w := completed_word(title, tokens[-1])))
    ranked = sorted(
        (r for r in product_rows if r.id in offers),
        key=lambda r: (
            not offers[r.id].in_stock,
            -popular[completed_word(r.title, tokens[-1]) or ""],
        ),
    )

    return SearchSuggestions(
        query=query,
        completions=build_completions([tuple(r) for r in title_rows], tokens, completions),
        product_types=sorted(types.values(), key=lambda t: -t.count)[:product_types],
        departments=[SuggestedDepartment(slug=s, name=n) for s, n in dept_rows],
        products=[
            SuggestedProduct(
                id=r.id,
                title=r.title,
                brand=r.brand,
                image_path=r.image_path,
                price_minor=offers[r.id].price_minor,
                currency=DEFAULT_CURRENCY,
                in_stock=offers[r.id].in_stock,
            )
            for r in ranked[:products]
        ],
    )
