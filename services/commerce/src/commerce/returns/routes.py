"""Return quotes, confirmation, and return status.

- ``POST /v1/returns/quote`` prices a return from saved order data (the assistant may call it
  for the customer).
- ``POST /v1/returns/quotes/{id}/confirmation`` and ``POST /v1/returns/confirm`` need the
  customer's own browser session: the assistant's service identity is refused, so no AI model
  can confirm a return or see a confirmation token.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import JSONResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from commerce.auth.deps import BrowserUser, CurrentUser
from commerce.config import Settings, get_settings
from commerce.db import get_db
from commerce.metrics import ownership_denials
from commerce.orders.models import Order
from commerce.returns import quotes
from commerce.returns.models import ReturnRequest
from commerce.returns.quote_schemas import (
    ConfirmationTokenOut,
    ConfirmReturnOut,
    ConfirmReturnRequest,
    DevAdvanceRequest,
    QuoteRejected,
    QuoteRequest,
    ReturnLabelOut,
    ReturnQuoteOut,
)
from commerce.returns.schemas import ReturnOut
from commerce.returns.service import order_returns

router = APIRouter(prefix="/v1/returns", tags=["returns"])
DbDep = Annotated[Session, Depends(get_db)]


def _fail(db: Session, exc: quotes.QuoteError) -> JSONResponse:
    db.rollback()
    if exc.status == 404:
        ownership_denials.add(1, {"resource": "return"})
    body = QuoteRejected(detail=exc.detail, problems=exc.problems)
    return JSONResponse(status_code=exc.status, content=body.model_dump(mode="json"))


def _return_out(db: Session, ret: ReturnRequest) -> ReturnOut:
    order = db.scalar(
        select(Order).options(selectinload(Order.lines)).where(Order.id == ret.order_id)
    )
    assert order is not None
    return next(r for r in order_returns(db, order) if r.id == ret.id)


@router.post(
    "/quote",
    response_model=ReturnQuoteOut,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": QuoteRejected}, 422: {"model": QuoteRejected}},
)
def create_quote(
    body: QuoteRequest, principal: CurrentUser, db: DbDep
) -> ReturnQuoteOut | JSONResponse:
    """Price a return from the order's saved amounts. Nothing is returned until the customer
    confirms this exact quote (valid 15 minutes)."""
    try:
        quote = quotes.create_quote(
            db, principal.id, body, created_via="assistant" if principal.via_assistant else "web"
        )
    except quotes.QuoteError as exc:
        return _fail(db, exc)
    db.commit()
    return quotes.quote_out(db, quote)


@router.get(
    "/quotes/{quote_id}", response_model=ReturnQuoteOut, responses={404: {"model": QuoteRejected}}
)
def get_quote(
    quote_id: uuid.UUID, principal: CurrentUser, db: DbDep
) -> ReturnQuoteOut | JSONResponse:
    try:
        return quotes.quote_out(db, quotes.own_quote(db, principal.id, quote_id))
    except quotes.QuoteError as exc:
        return _fail(db, exc)


@router.post(
    "/quotes/{quote_id}/confirmation",
    response_model=ConfirmationTokenOut,
    responses={
        403: {"description": "Not the customer's browser"},
        409: {"model": QuoteRejected},
        410: {"model": QuoteRejected},
    },
)
def mint_confirmation(
    quote_id: uuid.UUID, principal: BrowserUser, db: DbDep
) -> ConfirmationTokenOut | JSONResponse:
    """A single-use confirmation token for this quote, for the customer's own browser only."""
    try:
        token, expires_at = quotes.mint_token(db, principal.id, quote_id)
    except quotes.QuoteError as exc:
        return _fail(db, exc)
    db.commit()
    return ConfirmationTokenOut(confirmation_token=token, expires_at=expires_at)


@router.post(
    "/confirm",
    response_model=ConfirmReturnOut,
    responses={
        200: {"description": "Already confirmed: the same return"},
        403: {"model": QuoteRejected},
        409: {"model": QuoteRejected},
        410: {"model": QuoteRejected},
    },
    status_code=status.HTTP_201_CREATED,
)
def confirm_return(
    body: ConfirmReturnRequest,
    principal: BrowserUser,
    db: DbDep,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=120)],
) -> ConfirmReturnOut | JSONResponse:
    """Create the return for a quote. Repeats return the same return (200), never a second."""
    try:
        ret, refunded, created = quotes.confirm(
            db, principal.id, body.quote_id, body.confirmation_token, idempotency_key
        )
    except quotes.QuoteError as exc:
        return _fail(db, exc)
    db.commit()
    label = (
        ReturnLabelOut(
            carrier="Simulated carrier",
            tracking_number=ret.return_tracking_number,
            simulated=True,
            drop_off="Any carrier drop-off, or the return counter at any Serigan Mart store",
        )
        if ret.return_tracking_number
        else None
    )
    out = ConfirmReturnOut.model_validate(
        {
            "return": _return_out(db, ret),
            "label": label,
            "refunded_now_minor": refunded,
            "simulated": True,
        }
    )
    return JSONResponse(
        status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        content=out.model_dump(mode="json", by_alias=True),
    )


@router.get("", response_model=list[ReturnOut])
def list_returns(principal: CurrentUser, db: DbDep) -> list[ReturnOut]:
    """The customer's returns, newest first, with refund status."""
    orders = db.scalars(
        select(Order)
        .options(selectinload(Order.lines))
        .where(
            Order.id.in_(
                select(ReturnRequest.order_id).where(ReturnRequest.user_id == principal.id)
            )
        )
    )
    out = [r for order in orders for r in order_returns(db, order)]
    return sorted(out, key=lambda r: r.created_at, reverse=True)


@router.post(
    "/dev-reset",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"description": "Not a development environment"}},
)
def dev_reset(
    principal: BrowserUser, db: DbDep, settings: Annotated[Settings, Depends(get_settings)]
) -> Response:
    """Development only: undo the returns this customer made through quotes (not the seeded
    sample history), so browser tests and demos can start over."""
    if not settings.is_dev:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    quotes.reset_customer_returns(db, principal.id)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{return_id}/dev-advance",
    response_model=ReturnOut,
    responses={404: {"description": "Not found, or not a development environment"}},
)
def dev_advance(
    return_id: uuid.UUID,
    body: DevAdvanceRequest,
    principal: BrowserUser,
    db: DbDep,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ReturnOut | JSONResponse:
    """Development only: simulate the carrier scan, warehouse receipt, or inspection."""
    if not settings.is_dev:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    try:
        ret = quotes.advance(db, principal.id, return_id, body.event)
    except quotes.QuoteError as exc:
        return _fail(db, exc)
    db.commit()
    return _return_out(db, ret)
