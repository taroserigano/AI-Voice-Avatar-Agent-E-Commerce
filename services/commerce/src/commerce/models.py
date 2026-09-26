"""Import every model so SQLAlchemy metadata (and Alembic autogenerate) sees all tables."""

from commerce.activity.models import CustomerEvent
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
from commerce.payments.models import PaymentAttempt
from commerce.returns.models import PolicyVersion, RefundAttempt, ReturnItem, ReturnRequest
from commerce.reviews.models import Review
from commerce.shipping.models import Shipment, ShipmentEvent
from commerce.support.models import SupportCase

__all__ = [
    "AuthSession",
    "Base",
    "Cart",
    "CartItem",
    "Category",
    "CustomerEvent",
    "InventoryBalance",
    "Order",
    "OrderLine",
    "OrderStatus",
    "OutboxEvent",
    "PaymentAttempt",
    "PolicyClass",
    "PolicyVersion",
    "Price",
    "Product",
    "RefundAttempt",
    "ReturnItem",
    "ReturnRequest",
    "Review",
    "Role",
    "Shipment",
    "ShipmentEvent",
    "StockLocation",
    "SupportCase",
    "User",
    "Variant",
]
