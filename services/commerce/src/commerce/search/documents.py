"""The search projection of a product. Never holds price or stock: those come from PostgreSQL."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from commerce.catalog.models import Product


@dataclass(frozen=True)
class ProductSearchDoc:
    id: str
    title: str
    brand: str
    category_slug: str
    category_name: str
    description: str
    skus: list[str]
    variant_text: str

    def semantic_text(self) -> str:
        """The text Pinecone embeds: what the product *is*, in plain words."""
        return (
            f"{self.title}. Brand: {self.brand}. Category: {self.category_name}. "
            f"Options: {self.variant_text}. {self.description}"
        )


def doc_from_product(product: Product) -> ProductSearchDoc:
    variants = [v for v in product.variants if v.is_active]
    return ProductSearchDoc(
        id=str(product.id),
        title=product.title,
        brand=product.brand,
        category_slug=product.category.slug,
        category_name=product.category.name,
        description=product.description,
        skus=[v.sku for v in variants],
        variant_text=", ".join(v.name for v in variants),
    )


def load_docs(db: Session, product_ids: list[str] | None = None) -> list[ProductSearchDoc]:
    stmt = (
        select(Product)
        .options(selectinload(Product.variants), selectinload(Product.category))
        .where(Product.is_active.is_(True))
    )
    if product_ids is not None:
        stmt = stmt.where(Product.id.in_(product_ids))
    return [doc_from_product(p) for p in db.scalars(stmt)]
