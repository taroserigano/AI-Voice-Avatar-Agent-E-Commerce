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

# Applied at search time only, so changing them needs no reindex of the data itself (just
# `pnpm reindex` to recreate the index settings). Rules can't contain English stopwords
# such as "no" or "not": those are removed before synonyms apply.
SYNONYMS = [
    "nonfat, non fat, fat free, skim, zero fat",
    "sugar free, zero sugar, sugarless",
    "dairy free, non dairy, nondairy",
    "decaf, decaffeinated",
    "soda, pop, soft drink",
    "tv, television",
    "earbuds, earphones",
    "sneakers, trainers, tennis shoes",
    # One way: "shoes" also finds boots and sandals, but "boots" doesn't find every shoe.
    "shoes => shoes, boots, sneakers, sandals, footwear",
    "hoodie, hooded sweatshirt",
    "cilantro, coriander",
]

# Typo tolerance, applied at search time (no reindex). OpenSearch's plain "AUTO" allows one
# edit from 3 letters, so "ipad" matched "pad" (Puppy Training Pads, Pad Thai) and "milk"
# matched "mild". Words under 5 letters must be spelled right; 5-7 letters may be one edit
# off ("bananna", "yoghurt", "lactos"), longer words two. The first letter must match. The
# re-ranker (search.ranking.close_spelling) uses the same rule.
FUZZINESS = "AUTO:5,8"
FUZZY_PREFIX_LENGTH = 1

# English analysis like the built-in "english" analyzer, plus shop synonyms when searching.
_EN = {"type": "text", "analyzer": "shop", "search_analyzer": "shop_search"}

INDEX_BODY: dict[str, Any] = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "filter": {
                "english_possessive": {"type": "stemmer", "language": "possessive_english"},
                "english_stop": {"type": "stop", "stopwords": "_english_"},
                "english_stemmer": {"type": "stemmer", "language": "english"},
                "shop_synonyms": {"type": "synonym_graph", "synonyms": SYNONYMS},
            },
            "analyzer": {
                "shop": {
                    "tokenizer": "standard",
                    "filter": [
                        "english_possessive",
                        "lowercase",
                        "english_stop",
                        "english_stemmer",
                    ],
                },
                "shop_search": {
                    "tokenizer": "standard",
                    "filter": [
                        "english_possessive",
                        "lowercase",
                        "english_stop",
                        "shop_synonyms",
                        "english_stemmer",
                    ],
                },
            },
        },
    },
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "title": {**_EN, "fields": {"raw": {"type": "keyword"}}},
            "brand": {**_EN, "fields": {"raw": {"type": "keyword"}}},
            "category_slug": {"type": "keyword"},
            "category_name": _EN,
            "description": _EN,
            "variant_text": _EN,
            "skus": {"type": "keyword"},
            "product_type": {"type": "keyword"},
            "type_text": _EN,
            "tags": {"type": "keyword"},
            "tag_text": _EN,
            "specs_text": _EN,
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
                    "product_type": d.product_type,
                    "type_text": d.type_text,
                    "tags": d.tags,
                    "tag_text": d.tag_text,
                    "specs_text": d.specs_text,
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
                                    "type_text^3",
                                    "brand^2",
                                    "category_name^2",
                                    "tag_text^2",
                                    "variant_text",
                                    "specs_text",
                                    "description",
                                ],
                                "type": "best_fields",
                                "fuzziness": FUZZINESS,
                                "prefix_length": FUZZY_PREFIX_LENGTH,
                                # 1-2 terms: all must match; more: at least 75% must.
                                "minimum_should_match": "2<75%",
                                "boost": 3,
                            }
                        },
                        {
                            # Every term, but spread across fields: "dairy free milk" finds
                            # a product titled "Almond Milk" whose tags say "Dairy free".
                            "multi_match": {
                                "query": query,
                                "fields": ["title^3", "type_text^2", "tag_text^2", "brand"],
                                "type": "cross_fields",
                                "operator": "and",
                                "boost": 3,
                            }
                        },
                        {
                            # Partial matches rank below full ones but still show up, so
                            # "wireless headphones" also finds earbuds and wired headphones.
                            "multi_match": {
                                "query": query,
                                "fields": ["title^3", "type_text^2", "brand^2", "variant_text"],
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
