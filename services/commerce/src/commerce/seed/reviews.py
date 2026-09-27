"""Sample reviews for development, so product pages show ratings out of the box.

Every row is flagged ``is_sample`` and the storefront labels it "Sample review". The sample
reviewer accounts get a random password nobody knows, so they can't be signed in to.

Review text is composed from the pools in ``review_text`` and ``review_text_families``:
an opener, a few details that suit the product's family and department, sometimes a line
about a fact the product really has (a tag such as "organic" or a spec such as its flavor),
and a closer. No sentence repeats within one product's reviews. Everything is drawn from an
RNG seeded by the product slug, so the same catalog always gets the same reviews.

Seeding is idempotent and refreshes in place: sample reviews are inserted, rewritten when the
text has changed, or removed when a product no longer gets them. Reviews written by real
shoppers (``is_sample`` false) are never touched. Development only.
"""

from __future__ import annotations

import hashlib
import logging
import random
import re
import secrets
import string
import uuid
from collections import defaultdict
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from sqlalchemy import delete, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from commerce.auth.models import Role, User
from commerce.auth.sessions import hash_password
from commerce.catalog.models import Category, Product, Variant
from commerce.db import utcnow
from commerce.reviews.models import Review
from commerce.seed import review_text as text
from commerce.seed.data import ProductSeed
from commerce.seed.review_text_families import FAMILIES, FAMILY_OF_TYPE, FAMILY_OVERRIDES

log = logging.getLogger(__name__)

SAMPLE_REVIEWERS = text.REVIEWERS
MAX_REVIEWS = 12

# Ratings from 5 down to 1. Each product draws a quality tier, so products differ.
_QUALITY_TIERS: tuple[tuple[int, tuple[int, ...]], ...] = (
    (30, (72, 20, 5, 2, 1)),  # a standout
    (52, (50, 32, 10, 5, 3)),  # solid
    (18, (28, 30, 22, 11, 9)),  # divisive
)
_STARS = (5, 4, 3, 2, 1)
# How often a review opens with a lead-in sentence and ends with a sign-off, by rating.
_OPEN_CHANCE = {5: 0.6, 4: 0.5, 3: 0.7, 2: 0.6, 1: 0.6}
_CLOSE_CHANCE = {5: 0.55, 4: 0.4, 3: 0.5, 2: 0.6, 1: 0.7}

_FIELDS = frozenset({
    "this", "This", "it", "It", "obj", "it_is", "is", "was", "has", "does", "s", "es", "noun", "brand",
    "flavor", "scent", "roast", "cheese", "material", "battery", "color", "size", "pet", "Pet",
})  # fmt: skip
_COND_KEYS = frozenset({"tag", "type", "dept", "title", "spec"})

# Spec values that aren't a flavor or scent worth naming.
_NOT_A_FLAVOR = ("plain", "original", "unflavored", "unsweetened", "barista")
_NOT_A_SCENT = ("unscented", "fragrance", "no added")
# A size label reads naturally after "the" when it ends in a container ("the 3 lb bag").
_CONTAINERS = frozenset({
    "bag", "box", "tub", "jar", "bottle", "can", "carton", "gallon", "canister", "loaf",
    "tray", "clamshell", "jug", "container", "package", "pint", "quart", "tin", "pouch",
})  # fmt: skip


# --- Parsing the text pools -------------------------------------------------------------------


@dataclass(frozen=True)
class _Cond:
    key: str
    negate: bool
    values: tuple[str, ...]
    spec: str | None = None


@dataclass(frozen=True)
class Line:
    text: str
    conds: tuple[_Cond, ...] = ()
    fields: frozenset[str] = frozenset()
    topic: str | None = None  # at most one line per topic in a review


def parse_line(raw: str) -> Line:
    """``"[tag:organic;!type:milk] Some {noun}."`` -> Line (see ``review_text`` for syntax)."""
    body, conds, topic = raw, [], None
    if raw.startswith("["):
        end = raw.index("]")
        for part in raw[1:end].split(";"):
            if part.startswith("#"):
                topic = part[1:]
                continue
            negate = part.startswith("!")
            key, _, rest = part.lstrip("!").partition(":")
            if key not in _COND_KEYS:
                raise ValueError(f"unknown condition {key!r} in {raw!r}")
            spec = None
            if key == "spec":
                spec, eq, rest = rest.partition("=")
                spec = spec.lower()
                values = tuple(v.lower() for v in rest.split("|")) if eq else ()
            else:
                values = tuple(v.lower() for v in rest.split("|"))
            conds.append(_Cond(key, negate, values, spec))
        body = raw[end + 1 :].strip()
    fields = frozenset(name for _, name, _, _ in string.Formatter().parse(body) if name)
    if fields - _FIELDS:
        raise ValueError(f"unknown placeholder {sorted(fields - _FIELDS)} in {raw!r}")
    return Line(body, tuple(conds), fields, topic)


@dataclass(frozen=True)
class _Pool:
    pos: tuple[Line, ...]
    meh: tuple[Line, ...]
    neg: tuple[Line, ...]
    tpos: tuple[Line, ...]
    kind: str


def _lines(raw: Sequence[str]) -> tuple[Line, ...]:
    return tuple(parse_line(r) for r in raw)


def _pool(p: text.Pool) -> _Pool:
    return _Pool(_lines(p.pos), _lines(p.meh), _lines(p.neg), _lines(p.tpos), p.kind)


def _register(raw: Mapping[str, Sequence[str]]) -> dict[str, tuple[Line, ...]]:
    return {k: _lines(v) for k, v in raw.items()}


_FAMILY_POOLS = {k: _pool(v) for k, v in FAMILIES.items()}
_DEPT_POOLS = {k: _pool(v) for k, v in text.DEPARTMENTS.items()}
_KIND_POOLS = {k: _pool(v) for k, v in text.KIND_POOLS.items()}
_OPEN = {
    "pos": _register(text.OPEN_POS),
    "mixed": _register(text.OPEN_MIXED),
    "neg": _register(text.OPEN_NEG),
}
_CLOSE = {
    "pos": _register(text.CLOSE_POS),
    "mixed": _register(text.CLOSE_MIXED),
    "neg": _register(text.CLOSE_NEG),
}
_SOFT = _register(text.SOFT)
_TITLES = {stars: _lines(v) for stars, v in text.TITLES.items()}
_TITLES_NITPICK = _lines(text.TITLES_NITPICK)
_FACTS = _lines(text.FACT_LINES)
_EMPTY = _Pool((), (), (), (), "durable")


# --- Product facts ----------------------------------------------------------------------------


@dataclass(frozen=True)
class ProductFacts:
    """What the composer may say about a product: catalog data only, nothing invented."""

    slug: str
    title: str
    brand: str
    category: str
    product_type: str
    tags: tuple[str, ...] = ()
    specs: Mapping[str, str] = field(default_factory=dict)
    # (variant name, variant attributes), in display order.
    variants: tuple[tuple[str, Mapping[str, Any]], ...] = ()

    @classmethod
    def from_seed(cls, p: ProductSeed) -> ProductFacts:
        return cls(
            slug=p.slug,
            title=p.title,
            brand=p.brand,
            category=p.category,
            product_type=p.product_type,
            tags=p.tags,
            specs=dict(p.specs),
            variants=tuple((v.name, dict(v.attributes)) for v in p.variants),
        )


def family_of(category: str, product_type: str) -> str | None:
    return FAMILY_OVERRIDES.get((category, product_type)) or FAMILY_OF_TYPE.get(product_type)


def noun_for(facts: ProductFacts) -> str:
    title = facts.title.lower()
    for keyword, noun in text.TITLE_NOUNS.get(facts.product_type, ()):
        if keyword in title:
            return noun
    if facts.product_type in text.NOUNS:
        return text.NOUNS[facts.product_type]
    if facts.product_type in ("", "general"):
        return "item"
    return facts.product_type.replace("-", " ")


def _is_plural(noun: str) -> bool:
    last = noun.split()[-1].lower()
    return last.endswith("s") and not last.endswith("ss") and last not in text.SINGULAR_NOUNS


def _strip_parens(value: str) -> str:
    return re.sub(r"\s*\([^)]*\)", "", value).strip()


def _lower_first(value: str) -> str:
    return value[:1].lower() + value[1:]


def _fields(facts: ProductFacts) -> dict[str, str | tuple[str, ...]]:
    noun = noun_for(facts)
    plural = _is_plural(noun)
    this = f"{'these' if plural else 'this'} {noun}"
    fields: dict[str, str | tuple[str, ...]] = {
        "noun": noun,
        "this": this,
        "This": this[0].upper() + this[1:],
        "it": "they" if plural else "it",
        "It": "They" if plural else "It",
        "obj": "them" if plural else "it",
        "it_is": "they're" if plural else "it's",
        "is": "are" if plural else "is",
        "was": "were" if plural else "was",
        "has": "have" if plural else "has",
        "does": "do" if plural else "does",
        "s": "" if plural else "s",
        "es": "" if plural else "es",
        "brand": facts.brand,
    }
    specs = {k.lower(): str(v) for k, v in facts.specs.items()}
    flavor = specs.get("flavor", "")
    if flavor and not any(w in flavor.lower() for w in _NOT_A_FLAVOR):
        fields["flavor"] = flavor.lower()
    scent = _strip_parens(specs.get("scent", ""))
    if scent and not any(w in scent.lower() for w in _NOT_A_SCENT):
        fields["scent"] = scent.lower()
    if specs.get("roast"):
        fields["roast"] = specs["roast"].lower()
    if specs.get("cheese"):
        fields["cheese"] = specs["cheese"].lower()
    material = specs.get("material", "")
    if material and "," not in material:
        fields["material"] = _lower_first(material)
    battery = _strip_parens(specs.get("battery life", ""))
    battery = re.sub(r"^up to\s+", "", battery, flags=re.IGNORECASE)
    if battery and battery[0].isdigit():
        fields["battery"] = battery
    colors = tuple(dict.fromkeys(str(a["color"]) for _, a in facts.variants if a.get("color")))
    if colors:
        fields["color"] = colors
    sizes = tuple(
        dict.fromkeys(
            _lower_first(label)
            for label in (_strip_parens(str(a.get("size", ""))) for _, a in facts.variants)
            if label and " x " not in label and label.split()[-1].lower() in _CONTAINERS
        )
    )
    if len(sizes) >= 2:
        fields["size"] = sizes
    pet = _pet(facts, specs)
    if pet:
        fields["pet"], fields["Pet"] = f"my {pet}", f"My {pet}"
    return fields


def _pet(facts: ProductFacts, specs: Mapping[str, str]) -> str | None:
    t, title, for_ = facts.product_type, facts.title.lower(), specs.get("for", "").lower()
    if t.startswith(("dog", "puppy", "poop")) or "dog" in for_ or "dog" in title:
        return "dog"
    if t.startswith(("cat", "litter")) or "cat" in for_ or re.search(r"\bcats?\b", title):
        return "cat"
    return None


@dataclass
class _Context:
    facts: ProductFacts
    tags: frozenset[str]
    title: str
    specs: dict[str, str]
    fields: dict[str, str | tuple[str, ...]]

    def allows(self, line: Line) -> bool:
        for c in line.conds:
            if c.key == "tag":
                hit = any(v in self.tags for v in c.values)
            elif c.key == "type":
                hit = self.facts.product_type in c.values
            elif c.key == "dept":
                hit = self.facts.category in c.values
            elif c.key == "title":
                hit = any(v in self.title for v in c.values)
            else:
                value = self.specs.get(c.spec or "")
                hit = value is not None and (not c.values or any(v in value for v in c.values))
            if hit == c.negate:
                return False
        return line.fields <= self.fields.keys()


Weighted = list[tuple[Line, int]]


class _Composer:
    """Picks lines for one product, never using a line or a sentence twice."""

    def __init__(self, facts: ProductFacts, rng: random.Random) -> None:
        self.rng = rng
        self.ctx = _Context(
            facts=facts,
            tags=frozenset(facts.tags),
            title=facts.title.lower(),
            specs={k.lower(): str(v).lower() for k, v in facts.specs.items()},
            fields=_fields(facts),
        )
        family = family_of(facts.category, facts.product_type)
        fam = _FAMILY_POOLS.get(family or "", _EMPTY)
        dept = _DEPT_POOLS.get(facts.category, _EMPTY)
        self.kind = fam.kind if family else _default_kind(facts.category)
        kind = _KIND_POOLS.get(self.kind, _EMPTY)
        tiers = (fam, 3), (dept, 2), (kind, 1)
        self.pos = self._weighted([(p.pos, w) for p, w in tiers])
        self.meh = self._weighted([(p.meh, w) for p, w in tiers])
        self.neg = self._weighted([(p.neg, w) for p, w in tiers])
        self.tpos = self._weighted([(fam.tpos, 2), (dept.tpos, 2)])
        self.facts = self._weighted([(_FACTS, 1)])
        self.open = {k: self._weighted([(self._by_kind(v), 1)]) for k, v in _OPEN.items()}
        self.close = {k: self._weighted([(self._by_kind(v), 1)]) for k, v in _CLOSE.items()}
        self.soft = self._weighted([(self._by_kind(_SOFT), 1)])
        self.used_lines: set[Line] = set()
        self.used_text: set[str] = set()
        self.topics: set[str] = set()  # topics already covered in the current review

    def _by_kind(self, register: Mapping[str, tuple[Line, ...]]) -> tuple[Line, ...]:
        if self.kind == "gift":
            return register.get("gift", ())
        repeat = register.get("repeat", ()) if self.kind in ("food", "consumable") else ()
        return register.get("all", ()) + repeat + register.get(self.kind, ())

    def _weighted(self, groups: Sequence[tuple[Sequence[Line], int]]) -> Weighted:
        out: Weighted = []
        for lines, weight in groups:
            out.extend((line, weight) for line in lines if self.ctx.allows(line))
        return out

    def pick(self, options: Weighted) -> str | None:
        options = [
            (line, w)
            for line, w in options
            if line not in self.used_lines and line.topic not in self.topics
        ]
        while options:
            line = self.rng.choices([o[0] for o in options], [o[1] for o in options])[0]
            rendered = self._render(line)
            if rendered not in self.used_text:
                self.used_lines.add(line)
                self.used_text.add(rendered)
                if line.topic:
                    self.topics.add(line.topic)
                return rendered
            options = [o for o in options if o[0] is not line]
        return None

    def _render(self, line: Line) -> str:
        values: dict[str, str] = {}
        for name in sorted(line.fields):
            value = self.ctx.fields[name]
            values[name] = value if isinstance(value, str) else self.rng.choice(value)
        return line.text.format(**values)

    def title(self, rating: int, nitpick: bool) -> str | None:
        """Chosen after the body: a 4-star title like "Minor nitpicks" needs a nitpick."""
        options = self.tpos if rating >= 4 else []
        if rating == 4 and nitpick:
            options = options + self._weighted([(_TITLES_NITPICK, 3)])
        return self.pick(options + self._weighted([(_TITLES[rating], 1)]))

    def body(self, rating: int) -> tuple[str, bool]:
        """Opener, details, closer, and whether a nitpick made it in. Each slot is optional,
        but a body has at least two sentences unless the pools have run dry."""
        r = self.rng
        self.topics = set()
        nitpick: str | None = None
        sentiment = "pos" if rating >= 4 else "mixed" if rating == 3 else "neg"
        opener = self.pick(self.open[sentiment]) if r.random() < _OPEN_CHANCE[rating] else None
        details: list[str | None] = []
        if rating == 5:
            details += [self.pick(self.pos) for _ in range(r.choice((1, 1, 2, 2)))]
            if r.random() < 0.4:
                details.append(self.pick(self.facts))
            extra = [self.pos, self.facts]
        elif rating == 4:
            details += [self.pick(self.pos) for _ in range(r.choice((1, 1, 2)))]
            if r.random() < 0.3:
                details.append(self.pick(self.facts))
            if r.random() < 0.6:
                nitpick = self.pick(self.meh)
                details.append(nitpick)
            extra = [self.pos, self.facts]
        elif rating == 3:
            if r.random() < 0.8:
                details.append(self.pick(self.pos))
            details += [self.pick(self.meh) for _ in range(r.choice((1, 1, 2)))]
            extra = [self.meh]
        elif rating == 2:
            details.append(self.pick(self.neg))
            if r.random() < 0.5:
                details.append(self.pick(self.meh))
            if r.random() < 0.35:
                details.append(self.pick(self.soft))
            extra = [self.neg, self.meh]
        else:
            details += [self.pick(self.neg) for _ in range(r.choice((1, 2)))]
            extra = [self.neg]
        closer = self.pick(self.close[sentiment]) if r.random() < _CLOSE_CHANCE[rating] else None
        middle = [d for d in details if d]
        for options in extra:
            if len(middle) + bool(opener) + bool(closer) >= 2:
                break
            if more := self.pick(options):
                middle.append(more)
        if len(middle) + bool(opener) + bool(closer) < 2:
            closer = closer or self.pick(self.close[sentiment])
            opener = opener or self.pick(self.open[sentiment])
        return " ".join(s for s in (opener, *middle, closer) if s), nitpick is not None


def _default_kind(category: str) -> str:
    if category in ("dairy-eggs", "produce", "meat-seafood", "bakery", "frozen", "pantry",
                    "snacks", "beverages"):  # fmt: skip
        return "food"
    if category in ("household", "health-wellness", "baby", "pet", "beauty"):
        return "consumable"
    return "gift" if category == "gift-cards" else "durable"


# --- Composing a product's reviews ------------------------------------------------------------


@dataclass(frozen=True)
class SampleReview:
    reviewer: int  # index into SAMPLE_REVIEWERS
    rating: int
    title: str | None
    body: str
    age: timedelta  # how long before the seed run it was "written"


def _rng(slug: str) -> random.Random:
    # Deterministic per product, so re-seeding produces the same reviews every time.
    seed = int(hashlib.sha256(slug.encode()).hexdigest()[:12], 16)
    return random.Random(seed)  # noqa: S311 - picks demo text, not a secret


def _review_count(rng: random.Random, product_type: str) -> int:
    if product_type in text.POPULAR_TYPES:
        return rng.randint(5, MAX_REVIEWS)
    if product_type in text.NICHE_TYPES:
        return rng.choices(range(5), weights=(25, 25, 20, 15, 15))[0]
    return rng.choices(range(10), weights=(5, 7, 10, 13, 14, 14, 12, 10, 8, 7))[0]


def compose_sample_reviews(facts: ProductFacts) -> list[SampleReview]:
    rng = _rng(facts.slug)
    count = _review_count(rng, facts.product_type)
    weights = rng.choices([t[1] for t in _QUALITY_TIERS], [t[0] for t in _QUALITY_TIERS])[0]
    reviewers = rng.sample(range(len(SAMPLE_REVIEWERS)), k=count)
    composer = _Composer(facts, rng)
    out = []
    for reviewer in reviewers:
        rating = rng.choices(_STARS, weights=weights)[0]
        age = timedelta(days=rng.randint(2, 420), minutes=rng.randint(0, 1439))
        body, nitpick = composer.body(rating)
        out.append(
            SampleReview(
                reviewer=reviewer,
                rating=rating,
                title=composer.title(rating, nitpick),
                body=body,
                age=age,
            )
        )
    return out


# --- Database ---------------------------------------------------------------------------------


def _sample_users(db: Session) -> list[User]:
    emails = [email for email, _ in SAMPLE_REVIEWERS]
    existing = {u.email: u for u in db.scalars(select(User).where(User.email.in_(emails)))}
    users, locked = [], ""
    for email, name in SAMPLE_REVIEWERS:
        user = existing.get(email)
        if user is None:
            # A hash of a random password that is thrown away: nobody can sign in as these.
            locked = locked or hash_password(secrets.token_urlsafe(32))
            user = User(email=email, display_name=name, role=Role.CUSTOMER, password_hash=locked)
            db.add(user)
        elif user.display_name != name:
            user.display_name = name
        users.append(user)
    db.flush()
    return users


def _active_products(db: Session) -> list[tuple[uuid.UUID, ProductFacts]]:
    variants: dict[uuid.UUID, list[tuple[str, Mapping[str, Any]]]] = defaultdict(list)
    for product_id, name, attributes in db.execute(
        select(Variant.product_id, Variant.name, Variant.attributes)
        .where(Variant.is_active.is_(True))
        .order_by(Variant.product_id, Variant.sort_order, Variant.name)
    ):
        variants[product_id].append((name, attributes or {}))
    rows = db.execute(
        select(
            Product.id,
            Product.slug,
            Product.title,
            Product.brand,
            Product.product_type,
            Product.tags,
            Product.details,
            Category.slug,
        )
        .join(Category, Category.id == Product.category_id)
        .where(Product.is_active.is_(True))
        .order_by(Product.slug)
    ).all()
    return [
        (
            pid,
            ProductFacts(
                slug=slug,
                title=title,
                brand=brand,
                category=category,
                product_type=product_type,
                tags=tuple(tags or ()),
                specs=dict((details or {}).get("specs") or {}),
                variants=tuple(variants[pid]),
            ),
        )
        for pid, slug, title, brand, product_type, tags, details, category in rows
    ]


def _chunks[T](items: Sequence[T], size: int = 1000) -> Iterator[Sequence[T]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def seed_sample_reviews(db: Session) -> int:
    """Bring the sample reviews in line with ``compose_sample_reviews``; returns rows created.

    Existing sample rows keep their id and date; their rating and text are rewritten when the
    composer's output changed. Sample rows the composer no longer produces are deleted. Rows
    with ``is_sample`` false (a real shopper's review) are never selected, updated, or deleted.
    """
    users = _sample_users(db)
    now = utcnow()
    products = _active_products(db)
    existing: dict[tuple[uuid.UUID, uuid.UUID], uuid.UUID] = {
        (product_id, user_id): review_id
        for review_id, product_id, user_id in db.execute(
            select(Review.id, Review.product_id, Review.user_id).where(Review.is_sample.is_(True))
        )
    }

    rows: list[dict[str, Any]] = []
    for product_id, facts in products:
        for review in compose_sample_reviews(facts):
            written = now - review.age
            rows.append(
                {
                    "id": uuid.uuid4(),
                    "product_id": product_id,
                    "user_id": users[review.reviewer].id,
                    "rating": review.rating,
                    "title": review.title,
                    "body": review.body,
                    "is_sample": True,
                    "created_at": written,
                    "updated_at": written,
                }
            )
    wanted = {(r["product_id"], r["user_id"]) for r in rows}
    created = len(wanted - existing.keys())

    changed = 0
    for batch in _chunks(rows):
        stmt = insert(Review).values(list(batch))
        upsert = stmt.on_conflict_do_update(
            index_elements=[Review.product_id, Review.user_id],
            set_={
                "rating": stmt.excluded.rating,
                "title": stmt.excluded.title,
                "body": stmt.excluded.body,
                # Keep the original date; no "Edited" label on seeded rows.
                "updated_at": Review.created_at,
            },
            where=Review.is_sample.is_(True)
            & or_(
                Review.rating != stmt.excluded.rating,
                Review.title.is_distinct_from(stmt.excluded.title),
                Review.body.is_distinct_from(stmt.excluded.body),
            ),
        ).returning(Review.id)
        changed += len(db.execute(upsert).all())

    active = {product_id for product_id, _ in products}
    stale = [rid for key, rid in existing.items() if key[0] in active and key not in wanted]
    for ids in _chunks(stale):
        db.execute(
            delete(Review)
            .where(Review.id.in_(ids), Review.is_sample.is_(True))
            .execution_options(synchronize_session=False)
        )
    log.info(
        "sample reviews: %d created, %d rewritten, %d removed",
        created,
        changed - created,
        len(stale),
    )
    return created
