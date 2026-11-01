"""Export the catalog-stores seed catalog as spreadsheet and structured reports.

Run from the repository root with ``python scripts/export_product_report.py``.
The source worktree can also be supplied with ``--source``.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / ".claude/worktrees/catalog-stores"
DEFAULT_OUTPUT = ROOT / "reports/product-catalog"
NUTRITION_FIELDS = (
    "serving_size",
    "calories",
    "total_fat_g",
    "saturated_fat_g",
    "sodium_mg",
    "total_carbs_g",
    "fiber_g",
    "total_sugars_g",
    "added_sugars_g",
    "protein_g",
    "net_carbs_g",
)
ATTRIBUTE_FIELDS = ("age", "color", "fits", "length", "net_oz", "shade", "size", "storage", "value")
CSV_FIELDS = (
    "product_slug", "product_title", "brand", "category_slug", "category_name",
    "return_policy_class", "product_type", "description", "tags", "ingredients",
    "allergens", "specs_json", "image_path", "base_price_usd", "variant_sku",
    "variant_code", "variant_name", "variant_attributes_json", "variant_price_usd",
    "seed_stock_on_hand", "seed_stock_reserved", "seed_stock_available",
    *(f"variant_{field}" for field in ATTRIBUTE_FIELDS),
    *(f"nutrition_{field}" for field in NUTRITION_FIELDS),
)


def dollars(cents: int) -> str:
    return str(Decimal(cents) / 100)


def compact_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    sys.path.insert(0, str(source / "services/commerce/src"))

    from commerce.seed.catalog import PRODUCTS  # noqa: PLC0415
    from commerce.seed.data import CATEGORIES  # noqa: PLC0415
    from commerce.seed.run import make_sku  # noqa: PLC0415

    categories = {category.slug: category for category in CATEGORIES}
    if len({product.slug for product in PRODUCTS}) != len(PRODUCTS):
        raise ValueError("Duplicate product slugs in source catalog")
    output.mkdir(parents=True, exist_ok=True)
    csv_path = output / "product_variants.csv"
    jsonl_path = output / "products.jsonl"
    counts = Counter()
    skus: set[str] = set()

    with csv_path.open("w", newline="", encoding="utf-8-sig") as csv_file, jsonl_path.open(
        "w", encoding="utf-8", newline="\n"
    ) as jsonl_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for product in PRODUCTS:
            category = categories[product.category]
            counts[product.category] += 1
            nutrition = asdict(product.nutrition) if product.nutrition else None
            if nutrition is not None:
                nutrition["net_carbs_g"] = product.nutrition.net_carbs_g
            image_path = product.image_path or f"/images/products/{product.slug}.svg"
            variants = []
            for variant in product.variants:
                sku = variant.sku or make_sku(product.slug, variant.code)
                if sku in skus:
                    raise ValueError(f"Duplicate SKU: {sku}")
                skus.add(sku)
                price_cents = variant.price_cents or product.price_cents
                variants.append(
                    {
                        "sku": sku,
                        "code": variant.code,
                        "name": variant.name,
                        "attributes": variant.attributes,
                        "price_usd": dollars(price_cents),
                        "price_cents": price_cents,
                        "seed_stock_on_hand": variant.stock,
                        "seed_stock_reserved": 0,
                    }
                )
                row = {
                    "product_slug": product.slug,
                    "product_title": product.title,
                    "brand": product.brand,
                    "category_slug": category.slug,
                    "category_name": category.name,
                    "return_policy_class": category.policy_class.value,
                    "product_type": product.product_type,
                    "description": product.description,
                    "tags": "; ".join(product.tags),
                    "ingredients": product.ingredients or "",
                    "allergens": "; ".join(product.allergens),
                    "specs_json": compact_json(product.specs),
                    "image_path": image_path,
                    "base_price_usd": dollars(product.price_cents),
                    "variant_sku": sku,
                    "variant_code": variant.code,
                    "variant_name": variant.name,
                    "variant_attributes_json": compact_json(variant.attributes),
                    "variant_price_usd": dollars(price_cents),
                    "seed_stock_on_hand": variant.stock,
                    "seed_stock_reserved": 0,
                    "seed_stock_available": variant.stock,
                }
                row.update({f"variant_{key}": variant.attributes.get(key, "") for key in ATTRIBUTE_FIELDS})
                row.update({f"nutrition_{key}": (nutrition or {}).get(key, "") for key in NUTRITION_FIELDS})
                writer.writerow(row)
            jsonl_file.write(
                compact_json(
                    {
                        "slug": product.slug,
                        "title": product.title,
                        "brand": product.brand,
                        "category_slug": category.slug,
                        "category_name": category.name,
                        "return_policy_class": category.policy_class.value,
                        "product_type": product.product_type,
                        "description": product.description,
                        "tags": list(product.tags),
                        "nutrition": nutrition,
                        "ingredients": product.ingredients,
                        "allergens": list(product.allergens),
                        "specs": product.specs,
                        "image_path": image_path,
                        "base_price_usd": dollars(product.price_cents),
                        "base_price_cents": product.price_cents,
                        "variants": variants,
                    }
                ) + "\n"
            )

    summary = output / "README.md"
    summary.write_text(
        "# Product catalog report\n\n"
        "Source: `.claude/worktrees/catalog-stores/services/commerce/src/commerce/seed/` "
        "(`catalog.py`, `data.py`, and `gen/`). This is the full seed catalog in that worktree. "
        "The brands and products are demo data invented for this project.\n\n"
        f"- Products: **{len(PRODUCTS):,}**\n"
        f"- Purchasable variants / SKUs: **{len(skus):,}**\n"
        f"- Departments: **{len(categories)}**\n\n"
        "| Department | Products |\n|---|---:|\n"
        + "\n".join(f"| {category.name} | {counts[category.slug]:,} |" for category in CATEGORIES)
        + "\n\n"
        "## Files\n\n"
        "- `product_variants.csv`: one row per purchasable SKU, with product text, price, "
        "seed stock, options, nutrition, and specifications. UTF-8 with a BOM for Excel.\n"
        "- `products.jsonl`: one JSON object per product, preserving arrays and nested fields.\n\n"
        "Prices are in USD. Stock columns are **initial seed quantities**, not current inventory. "
        "The CSV has no database UUIDs, current reservations, order data, or review totals; "
        "those values are not part of the seed catalog. Empty nutrition, ingredients, and "
        "allergen fields mean the source does not provide those fields for that product. "
        "Specifications can be read in `specs_json`; variant attributes can be read in "
        "`variant_attributes_json` or their individual columns.\n\n"
        "Regenerate from the repository root with `python scripts/export_product_report.py`.\n",
        encoding="utf-8",
    )
    print(f"Exported {len(PRODUCTS)} products, {len(skus)} SKUs to {output}")


if __name__ == "__main__":
    main()
