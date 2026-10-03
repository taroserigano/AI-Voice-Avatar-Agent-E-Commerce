"""Search over approved policy sections: OpenSearch keywords, plus meaning search when set up.

Same design as product search. The policy files are the source; both indexes are rebuildable
projections. The OpenSearch index loads itself on first use and reloads when the files change
(a content hash is stored in the index), so no manual reindex is needed after editing a policy.
Meaning search is Qdrant (decision 23) through ``ai_commerce_retrieval`` (LlamaIndex nodes,
OpenAI embeddings) in collection ``aic-policies-<env>``. It syncs itself incrementally (by content
hash) the first time a process searches, and ``pnpm reindex`` syncs it too. Customers ask in their
own words ("can I send back opened headphones?") while the policy says "Opened items are fine",
which keywords alone miss; the two result lists are fused by rank (RRF). If Qdrant or the
embedding call is slow or down, keywords answer alone within ``policy_semantic_timeout_ms``.
Pinecone is only used when Qdrant isn't configured (the older setup).
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Literal

from opensearchpy import OpenSearch, helpers
from opensearchpy.exceptions import NotFoundError

from commerce.config import get_settings
from commerce.policies.documents import PolicyDocument, PolicySection, load_policies
from commerce.search.keyword import INDEX_BODY as PRODUCT_INDEX_BODY
from commerce.search.rrf import reciprocal_rank_fusion
from commerce.search.semantic import TEXT_FIELD, UPSERT_BATCH, get_semantic_index

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ai_commerce_retrieval.index import VectorIndex
    from ai_commerce_retrieval.records import Record

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


# --- Qdrant (decision 23) -----------------------------------------------------------------------

_QDRANT_RETRY_S = 60.0
_qdrant_lock = threading.Lock()
_qdrant: dict[str, Any] = {"index": None, "failed_at": 0.0, "synced": False}


def _policy_records() -> list[Record]:
    from ai_commerce_retrieval.records import Record

    return [
        Record(
            id=key,
            text=_semantic_text(doc, section),
            metadata={
                "cite": key,
                "doc_id": doc.id,
                "version": str(doc.version),
                "status": "approved",
                "effective_from": int(doc.effective_date.strftime("%Y%m%d")),
            },
        )
        for key, (doc, section) in _sections().items()
    ]


def _qdrant_policy_index() -> VectorIndex | None:
    """The policy collection, or None when meaning search isn't configured. A failure to
    connect is retried at most once a minute, so a down Qdrant doesn't slow every search."""
    from ai_commerce_retrieval.config import get_settings as retrieval_settings

    if not retrieval_settings().openai_api_key:
        return None
    with _qdrant_lock:
        if _qdrant["index"] is None:
            if time.monotonic() - _qdrant["failed_at"] < _QDRANT_RETRY_S:
                raise RuntimeError("qdrant unavailable (retrying soon)")
            try:
                from ai_commerce_retrieval.factory import vector_index

                _qdrant["index"] = vector_index("policies")
            except Exception:
                _qdrant["failed_at"] = time.monotonic()
                raise
        index: VectorIndex = _qdrant["index"]
        return index


def sync_policies_to_qdrant() -> dict[str, int] | None:
    """Make the Qdrant collection match the policy files, embedding only what changed."""
    index = _qdrant_policy_index()
    if index is None:
        return None
    result = index.sync(_policy_records())
    _qdrant["synced"] = True
    return {
        "added": result.added,
        "updated": result.updated,
        "deleted": result.deleted,
        "unchanged": result.unchanged,
    }


def _sync_in_background() -> None:
    if _qdrant["synced"]:
        return
    _qdrant["synced"] = True  # one attempt per process; reindex covers the rest

    def run() -> None:
        try:
            log.info("policy meaning index synced: %s", sync_policies_to_qdrant())
        except Exception as exc:  # noqa: BLE001 - keyword search still answers
            log.warning("policy meaning index sync failed: %s", type(exc).__name__)

    threading.Thread(target=run, name="policy-qdrant-sync", daemon=True).start()


_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="policy-semantic")


def _qdrant_ids(query: str, top_k: int) -> tuple[list[str], SemanticState] | None:
    """Qdrant's ranking, or None when it isn't configured (so Pinecone may be tried)."""
    try:
        index = _qdrant_policy_index()
    except Exception as exc:  # noqa: BLE001 - keyword results still answer
        log.warning("policy meaning search unavailable: %s", type(exc).__name__)
        return [], "unavailable"
    if index is None:
        return None
    _sync_in_background()
    try:
        future = _pool.submit(index.search, query, top_k)
        hits = future.result(timeout=get_settings().policy_semantic_timeout_ms / 1000)
    except (FutureTimeout, Exception) as exc:  # noqa: BLE001 - keyword results still answer
        log.warning("policy meaning search unavailable: %s", type(exc).__name__)
        return [], "unavailable"
    return [h.record_id for h in hits], "used"


def _semantic_ids(query: str, top_k: int) -> tuple[list[str], SemanticState]:
    if (qdrant := _qdrant_ids(query, top_k)) is not None:
        return qdrant
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


# Recent answers, by policy version and query. The same questions come up again and again
# ("how long do I have to return something?"), and each search costs an embedding call
# (~200-400 ms, more under load). Editing a policy changes content_hash(), so nothing stale is
# served; a result that fell back to keywords only isn't kept.
_CACHE_SIZE = 512
_CACHE_SECONDS = 600.0
_cache: dict[tuple[str, str, int], tuple[float, PolicySearchResult]] = {}
_cache_lock = threading.Lock()
# Its own threads: the meaning search below waits on _pool, so it can't run in _pool itself.
_searches = ThreadPoolExecutor(max_workers=8, thread_name_prefix="policy-search")


def _cache_key(query: str, top_k: int) -> tuple[str, str, int]:
    return (content_hash(), " ".join(query.lower().split()), top_k)


def search_policies(query: str, top_k: int = 5) -> PolicySearchResult:
    key = _cache_key(query, top_k)
    with _cache_lock:
        hit = _cache.get(key)
        if hit and time.monotonic() - hit[0] < _CACHE_SECONDS:
            return hit[1]
    sections = _sections()
    # Keywords (OpenSearch) and meaning (embedding + Qdrant) side by side, not one after the other.
    semantic = _searches.submit(_semantic_ids, query, top_k * 3)
    keyword_ids = get_policy_keyword_index().search(query, top_k=top_k * 3)
    semantic_ids, state = semantic.result()
    lists: Sequence[Sequence[str]] = [keyword_ids, semantic_ids] if semantic_ids else [keyword_ids]
    merged = reciprocal_rank_fusion(lists) if semantic_ids else keyword_ids
    hits = [PolicyHit(*sections[key]) for key in merged if key in sections][:top_k]
    result = PolicySearchResult(hits=hits, semantic=state)
    if state != "unavailable":
        with _cache_lock:
            if len(_cache) >= _CACHE_SIZE:
                _cache.pop(next(iter(_cache)))
            _cache[key] = (time.monotonic(), result)
    return result
