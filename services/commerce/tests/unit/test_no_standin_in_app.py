"""The Pinecone stand-in must never be reachable from app code (decision 2026-09-25)."""

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
    pattern = re.compile(r"pgvector|opensearch.*knn|faiss|chromadb|qdrant|weaviate|milvus", re.I)
    offenders = [
        str(path.relative_to(SRC))
        for path in SRC.rglob("*.py")
        if pattern.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == []
