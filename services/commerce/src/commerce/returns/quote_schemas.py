"""Request and response shapes for return quotes and confirmation."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import Field

from commerce.api_model import ApiModel
from commerce.returns.policy import RefundTiming
from commerce.returns.schemas import PaymentMethodOut, ReturnOut

ReturnReason = Literal[
    "damaged",
    "defective",
    "wrong_item",
    "not_as_described",
    "spoiled_or_expired",
    "missing_parts",
    "no_longer_needed",
    "better_price",
    "arrived_late",
    "other",
]

# Fresh and frozen food is refunded only for a problem with the food itself (policy §2.2).
PERISHABLE_REASONS: frozenset[str] = frozenset(
    {"damaged", "spoiled_or_expired", "wrong_item", "defective", "missing_parts"}
)


class QuoteLineIn(ApiModel):
    order_line_id: uuid.UUID
    quantity: int = Field(ge=1, le=100)


class QuoteRequest(ApiModel):
    order_id: uuid.UUID
    lines: list[QuoteLineIn] = Field(min_length=1, max_length=50)
    reason: ReturnReason
    note: str | None = Field(default=None, max_length=500)


class QuoteLineOut(ApiModel):
    order_line_id: uuid.UUID
    product_title: str
    variant_name: str
    image_path: str
    policy_class: str
    quantity: int
    refund_minor: int
    refund_timing: RefundTiming
    timing_message: str


class ReturnQuoteOut(ApiModel):
    id: uuid.UUID
    order_id: uuid.UUID
    status: Literal["open", "expired", "confirmed"]
    lines: list[QuoteLineOut]
    reason: str
    items_refund_minor: int
    shipping_refund_minor: int
    total_refund_minor: int
    currency: str
    refund_destination: PaymentMethodOut | None
    policy_version: str
    needs_shipping: bool = Field(description="False when nothing has to be sent back (perishables)")
    expires_at: datetime
    return_id: uuid.UUID | None


class LineProblem(ApiModel):
    order_line_id: uuid.UUID
    reason: str
    message: str


class QuoteRejected(ApiModel):
    detail: str
    problems: list[LineProblem]


class ConfirmationTokenOut(ApiModel):
    confirmation_token: str = Field(description="Single use; valid until the quote expires")
    expires_at: datetime


class ConfirmReturnRequest(ApiModel):
    quote_id: uuid.UUID
    confirmation_token: str = Field(min_length=20, max_length=200)


class ReturnLabelOut(ApiModel):
    carrier: str
    tracking_number: str
    simulated: bool
    drop_off: str


class ConfirmReturnOut(ApiModel):
    return_: ReturnOut = Field(alias="return", serialization_alias="return")
    label: ReturnLabelOut | None
    refunded_now_minor: int = Field(description="Refunded at confirmation (perishables)")
    simulated: bool = Field(description="Refunds are simulated until Stripe is connected")


class DevAdvanceRequest(ApiModel):
    event: Literal["carrier_scan", "warehouse_receive", "inspect_pass", "inspect_fail"]
