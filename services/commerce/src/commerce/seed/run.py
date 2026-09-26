"""Seed categories, products, stock, and development accounts. Safe to run repeatedly.

Every product it creates or changes gets a ``product.upserted`` outbox event in the same
transaction, so the outbox publisher indexes it into OpenSearch and Pinecone.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce.auth.models import Role, User
from commerce.auth.sessions import hash_password, normalize_email
from commerce.catalog.models import (
    Category,
    InventoryBalance,
    Price,
    Product,
    StockLocation,
    Variant,
)
from commerce.config import get_settings
from commerce.db import get_sessionmaker
from commerce.outbox.service import PRODUCT_UPSERTED, emit
from commerce.seed.data import CATEGORIES, DEV_USERS, PRODUCTS
from commerce.seed.history import seed_order_history, seed_policy_versions
from commerce.seed.return_history import seed_return_history
from commerce.seed.reviews import seed_sample_reviews

log = logging.getLogger(__name__)

MAIN_LOCATION = ("MAIN", "Main warehouse")


def make_sku(slug: str, variant_code: str) -> str:
    """e.g. ("sonora-arc-wireless-headphones", "MID") -> "SON-ARC-WIR-HEA-MID"."""
    parts = [part[:3].upper() for part in slug.split("-")[:4]]
    return "-".join([*parts, variant_code.upper()])


def seed_catalog(db: Session) -> dict[str, int]:
    location = db.scalar(select(StockLocation).where(StockLocation.code == MAIN_LOCATION[0]))
    if location is None:
        location = StockLocation(code=MAIN_LOCATION[0], name=MAIN_LOCATION[1])
        db.add(location)
        db.flush()

    categories: dict[str, Category] = {}
    for order, c in enumerate(CATEGORIES):
        row = db.scalar(select(Category).where(Category.slug == c.slug))
        if row is None:
            row = Category(slug=c.slug)
            db.add(row)
        row.name, row.policy_class, row.sort_order = c.name, c.policy_class, order
        categories[c.slug] = row
    db.flush()

    created = 0
    for p in PRODUCTS:
        product = db.scalar(select(Product).where(Product.slug == p.slug))
        if product is None:
            product = Product(slug=p.slug)
            db.add(product)
            created += 1
        product.title = p.title
        product.brand = p.brand
        product.description = p.description
        product.category_id = categories[p.category].id
        product.image_path = f"/images/products/{p.slug}.svg"
        product.is_active = True
        db.flush()

        for order, v in enumerate(p.variants):
            sku = make_sku(p.slug, v.code)
            variant = db.scalar(select(Variant).where(Variant.sku == sku))
            if variant is None:
                variant = Variant(product_id=product.id, sku=sku)
                db.add(variant)
            variant.name, variant.attributes, variant.sort_order = v.name, v.attributes, order
            variant.is_active = True
            db.flush()

            price = db.scalar(select(Price).where(Price.variant_id == variant.id))
            if price is None:
                price = Price(variant_id=variant.id, currency="USD")
                db.add(price)
            price.amount_minor = v.price_cents or p.price_cents

            balance = db.scalar(
                select(InventoryBalance).where(
                    InventoryBalance.variant_id == variant.id,
                    InventoryBalance.location_id == location.id,
                )
            )
            if balance is None:
                db.add(
                    InventoryBalance(
                        variant_id=variant.id, location_id=location.id, on_hand=v.stock, reserved=0
                    )
                )
        emit(db, PRODUCT_UPSERTED, str(product.id))
    return {"products": len(PRODUCTS), "products_created": created, "categories": len(CATEGORIES)}


def seed_dev_users(db: Session) -> int:
    count = 0
    for u in DEV_USERS:
        email = normalize_email(u.email)
        if db.scalar(select(User).where(User.email == email)) is None:
            db.add(
                User(
                    email=email,
                    display_name=u.display_name,
                    role=Role(u.role),
                    password_hash=hash_password(u.password),
                )
            )
            count += 1
    return count


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    with get_sessionmaker()() as db:
        result = seed_catalog(db)
        seed_policy_versions(db)
        if settings.is_dev:
            result["dev_users_created"] = seed_dev_users(db)
            result["sample_reviews_created"] = seed_sample_reviews(db)
            # After any order seed: payments, tracking, activity, and support around the orders.
            for key, value in seed_order_history(db).items():
                result[f"history_{key}"] = value
            result["history_returns"] = seed_return_history(db)
        else:
            log.info(
                "APP_ENV=%s: skipping development accounts and sample reviews", settings.app_env
            )
        db.commit()
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
