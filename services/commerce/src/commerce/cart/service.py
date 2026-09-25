"""Durable carts. Adding to a cart never reserves stock; checkout does that (Milestone 2)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from commerce.cart.models import MAX_LINE_QUANTITY, Cart, CartItem
from commerce.cart.schemas import CartLineOut, CartOut
from commerce.catalog.models import Product, Variant
from commerce.money import DEFAULT_CURRENCY, line_total


class CartError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def get_or_create_cart(db: Session, user_id: uuid.UUID) -> Cart:
    cart = db.scalar(select(Cart).where(Cart.user_id == user_id))
    if cart is not None:
        return cart
    cart = Cart(user_id=user_id)
    db.add(cart)
    try:
        db.flush()
    except IntegrityError:
        # Another request created it first.
        db.rollback()
        cart = db.scalar(select(Cart).where(Cart.user_id == user_id))
        assert cart is not None
    return cart


def _load_variant(db: Session, variant_id: uuid.UUID) -> Variant | None:
    return db.scalar(
        select(Variant)
        .options(
            selectinload(Variant.price),
            selectinload(Variant.balances),
            selectinload(Variant.product),
        )
        .where(Variant.id == variant_id)
    )


def _available(variant: Variant) -> int:
    return sum(max(b.available, 0) for b in variant.balances)


def set_item(db: Session, user_id: uuid.UUID, variant_id: uuid.UUID, quantity: int) -> None:
    """Set a line's quantity (0 removes it). Locks the cart row so concurrent edits serialize."""
    cart = get_or_create_cart(db, user_id)
    db.execute(select(Cart.id).where(Cart.id == cart.id).with_for_update())
    item = db.scalar(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.variant_id == variant_id)
    )

    if quantity == 0:
        if item is not None:
            db.delete(item)
            cart.version += 1
        db.commit()
        return

    variant = _load_variant(db, variant_id)
    if (
        variant is None
        or not variant.is_active
        or not variant.product.is_active
        or variant.price is None
    ):
        raise CartError(404, "That item is no longer available.")
    available = _available(variant)
    if available <= 0:
        raise CartError(409, "That item is out of stock.")
    if quantity > available:
        raise CartError(409, f"Only {available} left in stock.")

    if item is None:
        db.add(CartItem(cart_id=cart.id, variant_id=variant_id, quantity=quantity))
    else:
        item.quantity = quantity
    cart.version += 1
    db.commit()


def remove_item(db: Session, user_id: uuid.UUID, item_id: uuid.UUID) -> bool:
    """Remove a line by ID. Returns False when the line isn't in *this user's* cart."""
    item = db.scalar(
        select(CartItem)
        .join(Cart, Cart.id == CartItem.cart_id)
        .where(CartItem.id == item_id, Cart.user_id == user_id)
    )
    if item is None:
        return False
    cart = db.get(Cart, item.cart_id)
    assert cart is not None
    db.delete(item)
    cart.version += 1
    db.commit()
    return True


def cart_view(db: Session, user_id: uuid.UUID) -> CartOut:
    cart = get_or_create_cart(db, user_id)
    db.commit()
    items = db.scalars(
        select(CartItem)
        .options(
            selectinload(CartItem.variant).selectinload(Variant.price),
            selectinload(CartItem.variant).selectinload(Variant.balances),
            selectinload(CartItem.variant)
            .selectinload(Variant.product)
            .selectinload(Product.category),
        )
        .where(CartItem.cart_id == cart.id)
        .order_by(CartItem.added_at)
    ).all()

    lines: list[CartLineOut] = []
    warnings: list[str] = []
    subtotal = 0
    for item in items:
        v = item.variant
        available = _available(v)
        purchasable = v.is_active and v.product.is_active and v.price is not None
        price = v.price.amount_minor if v.price is not None else 0
        in_stock = purchasable and available >= item.quantity
        if not purchasable:
            warnings.append(f"{v.product.title} is no longer available.")
        elif available == 0:
            warnings.append(f"{v.product.title} is out of stock.")
        elif available < item.quantity:
            warnings.append(f"Only {available} of {v.product.title} left in stock.")
        total = line_total(price, item.quantity)
        if in_stock:
            subtotal += total
        lines.append(
            CartLineOut(
                id=item.id,
                variant_id=v.id,
                product_id=v.product_id,
                product_title=v.product.title,
                variant_name=v.name,
                sku=v.sku,
                image_path=v.product.image_path,
                quantity=item.quantity,
                unit_price_minor=price,
                line_total_minor=total,
                available=available,
                in_stock=in_stock,
                max_quantity=min(MAX_LINE_QUANTITY, max(available, 0)),
            )
        )
    return CartOut(
        id=cart.id,
        version=cart.version,
        currency=DEFAULT_CURRENCY,
        items=lines,
        item_count=sum(line.quantity for line in lines),
        subtotal_minor=subtotal,
        warnings=warnings,
    )
