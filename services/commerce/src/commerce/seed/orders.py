"""Order history for the development accounts, so order and return conversations have
something real to talk about. Development only (APP_ENV dev/test/ci).

Each order is a named scenario covering one branch of the sandbox return policy. Dates are
relative to when the seed runs, and every run resets these orders (same IDs, fresh dates),
so "delivered 3 days ago" stays true however long ago the database was created.

Amounts follow the order-line snapshot rules: unit price and discount as charged, and a
simulated Texas sales tax (8.25% on general merchandise; grocery food and gift cards are
exempt) standing in for what Stripe Tax will return once checkout exists. Shipping is $5.99
under $35 (after discounts, before tax) and free above. Orders created by real checkouts
(Milestone 2) never go through this file.

Each account ships to one made-up Dallas-Fort Worth address (real street names, invented
house numbers), flagged ``ship_to_is_sample`` so the storefront labels it as sample data.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from commerce.catalog.models import PolicyClass
from commerce.orders.models import OrderStatus
from commerce.seed.data import CATEGORIES, ProductSeed, VariantSeed

POLICY_VERSION = "sandbox-2026-09"
FREE_SHIPPING_MINOR = 3500  # orders under $35 (after discounts, before tax) pay shipping
SHIPPING_MINOR = 599
TAX_RATE_BPS = 825  # 8.25%, the Dallas combined rate
TAX_EXEMPT_CATEGORIES = frozenset(
    {"dairy-eggs", "produce", "meat-seafood", "bakery", "frozen", "pantry", "gift-cards"}
)
_NAMESPACE = uuid.UUID("5d0e4f1c-6a57-4c38-9d8e-2b0f7e3a91c4")


@dataclass(frozen=True)
class ShipTo:
    name: str
    line1: str
    city: str
    state: str
    postal_code: str
    line2: str | None = None
    country: str = "US"


# Sample delivery addresses for the development accounts (made up; labeled on screen).
DEV_SHIP_TO: dict[str, ShipTo] = {
    "alice@example.com": ShipTo(
        "Alice Rivera", "4127 Bluebonnet Ln", "Plano", "TX", "75023", line2="Apt 2B"
    ),
    "bob@example.com": ShipTo("Bob Chen", "918 W Magnolia Ave", "Fort Worth", "TX", "76104"),
}


@dataclass(frozen=True)
class LineSpec:
    slug: str
    variant_code: str
    quantity: int
    discount_minor: int = 0  # the whole line's discount, as charged


@dataclass(frozen=True)
class OrderSpec:
    key: str  # stable scenario name, e.g. "alice-headphones"
    email: str
    status: OrderStatus
    placed_days_ago: int
    delivered_days_ago: int | None
    lines: tuple[LineSpec, ...]
    scenario: str  # what this order is for, in one line


# Scenario keys that were renamed or removed. Reseeding deletes their orders, so an older dev
# database doesn't keep a stale copy (alice-toys became alice-small-order on 2026-09-26).
RETIRED_ORDER_KEYS: tuple[str, ...] = ("alice-toys",)

DEV_ORDERS: tuple[OrderSpec, ...] = (
    OrderSpec(
        "alice-headphones", "alice@example.com", OrderStatus.DELIVERED, 6, 3,
        (LineSpec("sonora-arc-wireless-headphones", "MID", 1),
         LineSpec("sonora-pulse-wireless-earbuds", "GRA", 1)),
        "Electronics delivered 3 days ago: returnable, refunded after inspection. Two "
        "wireless audio items, so 'the headphones' is ambiguous.",
    ),
    OrderSpec(
        "alice-groceries-recent", "alice@example.com", OrderStatus.DELIVERED, 3, 2,
        (LineSpec("cedar-hollow-farms-organic-fat-free-skim-milk", "GAL", 1),
         LineSpec("kalos-greek-yogurt-co-zero-sugar-greek-yogurt-vanilla", "4PK", 2),
         LineSpec("hollis-hen-farm-pasture-raised-large-brown-eggs", "12CT", 1)),
        "Perishables delivered 2 days ago: a spoiled or damaged item can be refunded "
        "without sending it back (within 7 days).",
    ),
    OrderSpec(
        "alice-groceries-old", "alice@example.com", OrderStatus.DELIVERED, 13, 12,
        (LineSpec("fernbrook-dairy-whole-milk", "GAL", 1),
         LineSpec("fernbrook-dairy-sharp-cheddar-cheese-block", "8OZ", 2)),
        "Perishables delivered 12 days ago: past the 7-day window for perishables.",
    ),
    OrderSpec(
        "alice-apparel", "alice@example.com", OrderStatus.DELIVERED, 21, 18,
        (LineSpec("driftwood-organic-tee", "M", 3, discount_minor=1000),
         LineSpec("driftwood-wool-socks-3pk", "M", 1)),
        "Three tees with a $10.00 line discount: a partial return refunds per unit with "
        "cents split 333/333/334.",
    ),
    OrderSpec(
        "alice-kettle-old", "alice@example.com", OrderStatus.DELIVERED, 48, 45,
        (LineSpec("kettleworth-gooseneck-kettle", "MAT", 1),),
        "Delivered 45 days ago: outside the 30-day return window.",
    ),
    OrderSpec(
        "alice-gift-card", "alice@example.com", OrderStatus.DELIVERED, 6, 6,
        (LineSpec("serigan-mart-gift-card", "50", 1),),
        "Gift card: final sale, never returnable.",
    ),
    OrderSpec(
        "alice-in-transit", "alice@example.com", OrderStatus.FULFILLING, 1, None,
        (LineSpec("tempo-yoga-mat", "SEA", 1), LineSpec("tempo-resistance-bands", "STD", 1)),
        "Not delivered yet: it can be tracked but not returned.",
    ),
    OrderSpec(
        "alice-pens", "alice@example.com", OrderStatus.DELIVERED, 10, 8,
        (LineSpec("quillmark-gel-pens-12pk", "STD", 1),),
        "One item under $25 that needs no inspection: instant refund at the carrier scan.",
    ),
    OrderSpec(
        "alice-small-order", "alice@example.com", OrderStatus.DELIVERED, 12, 10,
        (LineSpec("pebble-pine-plush-otter", "STD", 1), LineSpec("quillmark-dotted-notebook", "FOR", 1)),
        "Under $35, so it paid $5.99 shipping: returning the whole order refunds the shipping "
        "too; returning one item doesn't.",
    ),
    # Return history (the return and refund rows are seeded by the returns milestone):
    OrderSpec(
        "alice-partly-returned", "alice@example.com", OrderStatus.DELIVERED, 18, 15,
        (LineSpec("quillmark-laptop-backpack", "CHA", 2),),
        "Two backpacks; one was already returned and refunded ($75.76). Only the other can "
        "come back, and it takes the leftover tax cent ($75.77).",
    ),
    OrderSpec(
        "alice-return-in-progress", "alice@example.com", OrderStatus.DELIVERED, 12, 9,
        (LineSpec("harbor-home-throw-blanket", "CRE", 1),),
        "Its return is in transit and the refund isn't requested yet: 'where's my refund?' "
        "has a real answer, and there's nothing left to return.",
    ),
    OrderSpec(
        "bob-tablet", "bob@example.com", OrderStatus.DELIVERED, 32, 29,
        (LineSpec("lumen-tablet-10", "64", 1),),
        "Bob's tablet, delivered 29 days ago: the last day of the return window.",
    ),
    OrderSpec(
        "bob-headphones", "bob@example.com", OrderStatus.DELIVERED, 7, 4,
        (LineSpec("sonora-studio-wired-headphones", "STD", 1),),
        "Bob's order: Alice must never see or return it.",
    ),
    OrderSpec(
        "bob-canceled", "bob@example.com", OrderStatus.CANCELED, 5, None,
        (LineSpec("kettleworth-french-press", "STD", 1),),
        "Canceled before shipping: nothing to return.",
    ),
)  # fmt: skip


def order_id(key: str) -> uuid.UUID:
    return uuid.uuid5(_NAMESPACE, f"order:{key}")


def line_id(key: str, index: int) -> uuid.UUID:
    return uuid.uuid5(_NAMESPACE, f"order:{key}:line:{index}")


def tax_on(taxable_minor: int, category: str) -> int:
    if category in TAX_EXEMPT_CATEGORIES:
        return 0
    return (taxable_minor * TAX_RATE_BPS + 5000) // 10000  # round half up to the cent


@dataclass(frozen=True)
class BuiltLine:
    id: uuid.UUID
    product: ProductSeed
    variant: VariantSeed
    policy_class: PolicyClass
    quantity: int
    unit_price_minor: int
    discount_minor: int
    tax_minor: int

    @property
    def total_minor(self) -> int:
        return self.unit_price_minor * self.quantity - self.discount_minor + self.tax_minor


@dataclass(frozen=True)
class BuiltOrder:
    spec: OrderSpec
    id: uuid.UUID
    placed_at: datetime
    delivered_at: datetime | None
    lines: tuple[BuiltLine, ...]

    @property
    def subtotal_minor(self) -> int:
        return sum(ln.unit_price_minor * ln.quantity for ln in self.lines)

    @property
    def discount_minor(self) -> int:
        return sum(ln.discount_minor for ln in self.lines)

    @property
    def tax_minor(self) -> int:
        return sum(ln.tax_minor for ln in self.lines)

    @property
    def shipping_minor(self) -> int:
        return (
            SHIPPING_MINOR if self.subtotal_minor - self.discount_minor < FREE_SHIPPING_MINOR else 0
        )

    @property
    def total_minor(self) -> int:
        return sum(ln.total_minor for ln in self.lines) + self.shipping_minor


def build_order(spec: OrderSpec, products: dict[str, ProductSeed], now: datetime) -> BuiltOrder:
    """Resolve a scenario against the seed catalog and compute its amounts."""
    policy = {c.slug: c.policy_class for c in CATEGORIES}
    lines = []
    for i, ls in enumerate(spec.lines):
        product = products[ls.slug]
        variant = next(v for v in product.variants if v.code == ls.variant_code)
        unit = variant.price_cents or product.price_cents
        taxable = unit * ls.quantity - ls.discount_minor
        lines.append(
            BuiltLine(
                id=line_id(spec.key, i),
                product=product,
                variant=variant,
                policy_class=policy[product.category],
                quantity=ls.quantity,
                unit_price_minor=unit,
                discount_minor=ls.discount_minor,
                tax_minor=tax_on(taxable, product.category),
            )
        )
    return BuiltOrder(
        spec=spec,
        id=order_id(spec.key),
        placed_at=now - timedelta(days=spec.placed_days_ago),
        delivered_at=(
            now - timedelta(days=spec.delivered_days_ago)
            if spec.delivered_days_ago is not None
            else None
        ),
        lines=tuple(lines),
    )
