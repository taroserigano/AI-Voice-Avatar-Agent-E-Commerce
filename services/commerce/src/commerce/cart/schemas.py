from __future__ import annotations

import uuid

from pydantic import Field

from commerce.api_model import ApiModel
from commerce.cart.models import MAX_LINE_QUANTITY


class SetCartItemRequest(ApiModel):
    variant_id: uuid.UUID
    quantity: int = Field(ge=0, le=MAX_LINE_QUANTITY, description="0 removes the line")


class CartLineOut(ApiModel):
    id: uuid.UUID
    variant_id: uuid.UUID
    product_id: uuid.UUID
    product_title: str
    variant_name: str
    sku: str
    image_path: str
    quantity: int
    unit_price_minor: int = Field(description="Current price from PostgreSQL")
    line_total_minor: int
    available: int
    in_stock: bool
    max_quantity: int


class CartOut(ApiModel):
    id: uuid.UUID
    version: int
    currency: str
    items: list[CartLineOut]
    item_count: int
    subtotal_minor: int = Field(
        description="Estimate at current prices. Checkout recalculates on the server; "
        "tax is calculated at payment."
    )
    warnings: list[str] = Field(default_factory=list)
    shipping_minor: int = Field(
        default=0, description="Standard shipping for this subtotal: $5.99, free at the threshold"
    )
    free_shipping_threshold_minor: int = 0
    free_shipping_remaining_minor: int = Field(
        default=0, description="How much more for free shipping; 0 when it already applies"
    )
    estimated_total_minor: int = Field(
        default=0, description="Subtotal plus shipping, before tax (tax is calculated at payment)"
    )
