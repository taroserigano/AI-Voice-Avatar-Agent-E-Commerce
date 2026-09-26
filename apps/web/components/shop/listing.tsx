import {
  ChevronLeftIcon,
  ChevronRightIcon,
  CloseIcon,
  DepartmentIcon,
  SearchIcon,
  SlidersIcon,
} from "@/components/icons";
import { buttonClasses } from "@/components/ui/button";
import { inputClasses } from "@/components/ui/field";
import { Notice } from "@/components/ui/notice";
import { cn } from "@/lib/cn";
import type { ProductPage } from "@ai-commerce/contracts";
import Link from "next/link";
import { departmentTint } from "./department-style";
import { FilterPanel } from "./filter-panel";
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

type Facet = ProductPage["facets"]["brands"][number];

/** A checkbox group for a facet; checked values are submitted as repeated query params. */
function CheckboxFacet({ legend, name, facets, selected }: { legend: string; name: string; facets: Facet[]; selected: string[] }) {
  if (facets.length === 0) return null;
  return (
    <fieldset className="px-1 py-4">
      <legend className={cn(legendClasses, "px-2")}>{legend}</legend>
      <div className="clear-both max-h-64 space-y-0.5 overflow-y-auto pt-2">
        {facets.map((f) => (
          <label key={f.value} className={optionRow}>
            <input
              type="checkbox"
              name={name}
              value={f.value}
              defaultChecked={selected.includes(f.value)}
              className={cn(controlClasses, "rounded")}
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
  );
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

const legendClasses = "float-left w-full text-xs font-semibold uppercase tracking-eyebrow text-muted";
const optionRow =
  "flex min-h-10 cursor-pointer items-center gap-3 rounded-lg px-2 text-sm text-ink-soft transition-colors duration-150 hover:bg-sunken hover:text-ink has-[:checked]:font-semibold has-[:checked]:text-ink";
const countPill = "ml-auto rounded-full bg-sunken px-2 py-0.5 text-xs tabular-nums text-muted";
const controlClasses = "size-4.5 shrink-0 accent-brand-600";

export function Listing({
  page,
  params,
  basePath,
  heading,
  showCategoryFacet,
  category,
}: {
  page: ProductPage;
  params: ListingParams;
  basePath: string;
  heading: string;
  showCategoryFacet: boolean;
  /** When set, the header becomes a department banner. */
  category?: { slug: string; name: string };
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

  const chips: { label: string; href: string }[] = [];
  if (categoryFacet) chips.push({ label: categoryFacet.label, href: hrefWith(basePath, params, { category: undefined, page: undefined }) });
  for (const b of brands)
    chips.push({ label: b, href: hrefWith(basePath, params, { brand: brands.filter((x) => x !== b), page: undefined }) });
  const labelOf = (facets: Facet[], value: string) => facets.find((f) => f.value === value)?.label ?? value;
  for (const t of types)
    chips.push({
      label: labelOf(page.facets.product_types, t),
      href: hrefWith(basePath, params, { product_type: types.filter((x) => x !== t), page: undefined }),
    });
  for (const t of tags)
    chips.push({
      label: labelOf(page.facets.tags, t),
      href: hrefWith(basePath, params, { tag: tags.filter((x) => x !== t), page: undefined }),
    });
  if (params.min_price) chips.push({ label: `From $${params.min_price}`, href: hrefWith(basePath, params, { min_price: undefined, page: undefined }) });
  if (params.max_price) chips.push({ label: `Up to $${params.max_price}`, href: hrefWith(basePath, params, { max_price: undefined, page: undefined }) });
  if (params.in_stock === "true") chips.push({ label: "In stock only", href: hrefWith(basePath, params, { in_stock: undefined, page: undefined }) });

  return (
    <div>
      {category ? (
        <CategoryBanner category={category} total={page.total} images={[...new Set(page.items.map((p) => p.image_path))].slice(0, 3)} />
      ) : (
        <SearchHeader heading={heading} total={page.total} query={params.q?.trim()} />
      )}

      <div className="mt-8 sm:mt-10 lg:grid lg:grid-cols-[16.5rem_minmax(0,1fr)] lg:items-start lg:gap-10">
        <aside aria-labelledby="filters-heading" className="lg:sticky lg:top-36">
          <h2 id="filters-heading" className="sr-only">
            Filters
          </h2>
          <FilterPanel activeCount={activeCount}>
            <form
              id={FORM_ID}
              method="get"
              action={basePath}
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
                <CheckboxFacet legend="Type" name="product_type" facets={page.facets.product_types} selected={types} />
                <CheckboxFacet legend="Diet & features" name="tag" facets={page.facets.tags} selected={tags} />
                <CheckboxFacet legend="Brand" name="brand" facets={page.facets.brands} selected={brands} />
                <fieldset className="px-3 py-4">
                  <legend className={cn(legendClasses)}>Price</legend>
                  <div className="clear-both flex items-center gap-2 pt-3">
                    <PriceInput id="min_price" label="Minimum price in dollars" placeholder="Min" value={params.min_price} />
                    <span aria-hidden="true" className="text-muted">
                      –
                    </span>
                    <PriceInput id="max_price" label="Maximum price in dollars" placeholder="Max" value={params.max_price} />
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
              <div className="flex flex-col gap-1 p-2 pt-3">
                <button type="submit" className={buttonClasses("primary", "md", "w-full")}>
                  Apply filters
                </button>
                {activeCount > 0 ? (
                  <Link href={clearHref} className={buttonClasses("ghost", "md", "w-full text-muted lg:hidden")}>
                    Clear all filters
                  </Link>
                ) : null}
              </div>
            </form>
          </FilterPanel>
        </aside>

        <section aria-labelledby="results-heading" className="mt-6 lg:mt-0">
          <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-3 border-b border-line pb-4">
            <p className="text-sm text-muted" role="status">
              {page.total === 0 ? (
                "0 results"
              ) : (
                <>
                  <span className="hidden sm:inline">
                    Showing <span className="font-semibold tabular-nums text-ink">{first}–{last}</span> of{" "}
                  </span>
                  <span className="font-semibold tabular-nums text-ink">{page.total}</span>{" "}
                  {page.total === 1 ? "result" : "results"}
                </>
              )}
            </p>
            <SortSelect
              formId={FORM_ID}
              defaultValue={sort}
              options={SORTS.map((s) => ({
                value: s.value,
                label: s.value === "relevance" && !params.q ? "Featured" : s.label,
              }))}
            />
          </div>
          {chips.length > 0 ? (
            <ul aria-label="Active filters" className="mt-4 flex flex-wrap gap-2">
              {chips.map((chip) => (
                <li key={chip.label}>
                  <Link
                    href={chip.href}
                    className="relative inline-flex h-9 items-center gap-1.5 rounded-full bg-brand-50 pl-3.5 pr-2.5 text-sm font-medium text-brand-800 ring-1 ring-inset ring-brand-100 transition-colors duration-150 before:absolute before:inset-x-0 before:-inset-y-1 before:content-[''] hover:bg-brand-100"
                  >
                    <span className="sr-only">Remove filter: </span>
                    {chip.label}
                    <CloseIcon className="size-4 text-brand-600" />
                  </Link>
                </li>
              ))}
            </ul>
          ) : null}
          {page.search?.notice ? (
            <Notice tone="warning" className="mt-4">
              {page.search.notice}
            </Notice>
          ) : null}
          {page.items.length === 0 ? (
            <EmptyState clearHref={clearHref} hasFilters={activeCount > 0} />
          ) : (
            <div className="mt-6 sm:mt-8">
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
}: {
  category: { slug: string; name: string };
  total: number;
  images: string[];
}) {
  const tint = departmentTint(category.slug);
  return (
    <header
      className={cn(
        "relative isolate overflow-hidden rounded-3xl px-6 py-8 sm:rounded-4xl sm:px-10 sm:py-12",
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
        className="pointer-events-none absolute -right-10 top-1/2 -z-10 size-[30rem] -translate-y-1/2 rounded-full bg-white/70 blur-3xl"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(rgb(24_24_35/0.07)_1px,transparent_1px)] bg-size-[20px_20px] [mask-image:linear-gradient(to_right,black,transparent_60%)]"
      />
      <div className="relative z-10 max-w-xl">
        <Breadcrumbs items={[{ label: "Home", href: "/" }, { label: category.name }]} />
        <div className="mt-6 flex items-center gap-4">
          <span className={cn("grid size-14 shrink-0 place-items-center rounded-2xl shadow-sm ring-1 ring-black/5", tint.tile)}>
            <DepartmentIcon slug={category.slug} className="size-7" />
          </span>
          <div>
            <p className={cn("text-xs font-semibold uppercase tracking-eyebrow", tint.text)}>Department</p>
            <h1 id="results-heading" className="mt-1 font-display text-3xl font-semibold text-ink sm:text-5xl">
              {category.name}
            </h1>
          </div>
        </div>
        <p className="mt-5 text-base text-ink-soft">
          {total} {total === 1 ? "product" : "products"}, hand-picked for everyday life.
        </p>
      </div>
      {images.length > 0 ? (
        <div aria-hidden="true" className="absolute inset-y-0 right-4 hidden w-[23rem] md:block lg:right-12 lg:w-104">
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

function SearchHeader({ heading, total, query }: { heading: string; total: number; query?: string }) {
  return (
    <header className="relative isolate overflow-hidden rounded-3xl bg-mesh-light px-6 py-8 sm:rounded-4xl sm:px-10 sm:py-12">
      <Breadcrumbs items={[{ label: "Home", href: "/" }, { label: query ? "Search" : "All products" }]} />
      <p className="mt-6 text-xs font-semibold uppercase tracking-eyebrow text-brand-700">
        {query ? "Search results" : "The whole store"}
      </p>
      <h1 id="results-heading" className="mt-2 max-w-3xl font-display text-3xl font-semibold text-ink sm:text-5xl">
        {heading}
      </h1>
      <p className="mt-4 text-base text-muted">
        {query
          ? `${total} ${total === 1 ? "match" : "matches"} across every department.`
          : `Browse all ${total} products, or narrow things down with the filters.`}
      </p>
    </header>
  );
}

function EmptyState({ clearHref, hasFilters }: { clearHref: string; hasFilters: boolean }) {
  return (
    <div className="mt-8 flex flex-col items-center rounded-3xl border border-dashed border-line-strong bg-raised px-6 py-16 text-center">
      <span className="relative grid size-16 place-items-center rounded-2xl bg-brand-50 text-brand-600 shadow-sm ring-1 ring-inset ring-brand-100">
        <SearchIcon className="size-8" />
        <span className="absolute -right-1.5 -top-1.5 grid size-6 place-items-center rounded-full bg-accent-400 text-xs font-bold text-ink shadow-sm">
          ?
        </span>
      </span>
      <h2 className="mt-6 font-display text-2xl font-semibold text-ink">No products match</h2>
      <p className="mt-2 max-w-sm text-muted">
        Try different words or fewer filters. Check the spelling, or search for something more general.
      </p>
      <div className="mt-6 flex flex-wrap justify-center gap-3">
        {hasFilters ? (
          <Link href={clearHref} className={buttonClasses("secondary", "md")}>
            Clear filters
          </Link>
        ) : null}
        <Link href="/search" className={buttonClasses(hasFilters ? "outline" : "secondary", "md")}>
          Browse all products
        </Link>
        <Link href="/sitemap" className={buttonClasses("outline", "md")}>
          See every department
        </Link>
      </div>
    </div>
  );
}
