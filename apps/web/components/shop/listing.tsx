import { buttonClasses } from "@/components/ui/button";
import { Notice } from "@/components/ui/notice";
import type { ProductPage } from "@ai-commerce/contracts";
import Link from "next/link";
import { FilterPanel } from "./filter-panel";
import { ProductGrid } from "./product-card";

export type ListingParams = {
  q?: string;
  category?: string;
  brand?: string | string[];
  min_price?: string;
  max_price?: string;
  in_stock?: string;
  sort?: string;
  page?: string;
};

const SORTS = [
  { value: "relevance", label: "Best match" },
  { value: "price_asc", label: "Price: low to high" },
  { value: "price_desc", label: "Price: high to low" },
  { value: "newest", label: "Newest" },
] as const;

export function asList(value: string | string[] | undefined): string[] {
  if (value === undefined) return [];
  return Array.isArray(value) ? value : [value];
}

/** Dollars typed by the shopper -> integer cents for the API (no float money math). */
export function dollarsToMinor(value: string | undefined): number | undefined {
  if (!value) return undefined;
  const match = /^\s*(\d{1,6})(?:\.(\d{1,2}))?\s*$/.exec(value);
  if (!match) return undefined;
  return Number(match[1]) * 100 + Number((match[2] ?? "").padEnd(2, "0") || 0);
}

function hrefWith(basePath: string, params: ListingParams, changes: Partial<ListingParams>): string {
  const merged = { ...params, ...changes };
  const sp = new URLSearchParams();
  for (const [key, value] of Object.entries(merged)) {
    for (const v of asList(value as string | string[] | undefined)) if (v) sp.append(key, v);
  }
  const qs = sp.toString();
  return qs ? `${basePath}?${qs}` : basePath;
}

export function Listing({
  page,
  params,
  basePath,
  heading,
  showCategoryFacet,
}: {
  page: ProductPage;
  params: ListingParams;
  basePath: string;
  heading: string;
  showCategoryFacet: boolean;
}) {
  const brands = asList(params.brand);
  const pageCount = Math.max(1, Math.ceil(page.total / page.page_size));
  const current = page.page;
  const sort = SORTS.some((s) => s.value === params.sort) ? params.sort : "relevance";
  const activeCount =
    (params.category && showCategoryFacet ? 1 : 0) +
    brands.length +
    (params.min_price ? 1 : 0) +
    (params.max_price ? 1 : 0) +
    (params.in_stock === "true" ? 1 : 0);

  return (
    <div className="grid gap-6 lg:grid-cols-[16rem_1fr]">
      <aside aria-labelledby="filters-heading">
        <h2 id="filters-heading" className="sr-only lg:not-sr-only lg:text-lg lg:font-bold">
          Filters
        </h2>
        <FilterPanel activeCount={activeCount}>
        <form method="get" action={basePath} className="space-y-5 lg:mt-3">
          {params.q ? <input type="hidden" name="q" value={params.q} /> : null}
          {showCategoryFacet && page.facets.categories.length > 0 ? (
            <fieldset>
              <legend className="font-semibold">Department</legend>
              <div className="mt-2 space-y-1">
                <label className="flex min-h-8 items-center gap-2">
                  <input type="radio" name="category" value="" defaultChecked={!params.category} className="h-4 w-4" />
                  All
                </label>
                {page.facets.categories.map((f) => (
                  <label key={f.value} className="flex min-h-8 items-center gap-2">
                    <input
                      type="radio"
                      name="category"
                      value={f.value}
                      defaultChecked={params.category === f.value}
                      className="h-4 w-4"
                    />
                    <span>
                      {f.label} <span className="text-muted">({f.count})</span>
                    </span>
                  </label>
                ))}
              </div>
            </fieldset>
          ) : null}
          {page.facets.brands.length > 0 ? (
            <fieldset>
              <legend className="font-semibold">Brand</legend>
              <div className="mt-2 max-h-60 space-y-1 overflow-y-auto">
                {page.facets.brands.map((f) => (
                  <label key={f.value} className="flex min-h-8 items-center gap-2">
                    <input
                      type="checkbox"
                      name="brand"
                      value={f.value}
                      defaultChecked={brands.includes(f.value)}
                      className="h-4 w-4"
                    />
                    <span>
                      {f.label} <span className="text-muted">({f.count})</span>
                    </span>
                  </label>
                ))}
              </div>
            </fieldset>
          ) : null}
          <fieldset>
            <legend className="font-semibold">Price</legend>
            <div className="mt-2 flex items-center gap-2">
              <label className="sr-only" htmlFor="min_price">
                Minimum price in dollars
              </label>
              <input
                id="min_price"
                name="min_price"
                inputMode="decimal"
                placeholder="$ min"
                defaultValue={params.min_price}
                className="min-h-10 w-24 rounded-lg border border-stone-400 px-2"
              />
              <span aria-hidden="true">–</span>
              <label className="sr-only" htmlFor="max_price">
                Maximum price in dollars
              </label>
              <input
                id="max_price"
                name="max_price"
                inputMode="decimal"
                placeholder="$ max"
                defaultValue={params.max_price}
                className="min-h-10 w-24 rounded-lg border border-stone-400 px-2"
              />
            </div>
          </fieldset>
          <label className="flex min-h-8 items-center gap-2">
            <input type="checkbox" name="in_stock" value="true" defaultChecked={params.in_stock === "true"} className="h-4 w-4" />
            In stock only
          </label>
          <div>
            <label htmlFor="sort" className="font-semibold">
              Sort by
            </label>
            <select
              id="sort"
              name="sort"
              defaultValue={sort}
              className="mt-2 block min-h-10 w-full rounded-lg border border-stone-400 bg-white px-2"
            >
              {SORTS.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.value === "relevance" && !params.q ? "Featured" : s.label}
                </option>
              ))}
            </select>
          </div>
          <button type="submit" className={buttonClasses("secondary", "md", "w-full")}>
            Apply filters
          </button>
        </form>
        </FilterPanel>
      </aside>

      <section aria-labelledby="results-heading">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h1 id="results-heading" className="text-2xl font-bold">
            {heading}
          </h1>
          <p className="text-sm text-muted" role="status">
            {page.total} {page.total === 1 ? "result" : "results"}
          </p>
        </div>
        {page.search?.notice ? (
          <Notice tone="warning" className="mt-3">
            {page.search.notice}
          </Notice>
        ) : null}
        {page.items.length === 0 ? (
          <div className="mt-8 rounded-2xl border border-dashed border-stone-300 bg-white p-10 text-center">
            <p className="text-lg font-semibold">No products match.</p>
            <p className="mt-1 text-muted">Try different words, or remove a filter.</p>
            <Link href={basePath === "/search" ? "/search" : basePath} className={buttonClasses("secondary", "md", "mt-4")}>
              Clear filters
            </Link>
          </div>
        ) : (
          <div className="mt-4">
            <ProductGrid products={page.items} label={heading} />
          </div>
        )}
        {pageCount > 1 ? (
          <nav aria-label="Pagination" className="mt-8 flex items-center justify-center gap-2">
            {current > 1 ? (
              <Link className={buttonClasses("secondary", "sm")} href={hrefWith(basePath, params, { page: String(current - 1) })}>
                Previous
              </Link>
            ) : null}
            <span className="px-3 text-sm" aria-current="page">
              Page {current} of {pageCount}
            </span>
            {current < pageCount ? (
              <Link className={buttonClasses("secondary", "sm")} href={hrefWith(basePath, params, { page: String(current + 1) })}>
                Next
              </Link>
            ) : null}
          </nav>
        ) : null}
      </section>
    </div>
  );
}
