from __future__ import annotations

import uuid

import pytest
from llama_index.core.schema import MetadataMode

from ai_commerce_retrieval.qdrant_collections import collection_name
from ai_commerce_retrieval.records import Record, point_id


def test_content_hash_ignores_metadata_order_but_not_values() -> None:
    a = Record(id="p1", text="Fat free milk", metadata={"brand": "Larkspur", "type": "milk"})
    same = Record(id="p1", text="Fat free milk", metadata={"type": "milk", "brand": "Larkspur"})
    other_text = Record(id="p1", text="Whole milk", metadata={"brand": "Larkspur", "type": "milk"})
    other_meta = Record(id="p1", text="Fat free milk", metadata={"brand": "Other", "type": "milk"})

    assert a.content_hash == same.content_hash
    assert a.content_hash != other_text.content_hash
    assert a.content_hash != other_meta.content_hash


def test_point_ids_are_stable_uuids_per_record() -> None:
    assert point_id("returns-and-refunds#rr-2-1") == point_id("returns-and-refunds#rr-2-1")
    assert point_id("a") != point_id("b")
    uuid.UUID(point_id("any id at all, even with spaces#and@symbols"))  # Qdrant needs a UUID


def test_reserved_metadata_keys_are_rejected() -> None:
    with pytest.raises(ValueError, match="reserved"):
        Record(id="p1", text="x", metadata={"record_id": "spoof"})


def test_only_the_record_text_is_embedded() -> None:
    """Metadata is for filters and display; prepending it would change what's embedded."""
    node = Record(id="p1", text="Sugar free yogurt", metadata={"status": "approved"}).to_node()

    assert node.get_content(metadata_mode=MetadataMode.EMBED) == "Sugar free yogurt"
    assert node.metadata["record_id"] == "p1"


def test_collection_names_are_prefixed_and_safe() -> None:
    assert collection_name("policies", "dev-taro") == "aic-policies-dev-taro"
    assert collection_name("products", "Test_A1 b") == "aic-products-test-a1-b"
