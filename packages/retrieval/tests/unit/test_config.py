from __future__ import annotations

import re
from pathlib import Path

import pytest

from ai_commerce_retrieval.config import RetrievalSettings


def test_openai_key_is_read_from_the_shared_env_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPEN_AI_API", "sk-test")
    assert RetrievalSettings(_env_file=None).openai_api_key == "sk-test"


def test_qdrant_key_is_only_sent_over_https() -> None:
    local = RetrievalSettings(
        _env_file=None, qdrant_url="http://127.0.0.1:6333", qdrant_api_key="k"
    )
    cloud = RetrievalSettings(
        _env_file=None,
        qdrant_url="https://abc.us-east-1-0.aws.cloud.qdrant.io:6333",
        qdrant_api_key="k",
    )
    assert local.qdrant_key_for_url is None
    assert cloud.qdrant_key_for_url == "k"


SRC = Path(__file__).resolve().parents[2] / "src"


def test_app_code_never_imports_test_fakes_or_another_vector_store() -> None:
    forbidden = re.compile(
        r"^\s*(from|import)\s+tests(\.|\s|$)|HashingEmbedding|pinecone|pgvector|faiss|chromadb"
        r"|weaviate|milvus|VectorStoreIndex\.from_documents|SimpleVectorStore",
        re.M | re.I,
    )
    offenders = [
        str(p.relative_to(SRC)) for p in SRC.rglob("*.py") if forbidden.search(p.read_text("utf-8"))
    ]
    assert offenders == []
