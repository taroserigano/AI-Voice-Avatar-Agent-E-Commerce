"""App code never reaches test stand-ins, and uses only the chosen vector store."""

from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"
FORBIDDEN = re.compile(
    r"^\s*(from|import)\s+tests(\.|\s|$)|pinecone_standin|PineconeIndexStandIn", re.M
)


def test_app_code_never_imports_test_fakes() -> None:
    offenders = [
        str(path.relative_to(SRC))
        for path in SRC.rglob("*.py")
        if FORBIDDEN.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == []


def test_no_other_vector_store_in_app_code() -> None:
    pattern = re.compile(r"pgvector|opensearch.*knn|faiss|chromadb|weaviate|milvus", re.I)
    offenders = [
        str(path.relative_to(SRC))
        for path in SRC.rglob("*.py")
        if pattern.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == []


def test_qdrant_is_reached_only_through_the_shared_retrieval_package() -> None:
    """Qdrant replaced Pinecone (decision 23). App code goes through ai_commerce_retrieval
    (strict collections this app owns, LlamaIndex ingestion), never the raw client."""
    raw = re.compile(r"^\s*(from|import)\s+(qdrant_client|llama_index)", re.M)
    offenders = [
        str(path.relative_to(SRC))
        for path in SRC.rglob("*.py")
        if raw.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == []
