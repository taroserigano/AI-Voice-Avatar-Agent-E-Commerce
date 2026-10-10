"""What the assistant API sends: conversations, messages, and the cards shown beside answers.

Cards come from tool results (never from the model's text), so a price or order status on a card
is always what the commerce API returned. The web types in ``apps/web/lib/assistant-types.ts``
mirror these.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

AgentName = Literal["steph", "xana"]


class Tag(BaseModel):
    value: str
    label: str


class ProductCard(BaseModel):
    kind: Literal["product"] = "product"
    id: str
    title: str
    brand: str
    product_type: str
    price_minor: int
    currency: str = "USD"
    image_path: str
    in_stock: bool
    tags: list[Tag] = Field(default_factory=list)
    url: str
    # The variant "add to cart" adds: the only one, or the first in stock.
    variant_id: str | None = None
    variant_name: str | None = None
    facts: list[str] = Field(default_factory=list)  # e.g. "0 g added sugar", "Milkfat: 0%"
    # Customer reviews: average stars (one decimal), null with none; how many reviews.
    rating_average: float | None = None
    rating_count: int = 0


class OrderLineBrief(BaseModel):
    id: str
    title: str
    variant_name: str
    quantity: int
    image_path: str


class OrderCard(BaseModel):
    kind: Literal["order"] = "order"
    id: str
    number: str  # the short reference shown to customers
    status: str
    placed_at: datetime
    delivered_at: datetime | None = None
    total_minor: int
    currency: str = "USD"
    item_count: int
    lines: list[OrderLineBrief] = Field(default_factory=list)
    url: str


class StoreCard(BaseModel):
    kind: Literal["store"] = "store"
    code: str
    name: str
    address: str
    phone: str
    open_now: bool
    today_hours: str  # "7:00 AM – 10:00 PM" or "Closed today"
    services: list[str] = Field(default_factory=list)
    directions_url: str


class CitationCard(BaseModel):
    kind: Literal["citation"] = "citation"
    cite: str  # "returns-and-refunds#rr-7-3"
    doc_title: str
    number: str
    title: str
    version: str
    url: str | None
    excerpt: str


class CartCard(BaseModel):
    kind: Literal["cart"] = "cart"
    added_title: str
    added_variant: str
    quantity: int
    item_count: int
    subtotal_minor: int
    currency: str = "USD"


class HandoffCard(BaseModel):
    kind: Literal["handoff"] = "handoff"
    reason: str
    message: str


class ReturnOptionsCard(BaseModel):
    """What each item in an order can return right now (from the store's return options)."""

    model_config = ConfigDict(extra="allow")
    kind: Literal["return_options"] = "return_options"
    order_id: str
    lines: list[dict[str, Any]]


class ReturnStatusCard(BaseModel):
    """A return's outcome or status: confirmed, declined, expired, or an existing return."""

    model_config = ConfigDict(extra="allow")
    kind: Literal["return_status"] = "return_status"
    outcome: str


class ReturnQuoteCard(BaseModel):
    """A priced return waiting for the customer's own confirmation (see return_tools.quote_card)."""

    model_config = ConfigDict(extra="allow")
    kind: Literal["return_quote"] = "return_quote"
    quote_id: str


class SearchCard(BaseModel):
    """What a product search looked for (as chips), and a link to all results on the site."""

    kind: Literal["search"] = "search"
    total: int
    shown: int
    chips: list[str]
    url: str


class XanaCard(BaseModel):
    """A pointer to Xena, the support assistant, for returns and refunds."""

    kind: Literal["xana"] = "xana"
    about: str
    message: str
    url: str


Card = Annotated[
    SearchCard
    | XanaCard
    | ProductCard
    | OrderCard
    | StoreCard
    | CitationCard
    | CartCard
    | HandoffCard
    | ReturnOptionsCard
    | ReturnStatusCard
    | ReturnQuoteCard,
    Field(discriminator="kind"),
]


class ConversationOut(BaseModel):
    id: uuid.UUID
    agent: AgentName
    title: str
    created_at: datetime
    updated_at: datetime


class MessageOut(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    text: str
    cards: list[Card] = Field(default_factory=list)
    citations: list[CitationCard] = Field(default_factory=list)


class ConversationDetail(ConversationOut):
    messages: list[MessageOut]
    # A return quote waiting for the customer's confirmation (the conversation is paused on it).
    pending_quote: dict[str, Any] | None = None


class CreateConversation(BaseModel):
    agent: AgentName = "steph"


class SendMessage(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    voice: bool = False  # spoken by the customer: answer briefly


class ResumeTurn(BaseModel):
    """What the browser saw happen to the quote. The assistant checks it with the store."""

    quote_id: uuid.UUID
    outcome: Literal["confirmed", "declined"]
    voice: bool = False


class VoiceConfig(BaseModel):
    stt: Literal["deepgram", "groq", "browser"]
    tts: Literal["cartesia", "browser"]
    max_seconds: int
    decision_model: str
    notice: str


class TranscriptOut(BaseModel):
    text: str
    provider: str
    latency_ms: float


class SpeakIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    agent: AgentName = "xana"


class ConfirmCheckIn(BaseModel):
    """A spoken answer to a return read-back, and what the browser observed around it."""

    text: str = Field(max_length=500)
    final: bool
    readback_complete: bool
    speech_ms: int = Field(ge=0, le=60_000)
    conversation_id: uuid.UUID
    quote_id: uuid.UUID


class ConfirmCheckOut(BaseModel):
    decision: Literal["yes", "no", "unclear"]
    reason: str
    say: str  # what the app says next


class AssistantStatus(BaseModel):
    model: str  # "claude-sonnet-5", or "scripted"
    simulated: bool
    reason: str | None = None  # why the scripted model is in use
    prompt_versions: dict[str, str]
    decision_model: str  # "jev-latest", "jev-simulator", or "off"
    debug: bool  # development: the chat shows why each answer took its route
