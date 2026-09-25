"""Pinecone: meaning-based product search, using Pinecone's hosted embedding model.

Pinecone is the only vector store and is always the real service. When no API key is
configured, :func:`get_semantic_index` returns ``None`` and search reports the semantic leg
as disabled. There is deliberately no in-app substitute; the only stand-in lives in
``tests/unit/`` and cannot be selected by any setting.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterable
from typing import Any, Protocol

from commerce.config import Settings, get_settings
from commerce.search.documents import ProductSearchDoc

log = logging.getLogger(__name__)

# Pinecone accepts at most 96 records per upsert when it embeds the text itself.
UPSERT_BATCH = 90
TEXT_FIELD = "chunk_text"


class PineconeIndexLike(Protocol):
    """The slice of the Pinecone index client we use; lets unit tests pass a stand-in."""

    def upsert_records(self, *, records: list[dict[str, Any]], namespace: str) -> Any: ...

    def search(self, *, namespace: str, top_k: int, inputs: dict[str, Any], **kw: Any) -> Any: ...

    def delete(
        self, *, ids: list[str] | None = None, delete_all: bool = False, namespace: str = ""
    ) -> Any: ...


class SemanticIndex:
    def __init__(self, index: PineconeIndexLike, namespace: str) -> None:
        self.index = index
        self.namespace = namespace

    def upsert(self, docs: Iterable[ProductSearchDoc]) -> int:
        records = [
            {
                "_id": d.id,
                TEXT_FIELD: d.semantic_text(),
                "title": d.title,
                "brand": d.brand,
                "category_slug": d.category_slug,
            }
            for d in docs
        ]
        for start in range(0, len(records), UPSERT_BATCH):
            self.index.upsert_records(
                records=records[start : start + UPSERT_BATCH], namespace=self.namespace
            )
        return len(records)

    def delete(self, ids: Iterable[str]) -> None:
        id_list = list(ids)
        if id_list:
            self.index.delete(ids=id_list, namespace=self.namespace)

    def clear(self) -> None:
        try:
            self.index.delete(delete_all=True, namespace=self.namespace)
        except Exception as exc:  # noqa: BLE001 - a namespace that doesn't exist yet is fine
            log.info("pinecone clear skipped: %s", type(exc).__name__)

    def search(self, query: str, top_k: int, min_score: float = 0.0) -> list[str]:
        resp = self.index.search(
            namespace=self.namespace,
            top_k=top_k,
            inputs={"text": query},
            fields=["title"],
        )
        hits = resp.result.hits
        return [hit.id for hit in hits if (hit.score or 0.0) >= min_score]


class PineconeConfigError(RuntimeError):
    pass


def _field_map(description: Any) -> dict[str, Any]:
    embed = getattr(description, "embed", None)
    if embed is None:
        return {}
    field_map = getattr(embed, "field_map", None)
    if field_map is None and isinstance(embed, dict):
        field_map = embed.get("field_map")
    return dict(field_map or {})


def ensure_pinecone_index(settings: Settings) -> Any:
    """Create this app's integrated-embedding index if needed and return its client.

    Refuses to use an existing index that wasn't built for hosted embeddings on
    ``chunk_text``: the Pinecone project may hold other projects' indexes, and we must never
    write into one of those by pointing at it by mistake.
    """
    from pinecone import Pinecone

    pc = Pinecone(api_key=settings.pinecone_api_key)
    name = settings.pinecone_index
    if not pc.has_index(name):
        log.info("creating pinecone index %s", name)
        pc.create_index_for_model(
            name=name,
            cloud=settings.pinecone_cloud,
            region=settings.pinecone_region,
            embed={"model": settings.pinecone_embed_model, "field_map": {"text": TEXT_FIELD}},
        )
        for _ in range(60):
            if pc.describe_index(name).status.ready:
                break
            time.sleep(1)
    if _field_map(pc.describe_index(name)).get("text") != TEXT_FIELD:
        raise PineconeConfigError(
            f"Pinecone index {name!r} has no hosted embedding mapped to {TEXT_FIELD!r}, so it "
            "wasn't created by this app. Set PINECONE_INDEX_NAME to this app's own index "
            "(default 'ai-commerce'); nothing was written."
        )
    return pc.index(name)


_RETRY_AFTER_SECONDS = 60.0
_cached: SemanticIndex | None = None
_last_failure: tuple[float, Exception] | None = None


def get_semantic_index() -> SemanticIndex | None:
    """The Pinecone product index, or None when no key is configured.

    Setup failures are remembered for a minute so a misconfigured Pinecone doesn't add a
    round trip to every search; the error is re-raised so callers report "unavailable".
    """
    global _cached, _last_failure
    settings = get_settings()
    if not settings.pinecone_api_key:
        return None
    if _cached is not None:
        return _cached
    if _last_failure and time.monotonic() - _last_failure[0] < _RETRY_AFTER_SECONDS:
        raise _last_failure[1]
    try:
        _cached = SemanticIndex(ensure_pinecone_index(settings), settings.products_namespace)
    except Exception as exc:
        _last_failure = (time.monotonic(), exc)
        log.error("pinecone unavailable: %s", exc)
        raise
    return _cached
