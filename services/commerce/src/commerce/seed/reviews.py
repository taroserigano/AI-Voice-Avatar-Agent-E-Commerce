"""Sample reviews for development, so product pages show ratings out of the box.

Every row is flagged ``is_sample`` and the storefront labels it "Sample review". The sample
reviewer accounts get a random password nobody knows, so they can't be signed in to.
Development only; safe to run repeatedly (existing reviews are left alone).
"""

from __future__ import annotations

import hashlib
import random
import secrets
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from commerce.auth.models import Role, User
from commerce.auth.sessions import hash_password
from commerce.catalog.models import Category, Product
from commerce.db import utcnow
from commerce.reviews.models import Review

SAMPLE_REVIEWERS: tuple[tuple[str, str], ...] = (
    ("maya.sample@example.com", "Maya Okafor"),
    ("jordan.sample@example.com", "Jordan Lee"),
    ("priya.sample@example.com", "Priya Nair"),
    ("diego.sample@example.com", "Diego Alvarez"),
    ("hannah.sample@example.com", "Hannah Schmidt"),
    ("marcus.sample@example.com", "Marcus Bell"),
    ("sofia.sample@example.com", "Sofia Rossi"),
    ("kenji.sample@example.com", "Kenji Watanabe"),
)

# (title, body) by star rating. "{thing}" is a short, category-flavored noun.
_TEXT: dict[int, tuple[tuple[str, str], ...]] = {
    5: (
        (
            "Exactly what I hoped for",
            "Great quality for the price. The {thing} feels well made and it arrived quickly. "
            "Would buy again.",
        ),
        ("Love it", "I've used it almost every day since it arrived. Easy to recommend."),
        (
            "Better than expected",
            "Honestly surprised by how nice this {thing} is. The details are thoughtful.",
        ),
        ("Five stars", "Does exactly what it says. No complaints at all."),
    ),
    4: (
        ("Really good", "Solid {thing}. Only small nitpicks, but overall very happy with it."),
        (
            "Great value",
            "Works well and looks good. Took a day or two to get used to, but I'd buy it again.",
        ),
        ("Happy with this", "Nice quality. I'd give it five stars if it came in more colors."),
    ),
    3: (
        ("It's okay", "Does the job. The {thing} is fine, just not special."),
        ("Mixed feelings", "Some things I like, some I don't. Fair for the price."),
    ),
    2: (
        (
            "Not for me",
            "Smaller than I expected, and the finish could be better. Returns were easy, though.",
        ),
    ),
    1: (("Disappointed", "Didn't meet my expectations. Support was helpful when I reached out."),),
}

_THING = {
    "electronics": "device",
    "home-kitchen": "piece",
    "clothing-shoes": "fit",
    "outdoor": "gear",
    "sports": "gear",
    "toys": "toy",
    "beauty": "formula",
    "office": "design",
    "gift-cards": "gift",
}

# Mostly positive, like a real storefront, with a few honest low ratings.
_RATING_WEIGHTS = ((5, 52), (4, 28), (3, 11), (2, 5), (1, 4))


def _rng(slug: str) -> random.Random:
    # Deterministic per product, so re-seeding produces the same catalog every time.
    seed = int(hashlib.sha256(slug.encode()).hexdigest()[:12], 16)
    return random.Random(seed)  # noqa: S311 - picks demo text, not a secret


def _sample_users(db: Session) -> list[User]:
    users = []
    for email, name in SAMPLE_REVIEWERS:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(
                email=email,
                display_name=name,
                role=Role.CUSTOMER,
                password_hash=hash_password(secrets.token_urlsafe(32)),
            )
            db.add(user)
        users.append(user)
    db.flush()
    return users


def seed_sample_reviews(db: Session) -> int:
    users = _sample_users(db)
    now = utcnow()
    created = 0
    rows = db.execute(
        select(Product.id, Product.slug, Category.slug)
        .join(Category, Category.id == Product.category_id)
        .where(Product.is_active.is_(True))
        .order_by(Product.slug)
    ).all()
    stars, weights = zip(*_RATING_WEIGHTS, strict=True)
    for product_id, slug, category in rows:
        rng = _rng(slug)
        reviewers = rng.sample(users, k=rng.randint(2, 6))
        for n, user in enumerate(reviewers):
            rating = rng.choices(stars, weights=weights)[0]
            title, body = rng.choice(_TEXT[rating])
            written = now - timedelta(days=rng.randint(3, 240), minutes=n * 37)
            inserted = db.execute(
                insert(Review)
                .values(
                    product_id=product_id,
                    user_id=user.id,
                    rating=rating,
                    title=title,
                    body=body.format(thing=_THING.get(category, "item")),
                    is_sample=True,
                    created_at=written,
                    updated_at=written,
                )
                .on_conflict_do_nothing(index_elements=[Review.product_id, Review.user_id])
                .returning(Review.id)
            )
            created += len(inserted.all())
    return created
