"""A meaning-search index over one Qdrant collection: LlamaIndex ingestion in, hits out.

Writes go through LlamaIndex's ``IngestionPipeline`` (embed, then ``QdrantVectorStore``).
:meth:`VectorIndex.sync` is incremental: it compares each record's content hash with the
one stored in Qdrant and only embeds what changed, so a reindex costs nothing when nothing
changed. The collection is a projection; :meth:`VectorIndex.clear` plus a sync rebuilds it.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.vector_stores.types import MetadataFilters, VectorStoreQuery
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from ai_commerce_retrieval.qdrant_collections import (
    DENSE_VECTOR,
    Filterable,
    drop_collection,
    ensure_collection,
)
from ai_commerce_retrieval.records import CONTENT_HASH_KEY, RECORD_ID_KEY, Hit, Record

_SCROLL_PAGE = 256
# LlamaIndex's own payload keys; not app metadata.
_INTERNAL_KEYS = frozenset(
    {"_node_content", "_node_type", "doc_id", "document_id", "ref_doc_id", CONTENT_HASH_KEY}
)


@dataclass(frozen=True)
class SyncResult:
    added: int
    updated: int
    deleted: int
    unchanged: int


class VectorIndex:
    def __init__(
        self,
        client: QdrantClient,
        collection: str,
        embed_model: BaseEmbedding,
        *,
        corpus: str,
        embed_model_name: str,
        dimensions: int,
        filterable: Filterable | None = None,
    ) -> None:
        """``filterable``: payload fields to index for filters (default: the corpus's)."""
        self.client = client
        self.collection = collection
        self.embed_model = embed_model
        self.corpus = corpus
        self.embed_model_name = embed_model_name
        self.dimensions = dimensions
        self.filterable = filterable
        self._ensure()
        self.store = self._new_store()

    def _ensure(self) -> None:
        ensure_collection(
            self.client,
            self.collection,
            corpus=self.corpus,
            embed_model=self.embed_model_name,
            dimensions=self.dimensions,
            filterable=self.filterable,
        )

    def _new_store(self) -> QdrantVectorStore:
        return QdrantVectorStore(
            collection_name=self.collection,
            client=self.client,
            dense_vector_name=DENSE_VECTOR,
        )

    # --- writes -------------------------------------------------------------------------

    def stored_hashes(self) -> dict[str, str]:
        """record_id -> content_hash for every point in the collection."""
        found: dict[str, str] = {}
        offset = None
        while True:
            points, offset = self.client.scroll(
                self.collection,
                limit=_SCROLL_PAGE,
                offset=offset,
                with_payload=[RECORD_ID_KEY, CONTENT_HASH_KEY],
                with_vectors=False,
            )
            for p in points:
                payload = p.payload or {}
                if RECORD_ID_KEY in payload:
                    found[str(payload[RECORD_ID_KEY])] = str(payload.get(CONTENT_HASH_KEY, ""))
            if offset is None:
                return found

    def upsert(self, records: Iterable[Record]) -> int:
        nodes = [r.to_node() for r in records]
        if nodes:
            IngestionPipeline(transformations=[self.embed_model], vector_store=self.store).run(
                nodes=nodes
            )
        return len(nodes)

    def delete(self, record_ids: Iterable[str]) -> None:
        ids = [Record(id=r, text="").point_id for r in record_ids]
        if ids:
            self.store.delete_nodes(node_ids=ids)

    def sync(self, records: Iterable[Record]) -> SyncResult:
        """Make the collection hold exactly ``records``, embedding only what changed."""
        wanted = {r.id: r for r in records}
        stored = self.stored_hashes()
        changed = [r for rid, r in wanted.items() if stored.get(rid) != r.content_hash]
        gone = [rid for rid in stored if rid not in wanted]
        self.upsert(changed)
        self.delete(gone)
        added = sum(1 for r in changed if r.id not in stored)
        return SyncResult(
            added=added,
            updated=len(changed) - added,
            deleted=len(gone),
            unchanged=len(wanted) - len(changed),
        )

    def clear(self) -> None:
        """Drop and recreate the collection (it's a projection, so this is always safe)."""
        drop_collection(self.client, self.collection)
        self._ensure()
        self.store = self._new_store()

    # --- reads --------------------------------------------------------------------------

    def search(
        self,
        query: str,
        top_k: int,
        *,
        filters: MetadataFilters | None = None,
        min_score: float = 0.0,
    ) -> list[Hit]:
        result = self.store.query(
            VectorStoreQuery(
                query_embedding=self.embed_model.get_query_embedding(query),
                similarity_top_k=top_k,
                filters=filters,
            )
        )
        hits: list[Hit] = []
        for node, score in zip(result.nodes or [], result.similarities or [], strict=False):
            if score < min_score:
                continue
            metadata = {k: v for k, v in node.metadata.items() if k not in _INTERNAL_KEYS}
            record_id = str(metadata.pop(RECORD_ID_KEY, node.node_id))
            hits.append(
                Hit(record_id=record_id, score=score, text=node.get_content(), metadata=metadata)
            )
        return hits

    def count(self) -> int:
        return self.client.count(self.collection, exact=True).count


def record_ids(hits: Sequence[Hit]) -> list[str]:
    return [h.record_id for h in hits]
