import type { ListingParams } from "@/components/shop/listing";
import { asList, dollarsToMinor } from "@/components/shop/listing";
import type { SortOrder } from "@ai-commerce/contracts";

const SORTS: SortOrder[] = ["relevance", "price_asc", "price_desc", "newest", "top_rated"];
const SLUG = /^[a-z0-9]+(-[a-z0-9]+)*$/;

/** Kebab-case slugs only (tags, product types), at most 10. */
function slugs(value: string | string[] | undefined): string[] {
  return asList(value).filter((v) => SLUG.test(v)).slice(0, 10);
}

/** Turn page search params into the typed API query. Invalid values are dropped. */
export function toProductQuery(params: ListingParams, fixedCategory?: string) {
  const page = Number(params.page);
  const sort = SORTS.includes(params.sort as SortOrder) ? (params.sort as SortOrder) : undefined;
  return {
    q: params.q?.trim() || undefined,
    category: fixedCategory ?? (params.category || undefined),
    brand: asList(params.brand).filter(Boolean),
    product_type: slugs(params.product_type),
    tag: slugs(params.tag),
    min_price: dollarsToMinor(params.min_price),
    max_price: dollarsToMinor(params.max_price),
    in_stock: params.in_stock === "true" ? true : undefined,
    sort,
    page: Number.isInteger(page) && page > 0 && page <= 1000 ? page : 1,
    page_size: 24,
  };
}

/**
 * True for a department's plain landing view: no filters, no search, first page, default sort.
 * That's where extras such as the "Top rated" strip belong; once the shopper narrows things
 * down they'd only push the results further away.
 */
export function isLandingView(params: ListingParams): boolean {
  const filtered =
    !!params.q?.trim() ||
    asList(params.brand).some(Boolean) ||
    asList(params.product_type).some(Boolean) ||
    asList(params.tag).some(Boolean) ||
    !!params.min_price ||
    !!params.max_price ||
    params.in_stock === "true";
  const page = Number(params.page || "1");
  const sorted = !!params.sort && params.sort !== "relevance";
  return !filtered && !sorted && !(page > 1);
}

/**
 * A result count as shoppers read it: "1,284", or a round lower bound such as "350+" when
 * search stopped collecting candidates at its limit (the API's `search.total_capped`). The
 * capped figure is wherever collection stopped ("397"), so it's rounded down, never up, to a
 * step that reads as an estimate: 50s under 1,000, 100s above (small counts stay exact). Pass
 * `shownThrough` (the last result number on screen) so a late page never reads "385–397 of 350+".
 */
export function formatTotal(total: number, capped = false, shownThrough = 0): string {
  if (!capped || total <= 0) return total.toLocaleString("en-US");
  const step = total >= 1000 ? 100 : total >= 100 ? 50 : 1;
  const rounded = Math.floor(total / step) * step;
  return `${(rounded < shownThrough ? total : rounded).toLocaleString("en-US")}+`;
}
