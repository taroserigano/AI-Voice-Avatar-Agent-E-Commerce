from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import Field

from commerce.api_model import ApiModel
from commerce.payments.models import PaymentProvider, PaymentStatus
from commerce.returns.models import RefundStatus, ReturnStatus
from commerce.returns.policy import Reason, RefundTiming
from commerce.shipping.models import ShipmentStatus


class PaymentMethodOut(ApiModel):
    """Where refunds go: always the order's original payment method."""

    provider: PaymentProvider
    card_brand: str | None
    card_last4: str | None
    is_simulated: bool = Field(description="Seed/simulator payment, not a real Stripe charge")


class PaymentOut(PaymentMethodOut):
    status: PaymentStatus
    amount_minor: int
    refunded_minor: int
    currency: str
    captured_at: datetime | None


class ShipmentEventOut(ApiModel):
    occurred_at: datetime
    status: ShipmentStatus
    description: str
    location: str | None


class ShipmentOut(ApiModel):
    id: uuid.UUID
    carrier: str
    service: str
    tracking_number: str
    status: ShipmentStatus
    shipped_at: datetime | None
    estimated_delivery_at: datetime | None
    delivered_at: datetime | None
    is_simulated: bool
    events: list[ShipmentEventOut]


class RefundOut(ApiModel):
    status: RefundStatus
    amount_minor: int
    currency: str
    requested_at: datetime
    settled_at: datetime | None
    failure_reason: str | None


class ReturnItemOut(ApiModel):
    order_line_id: uuid.UUID
    product_title: str
    variant_name: str
    image_path: str
    quantity: int
    refund_minor: int
    condition: str


class ReturnOut(ApiModel):
    id: uuid.UUID
    order_id: uuid.UUID
    rma_number: str
    status: ReturnStatus
    reason: str
    created_at: datetime
    closed_at: datetime | None
    shipping_refund_minor: int
    items: list[ReturnItemOut]
    refund: RefundOut | None = Field(description="The latest refund attempt, if any")
    is_sample: bool = Field(description="Seeded demo history; label it on screen")


class LineReturnOption(ApiModel):
    order_line_id: uuid.UUID
    product_title: str
    variant_name: str
    image_path: str
    quantity: int
    returned_quantity: int = Field(description="Units already in returns that weren't rejected")
    returnable_quantity: int
    eligible: bool
    reason: Reason
    message: str = Field(description="Plain-language explanation, written by the server")
    window_ends_at: datetime | None
    inspection_required: bool
    refund_timing: RefundTiming | None
    max_refund_minor: int = Field(
        description="Refund if every returnable unit is sent back now; computed by the server"
    )
    currency: str


class ReturnOptions(ApiModel):
    order_id: uuid.UUID
    policy_version: str
    refund_destination: PaymentMethodOut | None
    lines: list[LineReturnOption]
    whole_order_shipping_refund_minor: int = Field(
        description="Shipping refunded only if everything left in the order is returned"
    )
    as_of: datetime
