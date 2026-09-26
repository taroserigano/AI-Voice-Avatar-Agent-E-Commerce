"""What goes into the vector store: app records, and their LlamaIndex nodes.

A :class:`Record` is the app's view (a product ID, or a policy section's ``doc#section``
citation key). Qdrant point IDs must be UUIDs, so each record maps to a stable UUIDv5 and
keeps its own ID in the payload as ``record_id``.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field

from llama_index.core.schema import TextNode

# Fixed namespace for record -> point IDs. Changing it orphans every stored point.
POINT_NAMESPACE = uuid.UUID("5f0a3c1e-2b7d-4e8a-9c41-6d2f8b1a7e30")
RECORD_ID_KEY = "record_id"
CONTENT_HASH_KEY = "content_hash"
RESERVED_KEYS = frozenset({RECORD_ID_KEY, CONTENT_HASH_KEY})

MetadataValue = str | int | float | bool | list[str]


@dataclass(frozen=True)
class Record:
    id: str
    text: str  # exactly what gets embedded
    metadata: Mapping[str, MetadataValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        clash = RESERVED_KEYS & set(self.metadata)
        if clash:
            raise ValueError(f"metadata keys {sorted(clash)} are reserved")
        if not self.id:
            raise ValueError("a record needs an id")

    @property
    def point_id(self) -> str:
        return point_id(self.id)

    @property
    def content_hash(self) -> str:
        """Changes when the embedded text or any stored metadata changes."""
        canonical = json.dumps(
            {"text": self.text, "metadata": dict(self.metadata)}, sort_keys=True, ensure_ascii=False
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_node(self) -> TextNode:
        metadata: dict[str, MetadataValue] = {
            **self.metadata,
            RECORD_ID_KEY: self.id,
            CONTENT_HASH_KEY: self.content_hash,
        }
        keys = list(metadata)
        return TextNode(
            id_=self.point_id,
            text=self.text,
            metadata=metadata,
            # The record's text is the whole embedding input; metadata is for filtering and
            # display, so LlamaIndex must not prepend it to the text it embeds.
            excluded_embed_metadata_keys=keys,
            excluded_llm_metadata_keys=keys,
        )


def point_id(record_id: str) -> str:
    return str(uuid.uuid5(POINT_NAMESPACE, record_id))


@dataclass(frozen=True)
class Hit:
    """One search result, in app terms."""

    record_id: str
    score: float
    text: str
    metadata: Mapping[str, MetadataValue]
