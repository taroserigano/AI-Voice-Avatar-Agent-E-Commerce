import type { ListingParams } from "@/components/shop/listing";
import { asList, dollarsToMinor } from "@/components/shop/listing";

type SortOrder = "relevance" | "price_asc" | "price_desc" | "newest";
const SORTS: SortOrder[] = ["relevance", "price_asc", "price_desc", "newest"];

/** Turn page search params into the typed API query. Invalid values are dropped. */
export function toProductQuery(params: ListingParams, fixedCategory?: string) {
  const page = Number(params.page);
  const sort = SORTS.includes(params.sort as SortOrder) ? (params.sort as SortOrder) : undefined;
  return {
    q: params.q?.trim() || undefined,
    category: fixedCategory ?? (params.category || undefined),
    brand: asList(params.brand).filter(Boolean),
    min_price: dollarsToMinor(params.min_price),
    max_price: dollarsToMinor(params.max_price),
    in_stock: params.in_stock === "true" ? true : undefined,
    sort,
    page: Number.isInteger(page) && page > 0 && page <= 1000 ? page : 1,
    page_size: 24,
  };
}
