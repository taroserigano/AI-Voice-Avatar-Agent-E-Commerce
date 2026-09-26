"""Seed categories, products, stock, stores, and (in development) accounts and their order
history. Safe to run repeatedly.

Every product it creates or changes gets a ``product.upserted`` outbox event in the same
transaction, so the outbox publisher indexes it into OpenSearch and Pinecone.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import delete, select
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
from commerce.db import get_sessionmaker, utcnow
from commerce.orders.models import Order, OrderLine
from commerce.outbox.service import PRODUCT_UPSERTED, emit
from commerce.seed.catalog import PRODUCTS
from commerce.seed.data import CATEGORIES, DEV_USERS
from commerce.seed.orders import DEV_ORDERS, POLICY_VERSION, build_order
from commerce.seed.stores import STORES
from commerce.stores.models import Store

log = logging.getLogger(__name__)

MAIN_LOCATION = ("MAIN", "Main warehouse")


def make_sku(slug: str, variant_code: str) -> str:
    """e.g. ("sonora-arc-wireless-headphones", "MID") -> "SON-ARC-WIR-HEA-MID"."""
    parts = [part[:3].upper() for part in slug.split("-")[:4]]
    return "-".join([*parts, variant_code.upper()])


def _assign(row: Any, values: dict[str, Any]) -> bool:
    """Set attributes on ``row``; True if anything changed."""
    changed = False
    for key, value in values.items():
        if getattr(row, key) != value:
            setattr(row, key, value)
            changed = True
    return changed


def seed_catalog(db: Session) -> dict[str, int]:
    location = db.scalar(select(StockLocation).where(StockLocation.code == MAIN_LOCATION[0]))
    if location is None:
        location = StockLocation(code=MAIN_LOCATION[0], name=MAIN_LOCATION[1])
        db.add(location)
        db.flush()

    categories = {c.slug: c for c in db.scalars(select(Category))}
    for order, c in enumerate(CATEGORIES):
        row = categories.get(c.slug)
        if row is None:
            row = categories[c.slug] = Category(slug=c.slug)
            db.add(row)
        row.name, row.policy_class, row.sort_order = c.name, c.policy_class, order
    db.flush()

    # Load everything once: a few thousand rows, far cheaper than a query per product.
    products = {p.slug: p for p in db.scalars(select(Product))}
    variants = {v.sku: v for v in db.scalars(select(Variant))}
    prices = {p.variant_id: p for p in db.scalars(select(Price))}
    balances = {
        b.variant_id
        for b in db.scalars(
            select(InventoryBalance).where(InventoryBalance.location_id == location.id)
        )
    }

    created = changed = 0
    for p in PRODUCTS:
        product = products.get(p.slug)
        is_new = product is None
        if product is None:
            product = Product(slug=p.slug)
            db.add(product)
            created += 1
        dirty = _assign(
            product,
            {
                "title": p.title,
                "brand": p.brand,
                "description": p.description,
                "category_id": categories[p.category].id,
                "image_path": p.image_path or f"/images/products/{p.slug}.svg",
                "is_active": True,
                "product_type": p.product_type,
                "tags": list(p.tags),
                "details": p.details(),
            },
        )
        db.flush()

        for order, v in enumerate(p.variants):
            sku = v.sku or make_sku(p.slug, v.code)
            variant = variants.get(sku)
            if variant is None:
                variant = Variant(product_id=product.id, sku=sku)
                db.add(variant)
                dirty = True
            dirty |= _assign(
                variant,
                {
                    "name": v.name,
                    "attributes": v.attributes,
                    "sort_order": order,
                    "is_active": True,
                },
            )
            db.flush()

            price = prices.get(variant.id)
            if price is None:
                price = Price(variant_id=variant.id, currency="USD")
                db.add(price)
            price.amount_minor = v.price_cents or p.price_cents

            # Stock is set once; later runs leave live stock (and reservations) alone.
            if variant.id not in balances:
                db.add(
                    InventoryBalance(
                        variant_id=variant.id, location_id=location.id, on_hand=v.stock, reserved=0
                    )
                )
        if is_new or dirty:
            emit(db, PRODUCT_UPSERTED, str(product.id))
            changed += not is_new
    return {
        "products": len(PRODUCTS),
        "products_created": created,
        "products_updated": changed,
        "categories": len(CATEGORIES),
    }


def seed_stores(db: Session) -> int:
    existing = {s.code: s for s in db.scalars(select(Store))}
    for order, s in enumerate(STORES):
        row = existing.get(s.code)
        if row is None:
            row = Store(code=s.code)
            db.add(row)
        _assign(
            row,
            {
                "name": s.name,
                "address_line1": s.address_line1,
                "city": s.city,
                "state": s.state,
                "postal_code": s.postal_code,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "phone": s.phone,
                "hours": s.hours,
                "services": list(s.services),
                "sort_order": order,
                "is_active": True,
            },
        )
    return len(STORES)


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


def seed_dev_orders(db: Session) -> int:
    """Reset the development accounts' scenario orders: same IDs, dates relative to now.

    Rows are updated in place, never deleted and recreated, so records that point at these
    orders and lines (payments, shipments, earlier returns) stay valid across reseeds.
    """
    catalog = {p.slug: p for p in PRODUCTS}
    users = {u.email: u.id for u in db.scalars(select(User))}
    skus = {v.sku: v.id for v in db.scalars(select(Variant))}
    now = utcnow()
    for b in (build_order(spec, catalog, now) for spec in DEV_ORDERS):
        order = db.get(Order, b.id)
        if order is None:
            order = Order(id=b.id)
            db.add(order)
        _assign(
            order,
            {
                "user_id": users[normalize_email(b.spec.email)],
                "status": b.spec.status,
                "currency": "USD",
                "subtotal_minor": b.subtotal_minor,
                "discount_minor": b.discount_minor,
                "tax_minor": b.tax_minor,
                "shipping_minor": b.shipping_minor,
                "total_minor": b.total_minor,
                "placed_at": b.placed_at,
                "delivered_at": b.delivered_at,
            },
        )
        for ln in b.lines:
            line = db.get(OrderLine, ln.id)
            if line is None:
                line = OrderLine(id=ln.id, order_id=b.id)
                db.add(line)
            sku = ln.variant.sku or make_sku(ln.product.slug, ln.variant.code)
            _assign(
                line,
                {
                    "order_id": b.id,
                    "variant_id": skus[sku],
                    "product_title": ln.product.title,
                    "variant_name": ln.variant.name,
                    "sku": sku,
                    "image_path": ln.product.image_path
                    or f"/images/products/{ln.product.slug}.svg",
                    "policy_class": ln.policy_class.value,
                    "policy_version": POLICY_VERSION,
                    "quantity": ln.quantity,
                    "unit_price_minor": ln.unit_price_minor,
                    "amount_discount_minor": ln.discount_minor,
                    "amount_tax_minor": ln.tax_minor,
                    "amount_total_minor": ln.total_minor,
                },
            )
        # A line dropped from a scenario goes away; the others keep their IDs.
        db.execute(
            delete(OrderLine).where(
                OrderLine.order_id == b.id, OrderLine.id.not_in([ln.id for ln in b.lines])
            )
        )
    db.flush()
    return len(DEV_ORDERS)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    with get_sessionmaker()() as db:
        result = seed_catalog(db)
        result["stores"] = seed_stores(db)
        if settings.is_dev:
            result["dev_users_created"] = seed_dev_users(db)
            db.flush()
            result["dev_orders"] = seed_dev_orders(db)
        else:
            log.info("APP_ENV=%s: skipping development accounts and orders", settings.app_env)
        db.commit()
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
