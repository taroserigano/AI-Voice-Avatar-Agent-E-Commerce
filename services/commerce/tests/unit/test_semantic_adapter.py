from __future__ import annotations

from commerce.search.documents import ProductSearchDoc
from commerce.search.semantic import SemanticIndex
from tests.unit.fakes.pinecone_standin import PineconeIndexStandIn


def _doc(i: int) -> ProductSearchDoc:
    return ProductSearchDoc(
        id=f"p{i}",
        title=f"Product {i}",
        brand="Brand",
        category_slug="electronics",
        category_name="Electronics",
        description="desc",
        skus=[f"SKU-{i}"],
        variant_text="Black",
        product_type="headphones",
        tags=["wireless"],
        tag_text="Wireless",
        specs_text="Battery: 40 hours.",
    )


def test_upsert_batches_stay_under_pinecone_limit() -> None:
    standin = PineconeIndexStandIn()
    index = SemanticIndex(standin, "products-test")

    assert index.upsert([_doc(i) for i in range(200)]) == 200

    sizes = [len(records) for _, records in standin.upsert_calls]
    assert sum(sizes) == 200
    assert max(sizes) <= 96
    assert {ns for ns, _ in standin.upsert_calls} == {"products-test"}


def test_upsert_embeds_descriptive_text_and_never_price_or_stock() -> None:
    standin = PineconeIndexStandIn()
    SemanticIndex(standin, "ns").upsert([_doc(1)])

    record = standin.upsert_calls[0][1][0]
    assert record["_id"] == "p1"
    assert "Product 1" in record["chunk_text"] and "Electronics" in record["chunk_text"]
    # Type, tags, and specs are embedded too, so "wireless headphones" matches on meaning.
    assert "Type: headphones" in record["chunk_text"] and "Wireless" in record["chunk_text"]
    assert "Battery: 40 hours." in record["chunk_text"]
    # Price and stock live only in PostgreSQL.
    assert not {k for k in record if "price" in k or "stock" in k or "available" in k}


def test_search_drops_hits_below_min_score_and_keeps_order() -> None:
    standin = PineconeIndexStandIn(scripted_hits=[("a", 0.9), ("b", 0.4), ("c", 0.1)])
    index = SemanticIndex(standin, "ns")

    assert index.search("rainy commute shoes", top_k=10, min_score=0.3) == ["a", "b"]
    assert standin.search_calls[0]["inputs"] == {"text": "rainy commute shoes"}
    assert standin.search_calls[0]["namespace"] == "ns"
