from __future__ import annotations

import re
import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import Field, field_validator

from commerce.api_model import ApiModel

# Control characters other than tab and newline never belong in review text.
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")

TITLE_MAX = 120
BODY_MAX = 2000


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = _CONTROL.sub("", value).strip()
    return value or None


class ReviewIn(ApiModel):
    """What a shopper submits. The author and product come from the session and the URL."""

    rating: int = Field(ge=1, le=5, description="Whole stars, 1 to 5")
    title: str | None = Field(default=None, max_length=TITLE_MAX)
    body: str | None = Field(default=None, max_length=BODY_MAX)

    @field_validator("title", "body", mode="after")
    @classmethod
    def _strip(cls, value: str | None) -> str | None:
        return _clean(value)


class ReviewOut(ApiModel):
    id: uuid.UUID
    rating: int
    title: str | None
    body: str | None
    author_name: str = Field(description='Shortened display name, e.g. "Alice R."')
    created_at: datetime
    updated_at: datetime
    is_mine: bool
    verified_purchase: bool = Field(description="The author has a paid order for this product")
    is_sample: bool = Field(description="Seeded demo content; label it as a sample on screen")


class RatingBucket(ApiModel):
    stars: int
    count: int


class RatingSummary(ApiModel):
    average: float | None = Field(description="Mean rating to one decimal; null with no reviews")
    count: int
    distribution: list[RatingBucket] = Field(description="One bucket per star value, 5 down to 1")


class ReviewSort(StrEnum):
    NEWEST = "newest"
    HIGHEST = "highest"
    LOWEST = "lowest"


class ReviewPage(ApiModel):
    summary: RatingSummary
    items: list[ReviewOut]
    total: int
    page: int
    page_size: int
    my_review: ReviewOut | None = Field(description="The signed-in shopper's review, if any")
