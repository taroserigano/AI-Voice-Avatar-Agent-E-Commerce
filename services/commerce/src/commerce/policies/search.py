"""Search over approved policy sections: OpenSearch keywords, plus Pinecone meaning when set up.

Same design as product search. The policy files are the source; both indexes are rebuildable
projections. The OpenSearch index loads itself on first use and reloads when the files change
(a content hash is stored in the index), so no manual reindex is needed after editing a policy.
Pinecone, when configured, is filled by ``pnpm reindex`` into namespace ``policies-<env>``.
"""

from __future__ import annotations

import hashlib
import logging
import threading
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Literal

from opensearchpy import OpenSearch, helpers
from opensearchpy.exceptions import NotFoundError

from commerce.config import get_settings
from commerce.policies.documents import PolicyDocument, PolicySection, load_policies
from commerce.search.keyword import INDEX_BODY as PRODUCT_INDEX_BODY
from commerce.search.rrf import reciprocal_rank_fusion
from commerce.search.semantic import TEXT_FIELD, UPSERT_BATCH, get_semantic_index

log = logging.getLogger(__name__)

_EN = {"type": "text", "analyzer": "shop", "search_analyzer": "shop_search"}
META_ID = "__meta__"

INDEX_BODY: dict[str, Any] = {
    # Same English analysis and shop synonyms as the product index.
    "settings": PRODUCT_INDEX_BODY["settings"],
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "doc_id": {"type": "keyword"},
            "doc_title": _EN,
            "section_id": {"type": "keyword"},
            "title": _EN,
            "parent_title": _EN,
            "body": _EN,
            "content_hash": {"type": "keyword"},
        },
    },
}

SemanticState = Literal["used", "unavailable", "disabled"]


@dataclass(frozen=True)
class PolicyHit:
    doc: PolicyDocument
    section: PolicySection

    @property
    def key(self) -> str:
        return section_key(self.doc.id, self.section.section_id)


@dataclass(frozen=True)
class PolicySearchResult:
    hits: list[PolicyHit]
    semantic: SemanticState


def section_key(doc_id: str, section_id: str) -> str:
    return f"{doc_id}#{section_id}" if section_id else doc_id


def _sections() -> dict[str, tuple[PolicyDocument, PolicySection]]:
    return {
        section_key(d.id, s.section_id): (d, s)
        for d in load_policies().values()
        for s in d.sections
        if s.body  # a heading with only subsections has nothing to cite by itself
    }


def content_hash() -> str:
    h = hashlib.sha256()
    for key, (doc, section) in sorted(_sections().items()):
        h.update(f"{key}\n{doc.version}\n{section.title}\n{section.body}\n".encode())
    return h.hexdigest()[:16]


def _semantic_text(doc: PolicyDocument, section: PolicySection) -> str:
    heading = " / ".join(t for t in (doc.title, section.parent_title, section.title) if t)
    return f"{heading}\n\n{section.body}"


class PolicyKeywordIndex:
    def __init__(self, client: OpenSearch, index: str) -> None:
        self.client = client
        self.index = index
        self._checked: str | None = None
        self._lock = threading.Lock()

    def _stored_hash(self) -> str | None:
        try:
            doc = self.client.get(index=self.index, id=META_ID)
        except NotFoundError:
            return None
        return str(doc["_source"].get("content_hash"))

    def rebuild(self) -> int:
        current = content_hash()
        self.client.indices.delete(index=self.index, ignore_unavailable=True)
        self.client.indices.create(index=self.index, body=INDEX_BODY)
        actions: list[dict[str, Any]] = [
            {
                "_op_type": "index",
                "_index": self.index,
                "_id": key,
                "_source": {
                    "doc_id": doc.id,
                    "doc_title": doc.title,
                    "section_id": section.section_id,
                    "title": section.title,
                    "parent_title": section.parent_title or "",
                    "body": section.body,
                },
            }
            for key, (doc, section) in _sections().items()
        ]
        actions.append(
            {
                "_op_type": "index",
                "_index": self.index,
                "_id": META_ID,
                "_source": {"content_hash": current},
            }
        )
        ok, _ = helpers.bulk(self.client, actions, refresh="wait_for")
        self._checked = current
        return int(ok) - 1

    def ensure_current(self) -> None:
        current = content_hash()
        if self._checked == current:
            return
        with self._lock:
            if self._checked == current:
                return
            if self._stored_hash() != current:
                log.info("policy index %s is missing or stale; rebuilding", self.index)
                self.rebuild()
            self._checked = current

    def search(self, query: str, top_k: int) -> list[str]:
        self.ensure_current()
        body = {
            "size": top_k,
            "_source": False,
            "query": {
                "bool": {
                    "must_not": [{"ids": {"values": [META_ID]}}],
                    "should": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["title^3", "parent_title^2", "body", "doc_title"],
                                "type": "best_fields",
                                "fuzziness": "AUTO",
                                "minimum_should_match": "2<60%",
                                "boost": 2,
                            }
                        },
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["title^2", "parent_title", "body"],
                                "type": "cross_fields",
                                "operator": "or",
                            }
                        },
                    ],
                    "minimum_should_match": 1,
                }
            },
        }
        resp = self.client.search(index=self.index, body=body)
        return [hit["_id"] for hit in resp["hits"]["hits"]]


@lru_cache
def get_policy_keyword_index() -> PolicyKeywordIndex:
    settings = get_settings()
    client = OpenSearch(hosts=[settings.opensearch_url], timeout=2, max_retries=1)
    return PolicyKeywordIndex(client, settings.policies_index)


# --- Pinecone ---------------------------------------------------------------------------------


def _pinecone_policy_index() -> Any | None:
    """This app's Pinecone index client (shared with products; a different namespace).

    Uses the product index's cached setup, so a misconfigured Pinecone is checked at most once
    a minute instead of on every search. Raises when Pinecone is configured but unusable.
    """
    semantic = get_semantic_index()
    return None if semantic is None else semantic.index


def upsert_policies_to_pinecone() -> int | None:
    """Replace this environment's policy namespace. None when Pinecone isn't configured."""
    index = _pinecone_policy_index()
    if index is None:
        return None
    namespace = get_settings().policies_namespace
    try:
        index.delete(delete_all=True, namespace=namespace)
    except Exception as exc:  # noqa: BLE001 - a namespace that doesn't exist yet is fine
        log.info("pinecone policy clear skipped: %s", type(exc).__name__)
    records = [
        {"_id": key, TEXT_FIELD: _semantic_text(doc, section), "doc_id": doc.id}
        for key, (doc, section) in _sections().items()
    ]
    for start in range(0, len(records), UPSERT_BATCH):
        index.upsert_records(records=records[start : start + UPSERT_BATCH], namespace=namespace)
    return len(records)


_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="policy-semantic")


def _semantic_ids(query: str, top_k: int) -> tuple[list[str], SemanticState]:
    settings = get_settings()
    if not settings.pinecone_api_key:
        return [], "disabled"
    try:
        index = _pinecone_policy_index()
        if index is None:
            return [], "disabled"
        future = _pool.submit(
            index.search,
            namespace=settings.policies_namespace,
            top_k=top_k,
            inputs={"text": query},
            fields=["doc_id"],
        )
        resp = future.result(timeout=settings.semantic_timeout_ms / 1000 * 2)
    except (FutureTimeout, Exception) as exc:  # noqa: BLE001 - keyword results still answer
        log.warning("policy semantic search unavailable: %s", type(exc).__name__)
        return [], "unavailable"
    return [hit.id for hit in resp.result.hits], "used"


def search_policies(query: str, top_k: int = 5) -> PolicySearchResult:
    sections = _sections()
    keyword_ids = get_policy_keyword_index().search(query, top_k=top_k * 3)
    semantic_ids, state = _semantic_ids(query, top_k * 3)
    lists: Sequence[Sequence[str]] = [keyword_ids, semantic_ids] if semantic_ids else [keyword_ids]
    merged = reciprocal_rank_fusion(lists) if semantic_ids else keyword_ids
    hits = [PolicyHit(*sections[key]) for key in merged if key in sections][:top_k]
    return PolicySearchResult(hits=hits, semantic=state)
