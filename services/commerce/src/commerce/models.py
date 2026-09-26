"""Import every model so SQLAlchemy metadata (and Alembic autogenerate) sees all tables."""

from commerce.auth.models import AuthSession, Role, User
from commerce.cart.models import Cart, CartItem
from commerce.catalog.models import (
    Category,
    InventoryBalance,
    PolicyClass,
    Price,
    Product,
    StockLocation,
    Variant,
)
from commerce.db import Base
from commerce.orders.models import Order, OrderLine, OrderStatus
from commerce.outbox.models import OutboxEvent
from commerce.stores.models import Store

__all__ = [
    "AuthSession",
    "Base",
    "Cart",
    "CartItem",
    "Category",
    "InventoryBalance",
    "Order",
    "OrderLine",
    "OrderStatus",
    "OutboxEvent",
    "PolicyClass",
    "Price",
    "Product",
    "Role",
    "StockLocation",
    "Store",
    "User",
    "Variant",
]
