"""Meaning-based retrieval for ai-commerce: LlamaIndex ingestion into Qdrant (the only
vector store), and hybrid search fused with OpenSearch keyword results."""

from ai_commerce_retrieval.fusion import reciprocal_rank_fusion, rrf_scores
from ai_commerce_retrieval.hybrid import HybridRetriever, KeywordSearch, SemanticSearch
from ai_commerce_retrieval.index import SyncResult, VectorIndex
from ai_commerce_retrieval.qdrant_collections import CollectionOwnershipError, collection_name
from ai_commerce_retrieval.records import Hit, Record

__all__ = [
    "CollectionOwnershipError",
    "Hit",
    "HybridRetriever",
    "KeywordSearch",
    "Record",
    "SemanticSearch",
    "SyncResult",
    "VectorIndex",
    "collection_name",
    "reciprocal_rank_fusion",
    "rrf_scores",
]
