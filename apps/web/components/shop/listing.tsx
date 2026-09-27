import { OpenStephButton } from "@/components/assistant/open-steph";
import {
  ChevronLeftIcon,
  ChevronRightIcon,
  CloseIcon,
  DepartmentIcon,
  SearchIcon,
  SlidersIcon,
} from "@/components/icons";
import { TopRatedStrip } from "@/components/product/top-rated-strip";
import { TypeChips } from "@/components/product/type-chips";
import { buttonClasses } from "@/components/ui/button";
import { inputClasses } from "@/components/ui/field";
import { Notice } from "@/components/ui/notice";
import { cn } from "@/lib/cn";
import type { CategoryOut, ProductPage, ProductSummary } from "@ai-commerce/contracts";
import Link from "next/link";
import { departmentTint } from "./department-style";
import { controlClasses, countPill, legendClasses, optionRow } from "@/components/product/filter-styles";
import { formatTotal } from "@/lib/listing-query";
import { FacetOptions, FilterForm, FilterPanel, FilterSheet, FilterTrigger } from "./filter-panel";
import { ProductGrid } from "./product-card";
import { SortSelect } from "./sort-select";

export type ListingParams = {
  q?: string;
  category?: string;
  brand?: string | string[];
  product_type?: string | string[];
  tag?: string | string[];
  min_price?: string;
  max_price?: string;
  in_stock?: string;
  sort?: string;
  page?: string;
};

const SORTS = [
  { value: "relevance", label: "Best match" },
  { value: "top_rated", label: "Top rated" },
  { value: "price_asc", label: "Price: low to high" },
  { value: "price_desc", label: "Price: high to low" },
  { value: "newest", label: "Newest" },
] as const;

const FORM_ID = "listing-filters";

/** Grocery departments: their tags are mostly dietary ("Organic", "Gluten-free"). */
const FOOD_DEPARTMENTS = new Set(["dairy-eggs", "produce", "meat-seafood", "bakery", "frozen", "pantry", "snacks", "beverages"]);

/** Popular searches offered when a search finds nothing. Each is known to match the catalog. */
const POPULAR_SEARCHES = ["milk", "bananas", "coffee", "bread", "chicken", "paper towels", "diapers", "dog food", "headphones", "yoga mat"];

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

/** "Diet & features" for food departments, "Features" everywhere else. */
export function tagLegend(categorySlug: string | undefined, items: Pick<ProductSummary, "category">[]): string {
  if (categorySlug) return FOOD_DEPARTMENTS.has(categorySlug) ? "Diet & features" : "Features";
  const food = items.filter((p) => FOOD_DEPARTMENTS.has(p.category.slug)).length;
  return items.length > 0 && food / items.length >= 0.5 ? "Diet & features" : "Features";
}

type Facet = ProductPage["facets"]["brands"][number];

export function hrefWith(basePath: string, params: ListingParams, changes: Partial<ListingParams>): string {
  const merged = { ...params, ...changes };
  const sp = new URLSearchParams();
  for (const [key, value] of Object.entries(merged)) {
    for (const v of asList(value as string | string[] | undefined)) if (v) sp.append(key, v);
  }
  const qs = sp.toString();
  return qs ? `${basePath}?${qs}` : basePath;
}

/** Page numbers to show: all when few, otherwise first, last and a window around the current. */
function pageWindow(current: number, count: number): (number | "gap")[] {
  if (count <= 7) return Array.from({ length: count }, (_, i) => i + 1);
  const pages = new Set([1, count, current - 1, current, current + 1]);
  const sorted = [...pages].filter((p) => p >= 1 && p <= count).sort((a, b) => a - b);
  const out: (number | "gap")[] = [];
  sorted.forEach((p, i) => {
    if (i > 0 && p - (sorted[i - 1] ?? p) > 1) out.push("gap");
    out.push(p);
  });
  return out;
}

export function Listing({
  page,
  params,
  basePath,
  heading,
  showCategoryFacet,
  category,
  departments = [],
  topRated = [],
}: {
  page: ProductPage;
  params: ListingParams;
  basePath: string;
  heading: string;
  showCategoryFacet: boolean;
  /** When set, the header becomes a department banner. */
  category?: { slug: string; name: string };
  /** Every department: for the empty state and the search breadcrumb. */
  departments?: CategoryOut[];
  /** "Top rated in <department>", shown on an unfiltered department landing. */
  topRated?: ProductSummary[];
}) {
  const brands = asList(params.brand);
  const types = asList(params.product_type);
  const tags = asList(params.tag);
  const pageCount = Math.max(1, Math.ceil(page.total / page.page_size));
  const current = page.page;
  const sort = SORTS.some((s) => s.value === params.sort) ? (params.sort as string) : "relevance";
  const categoryFacet = showCategoryFacet
    ? page.facets.categories.find((f) => f.value === params.category)
    : undefined;
  const activeCount =
    (params.category && showCategoryFacet ? 1 : 0) +
    brands.length +
    types.length +
    tags.length +
    (params.min_price ? 1 : 0) +
    (params.max_price ? 1 : 0) +
    (params.in_stock === "true" ? 1 : 0);
  // Everything but the filters: keep the query and sort when clearing.
  const clearHref = hrefWith(basePath, { q: params.q, sort: params.sort }, {});
  const first = page.total === 0 ? 0 : (current - 1) * page.page_size + 1;
  const last = Math.min(page.total, current * page.page_size);
  const query = hrefWith("", params, {}).replace(/^\?/, "");
  const showFilters = page.total > 0;
  // A search that stopped at its candidate limit knows only a lower bound: "400+".
  const totalLabel = formatTotal(page.total, page.search?.total_capped, last);
  const q = params.q?.trim();
  // Nothing matched the words themselves (e.g. "ipad" with no iPads): say the results are only related.
  const relatedOnly = !!q && page.items.length > 0 && page.search?.exact_match === false;

  const chips: { key: string; label: string; href: string }[] = [];
  const drop = (changes: Partial<ListingParams>) => hrefWith(basePath, params, { ...changes, page: undefined });
  if (categoryFacet) chips.push({ key: "category", label: categoryFacet.label, href: drop({ category: undefined }) });
  for (const b of brands) chips.push({ key: `b-${b}`, label: b, href: drop({ brand: brands.filter((x) => x !== b) }) });
  const labelOf = (facets: Facet[], value: string) => facets.find((f) => f.value === value)?.label ?? value;
  for (const t of types)
    chips.push({
      key: `t-${t}`,
      label: labelOf(page.facets.product_types, t),
      href: drop({ product_type: types.filter((x) => x !== t) }),
    });
  for (const t of tags)
    chips.push({ key: `g-${t}`, label: labelOf(page.facets.tags, t), href: drop({ tag: tags.filter((x) => x !== t) }) });
  if (params.min_price) chips.push({ key: "min", label: `From $${params.min_price}`, href: drop({ min_price: undefined }) });
  if (params.max_price) chips.push({ key: "max", label: `Up to $${params.max_price}`, href: drop({ max_price: undefined }) });
  if (params.in_stock === "true") chips.push({ key: "stock", label: "In stock only", href: drop({ in_stock: undefined }) });

  const searchCategory = !category && params.category ? departments.find((d) => d.slug === params.category) : undefined;

  return (
    <div>
      {category ? (
        <CategoryBanner
          category={category}
          total={page.total}
          images={[...new Set(page.items.map((p) => p.image_path))].slice(0, 3)}
          typeChips={page.facets.product_types.map((f) => {
            const isCurrent = types.length === 1 && types[0] === f.value;
            return {
              value: f.value,
              label: f.label,
              // Counts only describe the unfiltered department.
              count: activeCount === 0 ? f.count : undefined,
              href: isCurrent ? basePath : `${basePath}?product_type=${encodeURIComponent(f.value)}`,
              current: isCurrent,
            };
          })}
        />
      ) : (
        <SearchHeader
          heading={heading}
          total={page.total}
          totalLabel={totalLabel}
          relatedOnly={relatedOnly}
          query={q}
          department={searchCategory ? { slug: searchCategory.slug, name: searchCategory.name } : undefined}
        />
      )}

      {/* On phones the strip would push the products below the fold; "Top rated" is a sort there. */}
      {category && topRated.length > 0 ? (
        <div className="max-sm:hidden">
          <TopRatedStrip department={category.name} items={topRated} />
        </div>
      ) : null}

      <FilterSheet>
        <div
          className={cn(
            "mt-4 sm:mt-8 lg:mt-10",
            showFilters && "lg:grid lg:grid-cols-[16.5rem_minmax(0,1fr)] lg:items-start lg:gap-10",
          )}
        >
          {showFilters ? (
            <aside aria-labelledby="filters-heading" className="lg:sticky lg:top-36">
              <h2 id="filters-heading" className="sr-only">
                Filters
              </h2>
              <FilterPanel total={page.total} totalLabel={totalLabel}>
                <FilterForm
                  id={FORM_ID}
                  action={basePath}
                  query={query}
                  defaults={{ sort: "relevance" }}
                  className="rounded-3xl border border-line bg-raised p-2 shadow-xs lg:max-h-[calc(100vh-10.5rem)] lg:overflow-y-auto"
                >
                  <div className="hidden items-center gap-2 px-3 pb-1 pt-3 lg:flex">
                    <SlidersIcon className="size-4.5 text-brand-600" />
                    <p aria-hidden="true" className="font-display text-lg font-semibold text-ink">
                      Filters
                    </p>
                    {activeCount > 0 ? (
                      <Link
                        href={clearHref}
                        scroll={false}
                        className="-mr-1 ml-auto inline-flex min-h-11 items-center rounded-full px-2 text-sm font-semibold text-brand-700 hover:text-brand-900"
                      >
                        Clear all
                      </Link>
                    ) : null}
                  </div>
                  {params.q ? <input type="hidden" name="q" value={params.q} /> : null}
                  <div className="divide-y divide-line lg:mt-2 lg:border-t lg:border-line">
                    {showCategoryFacet && page.facets.categories.length > 0 ? (
                      <fieldset className="px-1 py-4">
                        <legend className={cn(legendClasses, "px-2")}>Department</legend>
                        <div className="clear-both space-y-0.5 pt-2">
                          <label className={optionRow}>
                            <input
                              type="radio"
                              name="category"
                              value=""
                              defaultChecked={!params.category}
                              className={controlClasses}
                            />
                            All departments
                          </label>
                          {page.facets.categories.map((f) => (
                            <label key={f.value} className={optionRow}>
                              <input
                                type="radio"
                                name="category"
                                value={f.value}
                                defaultChecked={params.category === f.value}
                                className={controlClasses}
                              />
                              <span className="min-w-0 truncate">{f.label}</span>
                              <span className={countPill}>
                                <span className="sr-only">(</span>
                                {f.count}
                                <span className="sr-only">)</span>
                              </span>
                            </label>
                          ))}
                        </div>
                      </fieldset>
                    ) : null}
                    <FacetOptions legend="Type" noun="type" name="product_type" facets={page.facets.product_types} selected={types} />
                    <FacetOptions
                      legend={tagLegend(category?.slug ?? params.category, page.items)}
                      noun="feature"
                      name="tag"
                      facets={page.facets.tags}
                      selected={tags}
                    />
                    <FacetOptions legend="Brand" noun="brand" name="brand" facets={page.facets.brands} selected={brands} />
                    <fieldset className="px-3 py-4">
                      <legend className={legendClasses}>Price</legend>
                      <div className="clear-both flex items-center gap-2 pt-3">
                        <PriceInput id="min_price" label="Minimum price in dollars" placeholder="Min" value={params.min_price} />
                        <span aria-hidden="true" className="text-muted">
                          –
                        </span>
                        <PriceInput id="max_price" label="Maximum price in dollars" placeholder="Max" value={params.max_price} />
                        {/* Submits the whole form; checkboxes apply on their own. */}
                        <button type="submit" className={buttonClasses("outline", "md", "shrink-0 px-3.5")}>
                          Apply<span className="sr-only"> filters</span>
                        </button>
                      </div>
                    </fieldset>
                    <fieldset className="px-1 py-4">
                      <legend className={cn(legendClasses, "px-2")}>Availability</legend>
                      <div className="clear-both pt-2">
                        <label className={optionRow}>
                          <input
                            type="checkbox"
                            name="in_stock"
                            value="true"
                            defaultChecked={params.in_stock === "true"}
                            className={cn(controlClasses, "rounded")}
                          />
                          In stock only
                        </label>
                      </div>
                    </fieldset>
                  </div>
                </FilterForm>
              </FilterPanel>
            </aside>
          ) : null}

          <section
            aria-labelledby="results-heading"
            className="transition-opacity duration-200 [:root:has(#listing-filters[data-pending])_&]:opacity-60"
          >
            {page.total > 0 ? (
              // One toolbar: on phones the Filters button sits here with the count (shown once) and sort.
              <div className="flex flex-wrap items-center justify-between gap-x-2 gap-y-2 border-b border-line pb-3 sm:gap-x-4 sm:pb-4">
                <div className="flex min-w-0 items-center gap-2.5 sm:gap-3">
                  {showFilters ? <FilterTrigger activeCount={activeCount} /> : null}
                  <p className="text-sm text-muted" role="status">
                    <span className="hidden sm:inline">
                      Showing <span className="font-semibold tabular-nums text-ink">{first}–{last}</span> of{" "}
                    </span>
                    <span className="font-semibold tabular-nums text-ink">{totalLabel}</span>{" "}
                    {page.total === 1 ? "result" : "results"}
                  </p>
                </div>
                <div className="max-sm:[&_label]:sr-only max-sm:[&_select]:max-w-38">
                  <SortSelect
                    formId={FORM_ID}
                    defaultValue={sort}
                    options={SORTS.map((s) => ({
                      value: s.value,
                      label: s.value === "relevance" && !params.q ? "Featured" : s.label,
                    }))}
                  />
                </div>
              </div>
            ) : (
              <p className="sr-only" role="status">
                0 results
              </p>
            )}
            {chips.length > 0 ? (
              <div className="mt-4 flex flex-wrap items-center gap-2">
                <ul aria-label="Active filters" className="contents">
                  {chips.map((chip) => (
                    <li key={chip.key}>
                      <Link
                        href={chip.href}
                        scroll={false}
                        className="relative inline-flex h-9 items-center gap-1.5 rounded-full bg-brand-50 pl-3.5 pr-2.5 text-sm font-medium text-brand-800 ring-1 ring-inset ring-brand-100 transition-colors duration-150 before:absolute before:inset-x-0 before:-inset-y-1 before:content-[''] hover:bg-brand-100"
                      >
                        <span className="sr-only">Remove filter: </span>
                        {chip.label}
                        <CloseIcon className="size-4 text-brand-600" />
                      </Link>
                    </li>
                  ))}
                </ul>
                {chips.length > 1 ? (
                  <Link
                    href={clearHref}
                    scroll={false}
                    className="inline-flex min-h-9 items-center rounded-full px-2.5 text-sm font-semibold text-brand-700 underline decoration-brand-300 underline-offset-4 hover:text-brand-900 hover:decoration-brand-700"
                  >
                    Clear all<span className="sr-only"> filters</span>
                  </Link>
                ) : null}
              </div>
            ) : null}
            {page.search?.notice ? (
              <Notice tone="warning" className="mt-4">
                {page.search.notice}
              </Notice>
            ) : null}
            {relatedOnly ? (
              <Notice tone="info" role="note" className="mt-4" title={`No exact matches for “${q}”`}>
                Showing related items instead. Try another word, or ask Steph to search the whole store for you.
              </Notice>
            ) : null}
            {page.items.length === 0 ? (
              <EmptyState
                clearHref={clearHref}
                hasFilters={activeCount > 0}
                query={params.q?.trim()}
                departments={departments}
                inDepartment={category?.name}
              />
            ) : (
              <div className="mt-4 sm:mt-8">
                <ProductGrid products={page.items} label={heading} />
              </div>
            )}
            {pageCount > 1 ? (
              <nav aria-label="Pagination" className="mt-14 flex items-center justify-center gap-1.5 sm:gap-2">
                {current > 1 ? (
                  <Link
                    className={buttonClasses("outline", "md", "px-3 sm:px-4")}
                    href={hrefWith(basePath, params, { page: String(current - 1) })}
                    rel="prev"
                  >
                    <ChevronLeftIcon className="size-4" />
                    <span className="max-sm:sr-only">Previous</span>
                    <span className="sr-only"> page</span>
                  </Link>
                ) : null}
                <ol className="flex items-center gap-1">
                  {pageWindow(current, pageCount).map((p, i) =>
                    p === "gap" ? (
                      <li key={`gap-${i}`} aria-hidden="true" className="w-6 text-center text-muted">
                        …
                      </li>
                    ) : (
                      <li key={p}>
                        <Link
                          href={hrefWith(basePath, params, { page: String(p) })}
                          aria-current={p === current ? "page" : undefined}
                          className="grid size-11 place-items-center rounded-full text-sm font-semibold tabular-nums text-ink-soft transition-colors duration-150 hover:bg-sunken hover:text-ink aria-[current=page]:bg-ink aria-[current=page]:text-white aria-[current=page]:shadow-sm"
                        >
                          <span className="sr-only">Page </span>
                          {p}
                        </Link>
                      </li>
                    ),
                  )}
                </ol>
                {current < pageCount ? (
                  <Link
                    className={buttonClasses("outline", "md", "px-3 sm:px-4")}
                    href={hrefWith(basePath, params, { page: String(current + 1) })}
                    rel="next"
                  >
                    <span className="max-sm:sr-only">Next</span>
                    <span className="sr-only"> page</span>
                    <ChevronRightIcon className="size-4" />
                  </Link>
                ) : null}
              </nav>
            ) : null}
            {pageCount > 1 ? (
              <p className="mt-3 text-center text-xs text-muted">
                Page {current} of {pageCount}
              </p>
            ) : null}
          </section>
        </div>
      </FilterSheet>
    </div>
  );
}

function PriceInput({ id, label, placeholder, value }: { id: string; label: string; placeholder: string; value?: string }) {
  return (
    <div className="relative min-w-0 flex-1">
      <label className="sr-only" htmlFor={id}>
        {label}
      </label>
      <span aria-hidden="true" className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm text-muted">
        $
      </span>
      <input
        id={id}
        name={id}
        inputMode="decimal"
        placeholder={placeholder}
        defaultValue={value}
        className={cn(inputClasses, "min-h-11 pl-7 pr-2 text-sm")}
      />
    </div>
  );
}

function Breadcrumbs({ items }: { items: { label: string; href?: string }[] }) {
  return (
    <nav aria-label="Breadcrumb">
      <ol className="flex flex-wrap items-center gap-1 text-sm text-muted">
        {items.map((item, i) => (
          <li key={item.label} className="flex items-center gap-1">
            {i > 0 ? <ChevronRightIcon className="size-3.5 text-muted" /> : null}
            {item.href ? (
              <Link href={item.href} className="inline-flex min-h-8 items-center rounded-md hover:text-ink hover:underline hover:underline-offset-4">
                {item.label}
              </Link>
            ) : (
              <span aria-current="page" className="font-medium text-ink">
                {item.label}
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}

function CategoryBanner({
  category,
  total,
  images,
  typeChips,
}: {
  category: { slug: string; name: string };
  total: number;
  images: string[];
  typeChips: Parameters<typeof TypeChips>[0]["chips"];
}) {
  const tint = departmentTint(category.slug);
  return (
    <header
      className={cn(
        "relative isolate overflow-hidden rounded-2xl px-4 py-4 sm:rounded-4xl sm:px-10 sm:py-10",
        tint.surface,
      )}
    >
      {/* hairline edge drawn on top, so the glow layers below can't cover it */}
      <div
        aria-hidden="true"
        className={cn("pointer-events-none absolute inset-0 z-20 rounded-[inherit] ring-1 ring-inset", tint.ring)}
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-10 top-1/2 -z-10 size-120 -translate-y-1/2 rounded-full bg-white/70 blur-3xl"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(rgb(24_24_35/0.07)_1px,transparent_1px)] bg-size-[20px_20px] mask-[linear-gradient(to_right,black,transparent_60%)]"
      />
      <div className="relative z-10 md:max-w-[calc(100%-22rem)] lg:max-w-[calc(100%-28rem)]">
        {/* Phones: the department rail above already says where you are. */}
        <div className="max-sm:hidden">
          <Breadcrumbs items={[{ label: "Home", href: "/" }, { label: category.name }]} />
        </div>
        <div className="flex items-center gap-3 sm:mt-5 sm:gap-4">
          <span
            className={cn(
              "grid size-11 shrink-0 place-items-center rounded-xl shadow-sm ring-1 ring-black/5 sm:size-14 sm:rounded-2xl",
              tint.tile,
            )}
          >
            <DepartmentIcon slug={category.slug} className="size-6 sm:size-7" />
          </span>
          <div>
            <p className={cn("text-xs font-semibold uppercase tracking-eyebrow", tint.text)}>
              Department
              {/* The results toolbar shows the count on phones; say it once. */}
              <span className="max-sm:hidden">
                <span aria-hidden="true"> · </span>
                <span className="sr-only">, </span>
                <span className="tabular-nums">
                  {total.toLocaleString("en-US")} {total === 1 ? "product" : "products"}
                </span>
              </span>
            </p>
            <h1 id="results-heading" className="font-display text-2xl font-semibold text-ink sm:mt-1 sm:text-5xl">
              {category.name}
            </h1>
          </div>
        </div>
        <TypeChips chips={typeChips} className="mt-3 sm:mt-6" />
      </div>
      {images.length > 0 ? (
        <div aria-hidden="true" className="absolute inset-y-0 right-4 hidden w-92 md:block lg:right-12 lg:w-104">
          {images.map((src, i) => (
            // eslint-disable-next-line @next/next/no-img-element -- local SVG illustrations
            <img
              key={src}
              src={src}
              alt=""
              width={640}
              height={640}
              className={cn(
                "absolute rounded-3xl shadow-lg ring-4 ring-white/80 animate-fade-up",
                i === 0 && "left-2 top-1/2 w-36 -translate-y-1/2 -rotate-8 animation-delay-80",
                i === 1 && "left-1/2 top-1/2 z-10 w-44 -translate-x-1/2 -translate-y-1/2 shadow-xl animation-delay-160",
                i === 2 && "right-2 top-1/2 w-36 -translate-y-1/2 rotate-8 animation-delay-240",
              )}
            />
          ))}
        </div>
      ) : null}
    </header>
  );
}

function SearchHeader({
  heading,
  total,
  totalLabel,
  relatedOnly = false,
  query,
  department,
}: {
  heading: string;
  total: number;
  /** "324", or "400+" when the search stopped at its candidate limit. */
  totalLabel: string;
  /** Nothing matched the query's words; the results are related items. */
  relatedOnly?: boolean;
  query?: string;
  department?: { slug: string; name: string };
}) {
  const where = department ? `in ${department.name}` : "across every department";
  const noun = relatedOnly ? (total === 1 ? "related item" : "related items") : total === 1 ? "match" : "matches";
  const crumbs: { label: string; href?: string }[] = [{ label: "Home", href: "/" }];
  if (department) crumbs.push({ label: department.name, href: `/c/${department.slug}` });
  crumbs.push({ label: query ? "Search" : "All products" });
  return (
    <header className="relative isolate overflow-hidden rounded-2xl bg-mesh-light px-5 py-5 sm:rounded-4xl sm:px-10 sm:py-12">
      <Breadcrumbs items={crumbs} />
      <p className="mt-3 text-xs font-semibold uppercase tracking-eyebrow text-brand-700 sm:mt-6">
        {query ? "Search results" : "The whole store"}
      </p>
      <h1 id="results-heading" className="mt-2 max-w-3xl font-display text-2xl font-semibold text-ink sm:text-5xl">
        {heading}
      </h1>
      <p className="mt-2 text-base text-muted sm:mt-4">
        {query
          ? total === 0
            ? department
              ? `Nothing matched in ${department.name}.`
              : "Nothing matched that search."
            : `${totalLabel} ${noun} ${where}.`
          : `Browse all ${totalLabel} products, or narrow things down with the filters.`}
      </p>
    </header>
  );
}

function EmptyState({
  clearHref,
  hasFilters,
  query,
  departments,
  inDepartment,
}: {
  clearHref: string;
  hasFilters: boolean;
  query?: string;
  departments: CategoryOut[];
  inDepartment?: string;
}) {
  return (
    <div className="mt-6">
      <div className="flex flex-col items-center rounded-3xl border border-dashed border-line-strong bg-raised px-6 py-12 text-center sm:py-14">
        <span className="relative grid size-16 place-items-center rounded-2xl bg-brand-50 text-brand-600 shadow-sm ring-1 ring-inset ring-brand-100">
          <SearchIcon className="size-8" />
          <span className="absolute -right-1.5 -top-1.5 grid size-6 place-items-center rounded-full bg-accent-400 text-xs font-bold text-ink shadow-sm">
            ?
          </span>
        </span>
        <h2 className="mt-6 font-display text-2xl font-semibold text-ink">
          {hasFilters ? "No products match these filters" : query ? `No results for “${query}”` : "No products here yet"}
        </h2>
        <p className="mt-2 max-w-md text-muted">
          {hasFilters
            ? "Remove a filter or two to see more."
            : "Check the spelling, try a more general word, or ask Steph. She can search the whole store for you."}
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          {hasFilters ? (
            <Link href={clearHref} scroll={false} className={buttonClasses("primary", "md")}>
              Clear filters
            </Link>
          ) : null}
          {query || !inDepartment ? (
            <OpenStephButton prompt={query} variant={hasFilters ? "outline" : "primary"} />
          ) : null}
        </div>
      </div>

      {!hasFilters ? (
        <section aria-labelledby="popular-searches" className="mt-10">
          <h2 id="popular-searches" className="font-display text-xl font-semibold text-ink">
            Popular searches
          </h2>
          <ul className="mt-3 flex flex-wrap gap-2">
            {POPULAR_SEARCHES.map((term) => (
              <li key={term}>
                <Link
                  href={`/search?q=${encodeURIComponent(term)}`}
                  className="inline-flex min-h-10 items-center gap-2 rounded-full bg-raised px-4 text-sm font-medium text-ink shadow-xs ring-1 ring-inset ring-line-strong transition-colors hover:bg-brand-50 hover:text-brand-800 hover:ring-brand-200"
                >
                  <SearchIcon className="size-4 text-muted" />
                  {term}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {departments.length > 0 ? (
        <section aria-labelledby="shop-departments" className="mt-10">
          <h2 id="shop-departments" className="font-display text-xl font-semibold text-ink">
            {inDepartment ? "Shop another department" : "Shop by department"}
          </h2>
          <ul className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            {departments.map((d) => {
              const tint = departmentTint(d.slug);
              return (
                <li key={d.slug}>
                  <Link
                    href={`/c/${d.slug}`}
                    className="flex min-h-14 items-center gap-3 rounded-2xl border border-line bg-raised p-2.5 text-sm font-semibold text-ink shadow-xs transition-[border-color,box-shadow] hover:border-line-strong hover:shadow-md"
                  >
                    <span className={cn("grid size-10 shrink-0 place-items-center rounded-xl", tint.tile)}>
                      <DepartmentIcon slug={d.slug} className="size-5" />
                    </span>
                    <span className="min-w-0">{d.name}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
