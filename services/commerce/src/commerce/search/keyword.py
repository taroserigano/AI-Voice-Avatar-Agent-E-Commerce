"""OpenSearch: keywords, exact SKUs, typo tolerance. A rebuildable projection of PostgreSQL."""

from __future__ import annotations

import contextlib
from collections.abc import Iterable
from functools import lru_cache
from typing import Any

from opensearchpy import OpenSearch, helpers
from opensearchpy.exceptions import NotFoundError

from commerce.config import get_settings
from commerce.search.documents import ProductSearchDoc

INDEX_BODY: dict[str, Any] = {
    "settings": {"number_of_shards": 1, "number_of_replicas": 0},
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "title": {
                "type": "text",
                "analyzer": "english",
                "fields": {"raw": {"type": "keyword"}},
            },
            "brand": {
                "type": "text",
                "analyzer": "english",
                "fields": {"raw": {"type": "keyword"}},
            },
            "category_slug": {"type": "keyword"},
            "category_name": {"type": "text", "analyzer": "english"},
            "description": {"type": "text", "analyzer": "english"},
            "variant_text": {"type": "text", "analyzer": "english"},
            "skus": {"type": "keyword"},
        },
    },
}


class KeywordIndex:
    def __init__(self, client: OpenSearch, index: str) -> None:
        self.client = client
        self.index = index

    def ensure_index(self) -> None:
        if not self.client.indices.exists(index=self.index):
            self.client.indices.create(index=self.index, body=INDEX_BODY)

    def recreate_index(self) -> None:
        self.client.indices.delete(index=self.index, ignore_unavailable=True)
        self.client.indices.create(index=self.index, body=INDEX_BODY)

    def upsert(self, docs: Iterable[ProductSearchDoc]) -> int:
        actions = [
            {
                "_op_type": "index",
                "_index": self.index,
                "_id": d.id,
                "_source": {
                    "title": d.title,
                    "brand": d.brand,
                    "category_slug": d.category_slug,
                    "category_name": d.category_name,
                    "description": d.description,
                    "variant_text": d.variant_text,
                    "skus": d.skus,
                },
            }
            for d in docs
        ]
        if not actions:
            return 0
        ok, _ = helpers.bulk(self.client, actions, refresh="wait_for")
        return int(ok)

    def delete(self, ids: Iterable[str]) -> None:
        for doc_id in ids:
            with contextlib.suppress(NotFoundError):
                self.client.delete(index=self.index, id=doc_id, refresh="wait_for")

    def search(self, query: str, top_k: int) -> list[str]:
        body = {
            "size": top_k,
            "_source": False,
            "query": {
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": [
                                    "title^3",
                                    "brand^2",
                                    "category_name^2",
                                    "variant_text",
                                    "description",
                                ],
                                "type": "best_fields",
                                "fuzziness": "AUTO",
                                # 1-2 terms: all must match; more: at least 75% must.
                                "minimum_should_match": "2<75%",
                                "boost": 3,
                            }
                        },
                        {
                            # Partial matches rank below full ones but still show up, so
                            # "wireless headphones" also finds earbuds and wired headphones.
                            "multi_match": {
                                "query": query,
                                "fields": ["title^3", "brand^2", "variant_text"],
                                "type": "best_fields",
                                "operator": "or",
                            }
                        },
                        {"term": {"skus": {"value": query.strip().upper(), "boost": 10}}},
                    ],
                    "minimum_should_match": 1,
                }
            },
        }
        resp = self.client.search(index=self.index, body=body)
        return [hit["_id"] for hit in resp["hits"]["hits"]]


@lru_cache
def get_keyword_index() -> KeywordIndex:
    settings = get_settings()
    client = OpenSearch(
        hosts=[settings.opensearch_url],
        timeout=2,
        max_retries=1,
        retry_on_timeout=False,
    )
    return KeywordIndex(client, settings.products_index)
