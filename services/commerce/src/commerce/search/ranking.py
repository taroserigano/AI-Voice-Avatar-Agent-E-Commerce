"""Re-rank fused search candidates by how well each one matches the shopper's words.

Rank fusion (see :mod:`commerce.search.rrf`) only knows positions in two lists. Both lists
reach past the real matches: OpenSearch's typo tolerance can match a near spelling, and
Pinecone always returns its top K however weak. So after fusing, every candidate is checked
against the query's words, in plain Python on the text PostgreSQL already holds (title,
product type, brand, tag labels, description):

1. Products whose title, type, brand and tags contain every meaningful query word, and
   products whose type *is* what was asked for ("diapers" in "diapers size 3"), rank first.
2. Then partial matches, most words first; within a tier the fused order is kept.
3. When something matched well, candidates whose title, type, brand and tags share no word
   with the query are dropped: a fuzzy spelling ("Mild"), or the word only in a description
   (yogurt "made with milk"). Meaning-based hits that passed their leg's score cut stay, last.
4. When nothing matched well, candidates are kept only if they share a query word, have it
   in their description, are a close spelling of it (a typo: "bananna" keeps Bananas,
   "yoghurt" keeps yogurt), or passed the meaning leg's cut; the caller says they're only
   related items. Anything else goes: "ipad" in a store with no iPads keeps nothing rather
   than puppy pads and Pad Thai, so the shopper sees the empty state and its suggestions.

A close spelling follows OpenSearch's fuzziness in :mod:`commerce.search.keyword`: none for
words under 5 letters (so "ipad" is never "pad", "milk" never "mild"), one edit for 5-7
letters, two for longer words, and the first letter must match.

Numbers and sizes ("3", "size", "12 oz") don't decide the tier: "diapers size 3" is a
diapers query, not a query for anything labeled 3.
"""

from __future__ import annotations

import re
from collections.abc import Hashable, Iterable, Sequence
from dataclasses import dataclass
from functools import lru_cache

from commerce.search.keyword import SYNONYMS

# OpenSearch's _english_ stopwords (the keyword leg ignores them too), plus the "s" left
# over from a possessive such as "women's".
# fmt: off
STOPWORDS = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "if", "in", "into", "is", "it",
    "no", "not", "of", "on", "or", "such", "that", "the", "their", "then", "there", "these",
    "they", "this", "to", "was", "will", "with", "s",
})
# Sizes and units: they narrow a query but don't say what the product is.
UNIT_WORDS = frozenset({
    "size", "sizes", "pack", "count", "ct", "oz", "fl", "lb", "lbs", "inch", "in", "ft", "pc",
    "piece", "pieces", "gb", "tb", "mm", "cm", "ml", "kg", "g", "x", "qt", "gal", "gallon",
})
# fmt: on
_WORD = re.compile(r"[a-z0-9]+")
_NUMBERISH = re.compile(r"^\d+[a-z]{0,2}$")  # 3, 64gb, 12oz, 2t


def stem(word: str) -> str:
    """A light English plural stemmer: enough that "diapers" matches "Diaper"."""
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and word.endswith(("ches", "shes", "sses", "xes")):
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]
    return word


def words(text: str) -> list[str]:
    """Lowercased, stemmed words without stopwords. Hyphenated words split: "lactose-free"."""
    return [stem(w) for w in _WORD.findall(text.lower()) if w not in STOPWORDS]


def _is_weak(word: str) -> bool:
    return word in UNIT_WORDS or bool(_NUMBERISH.match(word))


# Shortest word that tolerates one typo, and two. Keep in step with keyword.FUZZINESS.
TYPO_ONE_EDIT = 5
TYPO_TWO_EDITS = 8


def typo_edits(word: str) -> int:
    """Edits a word of this length may be off by and still count as the same word."""
    return 2 if len(word) >= TYPO_TWO_EDITS else 1 if len(word) >= TYPO_ONE_EDIT else 0


def _edit_distance(a: str, b: str, limit: int) -> int:
    """Levenshtein distance with adjacent swaps ("mlik"), or limit + 1 once it's past limit."""
    if abs(len(a) - len(b)) > limit:
        return limit + 1
    prev2: list[int] = []
    prev = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        cur = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            cost = int(a[i - 1] != b[j - 1])
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                cur[j] = min(cur[j], prev2[j - 2] + 1)
        if min(cur) > limit:
            return limit + 1
        prev2, prev = prev, cur
    return prev[-1]


@lru_cache(maxsize=65536)
def close_spelling(typed: str, word: str) -> bool:
    """`typed` is `word` or a typo of it: same first letter, within the edits its length
    allows."""
    if typed == word:
        return True
    edits = typo_edits(typed)
    if not edits or not word or typed[0] != word[0]:
        return False
    return _edit_distance(typed, word, edits) <= edits


@dataclass(frozen=True)
class Concept:
    """One thing the shopper asked for; any of its spellings counts ("tv" or "television")."""

    alternatives: tuple[tuple[str, ...], ...]
    weak: bool = False
    # A one-word concept's forms as typed and stemmed ("lactos", "lacto"), to test for typos.
    typed: tuple[str, ...] = ()

    def found_in(self, vocabulary: set[str]) -> bool:
        return any(all(w in vocabulary for w in alt) for alt in self.alternatives)

    def nearly_found_in(self, vocabulary: set[str]) -> bool:
        """Found, or a close spelling of it is ("bananna" in "Bananas")."""
        return self.found_in(vocabulary) or any(
            close_spelling(t, w) for t in self.typed for w in vocabulary
        )


def _synonym_groups() -> list[tuple[list[tuple[str, ...]], list[tuple[str, ...]]]]:
    """(spellings that trigger the group, spellings that count as a match) per synonym rule."""
    groups = []
    for rule in SYNONYMS:
        if "=>" in rule:
            lhs, rhs = rule.split("=>", 1)
            triggers = [tuple(words(v)) for v in lhs.split(",")]
            matches = [tuple(words(v)) for v in rhs.split(",")]
        else:
            triggers = matches = [tuple(words(v)) for v in rule.split(",")]
        triggers = [t for t in triggers if t]
        groups.append((sorted(triggers, key=len, reverse=True), [m for m in matches if m]))
    return groups


_GROUPS = _synonym_groups()


def parse_query(query: str) -> list[Concept]:
    raw = [w for w in _WORD.findall(query.lower()) if w not in STOPWORDS]
    tokens = [stem(w) for w in raw]
    concepts: list[Concept] = []
    i = 0
    while i < len(tokens):
        for triggers, matches in _GROUPS:
            hit = next((t for t in triggers if tuple(tokens[i : i + len(t)]) == t), None)
            if hit:
                concepts.append(Concept(tuple(dict.fromkeys([hit, *matches]))))
                i += len(hit)
                break
        else:
            forms = tuple(dict.fromkeys([raw[i], tokens[i]]))
            concepts.append(Concept(((tokens[i],),), weak=_is_weak(tokens[i]), typed=forms))
            i += 1
    return concepts


@dataclass(frozen=True)
class Candidate:
    id: Hashable
    title: str
    product_type: str  # slug, e.g. "plant-milk"
    brand: str = ""
    tag_labels: Sequence[str] = ()
    description: str = ""
    semantic: bool = False  # the meaning-based leg found it (and it passed that leg's score cut)


@dataclass(frozen=True)
class Ranking:
    ids: list[Hashable]  # kept candidates, best first
    dropped: int  # candidates removed for sharing no word with the query (rules 3 and 4)
    exact: bool  # something matched the query's words well


def rank_candidates(query: str, candidates: Iterable[Candidate]) -> Ranking:
    """Order candidates (given best-fused-first) by match quality; see the module docstring."""
    items = list(candidates)
    concepts = parse_query(query)
    if not concepts:
        return Ranking([c.id for c in items], 0, True)
    content = [c for c in concepts if not c.weak] or concepts
    query_words = {w for c in concepts for alt in c.alternatives for w in alt}

    rows = []
    strong = False
    for fused_rank, cand in enumerate(items):
        type_words = set(words(cand.product_type.replace("-", " ")))
        main = set(words(" ".join([cand.title, cand.brand, *cand.tag_labels]))) | type_words
        found = sum(1 for c in content if c.found_in(main))
        full = found == len(content)
        type_match = bool(type_words) and type_words <= query_words
        strong = strong or full or type_match
        rows.append((fused_rank, cand, type_words, main, found, full, type_match))

    scored = []
    for fused_rank, cand, type_words, main, found, full, type_match in rows:
        # Typos count only when nothing matched outright; next to real matches a near
        # spelling is noise ("bread" is one letter from "bead").
        near = found if strong else sum(1 for c in content if c.nearly_found_in(main))
        in_description = found == 0 and any(
            c.found_in(set(words(cand.description))) for c in content
        )
        key = (
            not full,
            not type_match,
            -found / len(content),
            -near / len(content),
            not (type_words & query_words),
            # Among products that share no word with the query: a word in the description,
            # then a meaning match, beat the rest.
            not in_description,
            not (found == 0 and cand.semantic),
            fused_rank,
        )
        if strong:
            unrelated = found == 0 and not cand.semantic
        else:
            unrelated = near == 0 and not in_description and not cand.semantic
        scored.append((key, unrelated, cand.id))

    scored.sort(key=lambda s: s[0])
    kept = [cid for _, unrelated, cid in scored if not unrelated]
    return Ranking(kept, len(scored) - len(kept), strong)
