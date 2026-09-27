"""Approved policy documents and section search, for the assistant's citations.

The public ``/returns-policy`` page reads the same files directly; these routes are behind
sign-in like every other API route.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, status

from commerce.api_model import ApiModel
from commerce.policies.documents import PolicyDocument, PolicySection, load_policies
from commerce.policies.search import search_policies, section_key

router = APIRouter(prefix="/v1/policies", tags=["policies"])

PAGE_PATHS = {
    "returns-and-refunds": "/returns-policy",
    "returns-regulations": "/returns-policy",
}


class PolicySectionOut(ApiModel):
    doc_id: str
    doc_title: str
    version: str
    effective_date: date
    section_id: str
    number: str
    title: str
    parent_title: str | None
    body: str
    cite: str  # "returns-and-refunds#rr-7-3": what the assistant cites
    url: str | None  # where a customer can read it, with the section anchor


class PolicySearchOut(ApiModel):
    query: str
    semantic: Literal["used", "unavailable", "disabled"]
    results: list[PolicySectionOut]


class PolicyDocumentOut(ApiModel):
    id: str
    title: str
    version: str
    effective_date: date
    status: str
    summary: list[str]
    url: str | None
    sections: list[PolicySectionOut]


def _section_out(doc: PolicyDocument, s: PolicySection) -> PolicySectionOut:
    page = PAGE_PATHS.get(doc.id)
    return PolicySectionOut(
        doc_id=doc.id,
        doc_title=doc.title,
        version=doc.version,
        effective_date=doc.effective_date,
        section_id=s.section_id,
        number=s.number,
        title=s.title,
        parent_title=s.parent_title,
        body=s.body,
        cite=section_key(doc.id, s.section_id),
        url=(f"{page}#{s.section_id}" if s.section_id else page) if page else None,
    )


@router.get("/search", response_model=PolicySearchOut)
def search(
    q: Annotated[str, Query(min_length=2, max_length=300)],
    limit: Annotated[int, Query(ge=1, le=10)] = 5,
) -> PolicySearchOut:
    result = search_policies(q, top_k=limit)
    return PolicySearchOut(
        query=q,
        semantic=result.semantic,
        results=[_section_out(h.doc, h.section) for h in result.hits],
    )


@router.get(
    "/{doc_id}", response_model=PolicyDocumentOut, responses={404: {"description": "Not found"}}
)
def get_document(doc_id: str) -> PolicyDocumentOut:
    doc = load_policies().get(doc_id)
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Policy not found")
    return PolicyDocumentOut(
        id=doc.id,
        title=doc.title,
        version=doc.version,
        effective_date=doc.effective_date,
        status=doc.status,
        summary=list(doc.summary),
        url=PAGE_PATHS.get(doc.id),
        sections=[_section_out(doc, s) for s in doc.sections],
    )
