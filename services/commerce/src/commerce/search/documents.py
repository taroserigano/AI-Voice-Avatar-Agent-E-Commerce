"""The search projection of a product. Never holds price or stock: those come from PostgreSQL."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from commerce.catalog.models import Product
from commerce.catalog.tags import tag_label


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
    product_type: str
    tags: list[str]
    tag_text: str  # the tags' shopper-facing labels, e.g. "Organic, Fat free"
    specs_text: str  # e.g. "Milkfat: 0%. Style: Greek."

    @property
    def type_text(self) -> str:
        return self.product_type.replace("-", " ")

    def semantic_text(self) -> str:
        """The text Pinecone embeds: what the product *is*, in plain words."""
        parts = [
            f"{self.title}. Brand: {self.brand}. Category: {self.category_name}.",
            f"Type: {self.type_text}.",
            f"Attributes: {self.tag_text}." if self.tag_text else "",
            self.specs_text,
            f"Options: {self.variant_text}.",
            self.description,
        ]
        return " ".join(p for p in parts if p)


def doc_from_product(product: Product) -> ProductSearchDoc:
    variants = [v for v in product.variants if v.is_active]
    specs = (product.details or {}).get("specs") or {}
    return ProductSearchDoc(
        id=str(product.id),
        title=product.title,
        brand=product.brand,
        category_slug=product.category.slug,
        category_name=product.category.name,
        description=product.description,
        skus=[v.sku for v in variants],
        variant_text=", ".join(v.name for v in variants),
        product_type=product.product_type,
        tags=list(product.tags or []),
        tag_text=", ".join(tag_label(t) for t in product.tags or []),
        specs_text=" ".join(f"{k}: {v}." for k, v in specs.items() if k != "Storage"),
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
