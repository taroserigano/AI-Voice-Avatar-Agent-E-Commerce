"""Qdrant collections this app owns, and the guard that refuses everyone else's.

The Qdrant server (Qdrant Cloud especially) may hold other projects' collections. Every
collection this app creates carries ``metadata.owner == "ai-commerce"`` plus the embedding
model and size it was built with, and nothing is ever written to a collection without them.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from qdrant_client import QdrantClient, models

OWNER = "ai-commerce"
DENSE_VECTOR = "text-dense"  # LlamaIndex's default name for the dense vector

Filterable = Mapping[str, models.PayloadSchemaType]
# Payload fields each corpus filters on. Qdrant Cloud's strict mode refuses filters on
# unindexed fields, and every collection here is created in strict mode so local matches it.
CORPUS_FILTERS: dict[str, Filterable] = {
    "policies": {
        "cite": models.PayloadSchemaType.KEYWORD,
        "doc_id": models.PayloadSchemaType.KEYWORD,
        "version": models.PayloadSchemaType.KEYWORD,
        "status": models.PayloadSchemaType.KEYWORD,
        "effective_from": models.PayloadSchemaType.INTEGER,
    },
    "products": {
        "type": models.PayloadSchemaType.KEYWORD,
        "category_slug": models.PayloadSchemaType.KEYWORD,
        "tags": models.PayloadSchemaType.KEYWORD,
    },
}
STRICT = models.StrictModeConfig(
    enabled=True, unindexed_filtering_retrieve=False, unindexed_filtering_update=False
)


class CollectionOwnershipError(RuntimeError):
    pass


def collection_name(corpus: str, search_env: str) -> str:
    """``aic-<corpus>-<env>``, e.g. ``aic-policies-dev-taro``."""
    safe = re.sub(r"[^a-z0-9-]+", "-", f"{corpus}-{search_env}".lower()).strip("-")
    return f"aic-{safe}"


def _metadata(client: QdrantClient, name: str) -> dict[str, Any]:
    return dict(client.get_collection(name).config.metadata or {})


def ensure_collection(
    client: QdrantClient,
    name: str,
    *,
    corpus: str,
    embed_model: str,
    dimensions: int,
    filterable: Filterable | None = None,
) -> None:
    """Create the collection if needed; refuse one that isn't ours or was built differently.

    Also makes sure every ``filterable`` payload field (default: the corpus's
    :data:`CORPUS_FILTERS`) has an index, adding any that a newer version declares.
    """
    fields = {"record_id": models.PayloadSchemaType.KEYWORD}
    fields.update(CORPUS_FILTERS.get(corpus, {}) if filterable is None else filterable)
    expected = {
        "owner": OWNER,
        "corpus": corpus,
        "embed_model": embed_model,
        "dimensions": dimensions,
    }
    if not client.collection_exists(name):
        client.create_collection(
            collection_name=name,
            vectors_config={
                DENSE_VECTOR: models.VectorParams(size=dimensions, distance=models.Distance.COSINE)
            },
            metadata=expected,
            strict_mode_config=STRICT,
        )
        _ensure_payload_indexes(client, name, fields)
        return

    found = _metadata(client, name)
    if found.get("owner") != OWNER:
        raise CollectionOwnershipError(
            f"Qdrant collection {name!r} wasn't created by this app (no owner={OWNER!r} "
            "metadata), so nothing was written. Pick another SEARCH_ENV or remove it yourself."
        )
    mismatched = {k: (found.get(k), v) for k, v in expected.items() if found.get(k) != v}
    if mismatched:
        detail = ", ".join(
            f"{k}: stored {a!r}, configured {b!r}" for k, (a, b) in mismatched.items()
        )
        raise CollectionOwnershipError(
            f"Qdrant collection {name!r} was built differently ({detail}). "
            "Rebuild it (pnpm reindex) instead of mixing embeddings."
        )
    _ensure_payload_indexes(client, name, fields)


def _ensure_payload_indexes(client: QdrantClient, name: str, fields: Filterable) -> None:
    existing = client.get_collection(name).payload_schema or {}
    for field_name, schema in fields.items():
        if field_name not in existing:
            client.create_payload_index(name, field_name, schema, wait=True)


def drop_collection(client: QdrantClient, name: str) -> bool:
    """Delete one of our collections; refuses anyone else's. False if it didn't exist."""
    if not client.collection_exists(name):
        return False
    if _metadata(client, name).get("owner") != OWNER:
        raise CollectionOwnershipError(f"refusing to delete {name!r}: not created by this app")
    client.delete_collection(name)
    return True
