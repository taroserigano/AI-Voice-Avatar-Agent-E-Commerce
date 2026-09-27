from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from commerce.db import Base, Timestamps, UUIDPk, utcnow


class PolicyClass(enum.StrEnum):
    """How the sandbox return policy treats a category (see PRODUCT_REQUIREMENTS.md)."""

    STANDARD = "standard"
    INSPECTION = "inspection"  # e.g. Electronics: refund after warehouse inspection
    FINAL_SALE = "final_sale"  # e.g. Gift cards: not returnable
    # Fresh and frozen food: not sent back; a damaged or spoiled item reported within
    # 7 days of delivery is refunded without a return shipment.
    PERISHABLE = "perishable"


class Category(UUIDPk, Base):
    __tablename__ = "categories"

    slug: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    policy_class: Mapped[PolicyClass] = mapped_column(
        Enum(PolicyClass, name="policy_class", values_callable=lambda e: [m.value for m in e]),
        default=PolicyClass.STANDARD,
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    products: Mapped[list[Product]] = relationship(back_populates="category")


class Product(UUIDPk, Timestamps, Base):
    __tablename__ = "products"
    __table_args__ = (Index("ix_products_tags", "tags", postgresql_using="gin"),)

    slug: Mapped[str] = mapped_column(String(160), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    brand: Mapped[str] = mapped_column(String(120), index=True)
    description: Mapped[str] = mapped_column(Text)
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("categories.id"), index=True)
    image_path: Mapped[str] = mapped_column(String(300))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # What a shopper would call it ("milk", "yogurt", "headphones"): groups products across
    # brands for filters and for the assistant's structured search.
    product_type: Mapped[str] = mapped_column(String(80), default="general", index=True)
    # Controlled vocabulary in catalog/tags.py ("organic", "fat-free", "wireless", ...).
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(40)), default=list)
    # Nutrition facts, ingredients, allergens, and specs (see catalog.schemas.ProductDetail).
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    category: Mapped[Category] = relationship(back_populates="products")
    variants: Mapped[list[Variant]] = relationship(
        back_populates="product", order_by="[Variant.sort_order, Variant.sku]"
    )


class Variant(UUIDPk, Base):
    """The purchasable unit. IDs stay stable even when names change."""

    __tablename__ = "variants"

    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), index=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    attributes: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    product: Mapped[Product] = relationship(back_populates="variants")
    price: Mapped[Price | None] = relationship(back_populates="variant", uselist=False)
    balances: Mapped[list[InventoryBalance]] = relationship(back_populates="variant")


class Price(UUIDPk, Base):
    """The one current price per variant and currency. Always the authority for totals."""

    __tablename__ = "prices"
    __table_args__ = (
        UniqueConstraint("variant_id", "currency"),
        CheckConstraint("amount_minor > 0", name="positive_amount"),
    )

    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("variants.id"))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    amount_minor: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    variant: Mapped[Variant] = relationship(back_populates="price")


class StockLocation(UUIDPk, Base):
    __tablename__ = "stock_locations"

    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(120))


class InventoryBalance(UUIDPk, Base):
    """One current balance per variant and location. ``reserved`` never exceeds ``on_hand``."""

    __tablename__ = "inventory_balances"
    __table_args__ = (
        UniqueConstraint("variant_id", "location_id"),
        CheckConstraint("on_hand >= 0", name="on_hand_non_negative"),
        CheckConstraint("reserved >= 0", name="reserved_non_negative"),
        CheckConstraint("reserved <= on_hand", name="reserved_within_on_hand"),
    )

    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("variants.id"))
    location_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stock_locations.id"))
    on_hand: Mapped[int] = mapped_column(Integer, default=0)
    reserved: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    variant: Mapped[Variant] = relationship(back_populates="balances")

    @property
    def available(self) -> int:
        return self.on_hand - self.reserved
