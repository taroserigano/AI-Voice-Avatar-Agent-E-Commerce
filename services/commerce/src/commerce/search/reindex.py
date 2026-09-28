"""Rebuild OpenSearch and Pinecone from PostgreSQL (``pnpm reindex`` / ``make reindex``).

Both are projections, so this is always safe: it recreates the OpenSearch index and clears
this environment's Pinecone namespace before loading every active product again.
"""

from __future__ import annotations

import logging

from commerce.config import get_settings
from commerce.db import get_sessionmaker
from commerce.policies.search import (
    get_policy_keyword_index,
    sync_policies_to_qdrant,
    upsert_policies_to_pinecone,
)
from commerce.search.documents import load_docs
from commerce.search.keyword import get_keyword_index
from commerce.search.semantic import get_semantic_index

log = logging.getLogger(__name__)


def reindex() -> dict[str, int | str]:
    settings = get_settings()
    with get_sessionmaker()() as db:
        docs = load_docs(db)
    keyword = get_keyword_index()
    keyword.recreate_index()
    kw_count = keyword.upsert(docs)
    result: dict[str, int | str] = {"opensearch_index": keyword.index, "opensearch_docs": kw_count}
    policies = get_policy_keyword_index()
    result["opensearch_policy_index"] = policies.index
    result["opensearch_policy_sections"] = policies.rebuild()
    try:
        synced = sync_policies_to_qdrant()
        result["qdrant_policies"] = (
            "skipped: no OpenAI key for embeddings"
            if synced is None
            else ", ".join(f"{k} {v}" for k, v in synced.items())
        )
    except Exception as exc:  # noqa: BLE001 - report it; keyword search is already rebuilt
        result["qdrant_policies"] = f"FAILED: {type(exc).__name__}: {exc}"[:400]

    try:
        semantic = get_semantic_index()
    except Exception as exc:  # noqa: BLE001 - report it; OpenSearch is already rebuilt
        result["pinecone"] = f"FAILED: {type(exc).__name__}: {exc}"[:400]
        return result
    if semantic is None:
        result["pinecone"] = "skipped: PINECONE_API_KEY is not set"
    else:
        semantic.clear()
        result["pinecone_namespace"] = settings.products_namespace
        result["pinecone_records"] = semantic.upsert(docs)
        result["pinecone_policy_namespace"] = settings.policies_namespace
        result["pinecone_policy_records"] = upsert_policies_to_pinecone() or 0
    return result


def main() -> None:
    from commerce.telemetry import init_telemetry

    init_telemetry("commerce-reindex")
    result = reindex()
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
