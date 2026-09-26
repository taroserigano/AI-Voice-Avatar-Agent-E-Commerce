"""Against a real Qdrant: the local one from `pnpm local:up`, or another server named by
RETRIEVAL_TEST_QDRANT_URL (and _API_KEY), e.g. Qdrant Cloud. Embeddings use a deterministic
test model; the one test that calls OpenAI is opt-in because it costs money."""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from datetime import date

import pytest
from llama_index.core import Settings as LlamaSettings
from llama_index.core.vector_stores.types import (
    FilterOperator,
    MetadataFilter,
    MetadataFilters,
)
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

from ai_commerce_retrieval.config import get_settings
from ai_commerce_retrieval.hybrid import HybridRetriever
from ai_commerce_retrieval.index import VectorIndex, record_ids
from ai_commerce_retrieval.qdrant_collections import (
    CORPUS_FILTERS,
    CollectionOwnershipError,
    Filterable,
    collection_name,
    drop_collection,
)
from ai_commerce_retrieval.records import Hit, Record
from tests.fakes import DIMS, ExplodingEmbedding, HashingEmbedding

pytestmark = pytest.mark.integration

PRODUCTS = [
    Record(id="p-milk-ff", text="Organic fat free milk, one gallon", metadata={"type": "milk"}),
    Record(id="p-milk-whole", text="Whole milk, half gallon", metadata={"type": "milk"}),
    Record(id="p-yogurt-sf", text="Sugar free Greek yogurt, vanilla", metadata={"type": "yogurt"}),
]


@pytest.fixture(scope="module")
def client() -> Iterator[QdrantClient]:
    settings = get_settings()
    c = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_key_for_url, timeout=5)
    try:
        c.get_collections()
    except Exception as exc:  # noqa: BLE001
        pytest.fail(f"Qdrant isn't reachable at {settings.qdrant_url} ({exc}); run `pnpm local:up`")
    yield c
    # This run's collections all end in its throwaway SEARCH_ENV suffix.
    run_suffix = collection_name("x", settings.search_env).removeprefix("aic-x")
    for col in c.get_collections().collections:
        if col.name.startswith("aic-") and col.name.endswith(run_suffix):
            c.delete_collection(col.name)


@pytest.fixture
def corpus() -> str:
    return f"c{uuid.uuid4().hex[:6]}"


def make_index(
    client: QdrantClient,
    corpus: str,
    embed: HashingEmbedding | None = None,
    filterable: Filterable | None = None,
) -> VectorIndex:
    return VectorIndex(
        client,
        collection_name(corpus, get_settings().search_env),
        embed or HashingEmbedding(),
        corpus=corpus,
        embed_model_name="test-hashing",
        dimensions=DIMS,
        filterable=filterable,
    )


def test_sync_embeds_only_what_changed(client: QdrantClient, corpus: str) -> None:
    embed = HashingEmbedding()
    index = make_index(client, corpus, embed)

    first = index.sync(PRODUCTS)
    assert (first.added, first.updated, first.deleted, first.unchanged) == (3, 0, 0, 0)
    assert embed.documents_embedded == 3

    again = index.sync(PRODUCTS)
    assert (again.added, again.updated, again.deleted, again.unchanged) == (0, 0, 0, 3)
    assert embed.documents_embedded == 3  # nothing re-embedded

    renamed = Record(id="p-milk-whole", text="Whole milk, one gallon", metadata={"type": "milk"})
    changed = index.sync([PRODUCTS[0], renamed])
    assert (changed.added, changed.updated, changed.deleted, changed.unchanged) == (0, 1, 1, 1)
    assert embed.documents_embedded == 4
    assert index.count() == 2
    assert index.stored_hashes() == {r.id: r.content_hash for r in [PRODUCTS[0], renamed]}


def test_search_ranks_by_meaning_and_returns_app_ids(client: QdrantClient, corpus: str) -> None:
    index = make_index(client, corpus)
    index.sync(PRODUCTS)

    top = index.search("fat free organic milk", top_k=3)

    assert top[0].record_id == "p-milk-ff"
    assert top[0].text == "Organic fat free milk, one gallon"
    assert top[0].metadata == {"type": "milk"}  # no LlamaIndex internals or hashes leak out


def test_policy_filters_exclude_drafts_and_future_versions(
    client: QdrantClient, corpus: str
) -> None:
    today = int(date.today().strftime("%Y%m%d"))
    index = make_index(client, corpus, filterable=CORPUS_FILTERS["policies"])
    index.sync(
        [
            Record(
                id="returns#rr-2-1@v3",
                text="Refunds go back to the original card within 5 business days",
                metadata={
                    "cite": "returns#rr-2-1",
                    "status": "approved",
                    "effective_from": 20260901,
                },
            ),
            Record(
                id="returns#rr-2-1@v4",
                text="Refunds go back to the original card within 3 business days",
                metadata={
                    "cite": "returns#rr-2-1",
                    "status": "approved",
                    "effective_from": today + 100,
                },
            ),
            Record(
                id="returns#rr-9-9@draft",
                text="Refunds go back as store credit",
                metadata={"cite": "returns#rr-9-9", "status": "draft", "effective_from": 20260101},
            ),
        ]
    )
    in_force = MetadataFilters(
        filters=[
            MetadataFilter(key="status", value="approved"),
            MetadataFilter(key="effective_from", value=today, operator=FilterOperator.LTE),
        ]
    )

    found = index.search("how are refunds paid back", top_k=5, filters=in_force)

    assert record_ids(found) == ["returns#rr-2-1@v3"]


def test_filters_on_unindexed_fields_are_refused_like_qdrant_cloud(
    client: QdrantClient, corpus: str
) -> None:
    """Collections are strict (as Qdrant Cloud is), so a missing index fails locally too."""
    index = make_index(client, corpus, filterable={})
    index.sync(PRODUCTS)
    unindexed = MetadataFilters(filters=[MetadataFilter(key="type", value="milk")])

    with pytest.raises(UnexpectedResponse, match="Index required"):
        index.search("milk", top_k=3, filters=unindexed)


def test_reopening_adds_newly_declared_filter_indexes(client: QdrantClient, corpus: str) -> None:
    make_index(client, corpus, filterable={}).sync(PRODUCTS)
    index = make_index(client, corpus, filterable={"type": models.PayloadSchemaType.KEYWORD})

    only_yogurt = MetadataFilters(filters=[MetadataFilter(key="type", value="yogurt")])
    assert record_ids(index.search("milk", top_k=3, filters=only_yogurt)) == ["p-yogurt-sf"]


def test_refuses_a_collection_this_app_did_not_create(client: QdrantClient, corpus: str) -> None:
    name = collection_name(corpus, get_settings().search_env)
    client.create_collection(
        name, vectors_config=models.VectorParams(size=DIMS, distance=models.Distance.COSINE)
    )

    with pytest.raises(CollectionOwnershipError, match="wasn't created by this app"):
        make_index(client, corpus)
    with pytest.raises(CollectionOwnershipError):
        drop_collection(client, name)
    assert client.count(name).count == 0
    client.delete_collection(name)


def test_refuses_to_mix_embedding_models(client: QdrantClient, corpus: str) -> None:
    make_index(client, corpus).sync(PRODUCTS[:1])

    with pytest.raises(CollectionOwnershipError, match="built differently"):
        VectorIndex(
            client,
            collection_name(corpus, get_settings().search_env),
            HashingEmbedding(),
            corpus=corpus,
            embed_model_name="text-embedding-3-small",
            dimensions=1536,
        )


def test_clear_rebuilds_an_empty_collection(client: QdrantClient, corpus: str) -> None:
    index = make_index(client, corpus)
    index.sync(PRODUCTS)

    index.clear()

    assert index.count() == 0
    assert index.sync(PRODUCTS).added == 3


def test_never_falls_back_to_llamaindex_global_settings(
    client: QdrantClient, corpus: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """LlamaIndex's defaults would pick OpenAI models silently; we always pass our own."""
    monkeypatch.setattr(LlamaSettings, "_embed_model", ExplodingEmbedding())
    index = make_index(client, corpus)

    index.sync(PRODUCTS)
    assert index.search("yogurt", top_k=1)[0].record_id == "p-yogurt-sf"


def test_hybrid_search_fuses_keyword_hits_with_real_qdrant(
    client: QdrantClient, corpus: str
) -> None:
    index = make_index(client, corpus)
    index.sync(PRODUCTS)

    class Keyword:
        def search(self, query: str, top_k: int) -> list[Hit]:
            return [
                Hit(
                    record_id="p-milk-whole", score=9.0, text="Whole milk, half gallon", metadata={}
                )
            ]

    retriever = HybridRetriever(
        keyword=Keyword(), semantic=index, top_k=3, semantic_timeout_ms=2000
    )
    result = retriever.search("whole milk")

    assert result[0].record_id == "p-milk-whole"  # found by both legs
    assert retriever.last_legs == {"keyword": "ok", "semantic": "ok"}


@pytest.mark.openai
@pytest.mark.skipif(
    os.environ.get("RETRIEVAL_LIVE_EMBED") != "1", reason="set RETRIEVAL_LIVE_EMBED=1"
)
def test_real_openai_embeddings_find_by_meaning(client: QdrantClient, corpus: str) -> None:
    from ai_commerce_retrieval.embeddings import openai_embedder

    settings = get_settings()
    index = VectorIndex(
        client,
        collection_name(corpus, settings.search_env),
        openai_embedder(settings),
        corpus=corpus,
        embed_model_name=settings.embed_model,
        dimensions=settings.embed_dimensions,
    )
    index.sync(PRODUCTS)

    assert index.search("yoghurt without sugar", top_k=1)[0].record_id == "p-yogurt-sf"
    # No words in common with any record: only meaning can match it.
    assert index.search("a dairy drink", top_k=1)[0].metadata["type"] == "milk"
    # Not asserted: "skim milk" ranks whole milk above fat free milk with
    # text-embedding-3-small. Synonyms like that are the keyword leg's and tags' job, and
    # belong in the search eval, not here.
