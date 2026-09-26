import { ArrowRightIcon, DepartmentIcon, SitemapIcon } from "@/components/icons";
import { departmentTint } from "@/components/shop/department-style";
import { serverApi, unwrap } from "@/lib/api-server";
import { cn } from "@/lib/cn";
import { formatMoney } from "@/lib/format";
import type { ProductSummary } from "@ai-commerce/contracts";
import Link from "next/link";

export const metadata = { title: "Site map" };

const SHOP_LINKS = [
  { href: "/", label: "Home" },
  { href: "/search", label: "All products" },
  { href: "/search?sort=top_rated", label: "Top rated" },
  { href: "/search?sort=newest", label: "Newest arrivals" },
] as const;

const ACCOUNT_LINKS = [
  { href: "/orders", label: "Orders & returns" },
  { href: "/activity", label: "Activity" },
  { href: "/cart", label: "Your cart" },
  { href: "/search", label: "Search" },
] as const;

const POLICY_LINKS = [
  { href: "/help/returns", label: "How returns work" },
  { href: "/privacy", label: "Privacy" },
  { href: "/terms", label: "Terms" },
  { href: "/accessibility", label: "Accessibility" },
] as const;


export default async function SitemapPage() {
  const api = await serverApi();
  const [categories, catalog] = await Promise.all([
    api.GET("/v1/categories").then(unwrap),
    // The whole catalog in one read (the API caps page_size at 60), grouped by department below.
    api.GET("/v1/products", { params: { query: { page_size: 60 } } }).then(unwrap),
  ]);

  const byCategory = new Map<string, ProductSummary[]>();
  for (const p of catalog.items) {
    const list = byCategory.get(p.category.slug) ?? [];
    list.push(p);
    byCategory.set(p.category.slug, list);
  }
  for (const list of byCategory.values()) list.sort((a, b) => a.title.localeCompare(b.title));
  const partial = catalog.total > catalog.items.length;

  return (
    <div>
      <header className="relative isolate overflow-hidden rounded-3xl bg-mesh-light px-6 py-10 sm:rounded-4xl sm:px-12 sm:py-14">
        <span className="grid size-12 place-items-center rounded-2xl bg-raised text-brand-600 shadow-md">
          <SitemapIcon className="size-6" />
        </span>
        <h1 className="mt-6 font-display text-4xl font-semibold text-ink sm:text-5xl">Site map</h1>
        <p className="mt-4 max-w-2xl text-lg text-muted">
          Every department, every product, and every page in the store, all in one place.
        </p>
        <dl className="mt-8 flex flex-wrap gap-x-10 gap-y-4">
          <div>
            <dt className="text-xs font-semibold uppercase tracking-eyebrow text-brand-700">Departments</dt>
            <dd className="mt-1 font-display text-3xl font-semibold tabular-nums text-ink">{categories.length}</dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase tracking-eyebrow text-brand-700">Products</dt>
            <dd className="mt-1 font-display text-3xl font-semibold tabular-nums text-ink">{catalog.total}</dd>
          </div>
        </dl>
      </header>

      <div className="mt-12 lg:grid lg:grid-cols-[15rem_minmax(0,1fr)] lg:items-start lg:gap-14">
        <nav aria-label="Site map sections" className="hidden lg:sticky lg:top-36 lg:block">
          <p className="text-xs font-semibold uppercase tracking-eyebrow text-muted">On this page</p>
          <ul className="mt-3 space-y-0.5 border-l border-line">
            {categories.map((c) => (
              <li key={c.slug}>
                <a
                  href={`#dept-${c.slug}`}
                  className="-ml-px flex min-h-9 items-center gap-2.5 border-l-2 border-transparent pl-4 text-sm text-muted transition-colors duration-150 hover:border-brand-600 hover:text-ink"
                >
                  <DepartmentIcon slug={c.slug} className="size-4" />
                  {c.name}
                </a>
              </li>
            ))}
            <li>
              <a
                href="#account-and-help"
                className="-ml-px flex min-h-9 items-center border-l-2 border-transparent pl-4 text-sm text-muted transition-colors duration-150 hover:border-brand-600 hover:text-ink"
              >
                Account &amp; help
              </a>
            </li>
          </ul>
        </nav>

        <div className="space-y-6">
          <section aria-labelledby="shop-heading" className="rounded-3xl border border-line bg-raised p-6 shadow-xs sm:p-8">
            <h2 id="shop-heading" className="font-display text-2xl font-semibold text-ink">
              Shop
            </h2>
            <ul className="mt-5 flex flex-wrap gap-2">
              {SHOP_LINKS.map((l) => (
                <li key={l.href}>
                  <Link
                    href={l.href}
                    className="group inline-flex min-h-11 items-center gap-1.5 rounded-full bg-sunken px-4 text-sm font-semibold text-ink transition-colors duration-150 hover:bg-brand-50 hover:text-brand-800"
                  >
                    {l.label}
                    <ArrowRightIcon className="size-4 text-muted transition-transform duration-200 ease-snappy group-hover:translate-x-0.5 group-hover:text-brand-600" />
                  </Link>
                </li>
              ))}
            </ul>
          </section>

          {categories.map((c) => {
            const products = byCategory.get(c.slug) ?? [];
            const tint = departmentTint(c.slug);
            return (
              <section
                key={c.slug}
                id={`dept-${c.slug}`}
                aria-labelledby={`dept-${c.slug}-heading`}
                className="scroll-mt-40 rounded-3xl border border-line bg-raised p-6 shadow-xs sm:p-8"
              >
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <span className={cn("grid size-12 shrink-0 place-items-center rounded-2xl", tint.tile)}>
                      <DepartmentIcon slug={c.slug} className="size-6" />
                    </span>
                    <div>
                      <h2 id={`dept-${c.slug}-heading`} className="font-display text-2xl font-semibold text-ink">
                        {c.name}
                      </h2>
                      <p className="text-sm text-muted">
                        {products.length} {products.length === 1 ? "product" : "products"}
                      </p>
                    </div>
                  </div>
                  <Link
                    href={`/c/${c.slug}`}
                    className="group inline-flex min-h-11 items-center gap-1.5 rounded-full px-3 text-sm font-semibold text-brand-700 transition-colors hover:bg-brand-50 hover:text-brand-900"
                  >
                    Shop {c.name}
                    <ArrowRightIcon className="size-4 transition-transform duration-200 ease-snappy group-hover:translate-x-0.5" />
                  </Link>
                </div>
                {products.length > 0 ? (
                  <ul className="mt-6 grid gap-x-8 gap-y-4 border-t border-line pt-6 sm:grid-cols-2 xl:grid-cols-3">
                    {products.map((p) => (
                      <li key={p.id} className="min-w-0">
                        <Link
                          href={`/products/${p.id}`}
                          className="group block rounded-md text-[0.9375rem] font-medium leading-snug text-ink transition-colors duration-150 hover:text-brand-700"
                        >
                          <span className="underline decoration-transparent underline-offset-4 transition-colors group-hover:decoration-brand-300">
                            {p.title}
                          </span>
                        </Link>
                        <p className="mt-0.5 text-xs text-muted">
                          {p.brand} <span aria-hidden="true">·</span>{" "}
                          <span className="tabular-nums">
                            {p.variant_count > 1 ? "from " : ""}
                            {formatMoney(p.price_minor, p.currency)}
                          </span>
                        </p>
                      </li>
                    ))}
                  </ul>
                ) : null}
              </section>
            );
          })}

          {partial ? (
            <p className="text-sm text-muted">
              Showing the first {catalog.items.length} of {catalog.total} products.{" "}
              <Link href="/search" className="font-medium text-brand-700 underline decoration-brand-300 underline-offset-4 hover:decoration-brand-700">
                Browse everything
              </Link>
              .
            </p>
          ) : null}

          <section
            id="account-and-help"
            aria-labelledby="account-and-help-heading"
            className="scroll-mt-40 rounded-3xl bg-inverse p-6 text-brand-200 focus-inverse sm:p-8"
          >
            <h2 id="account-and-help-heading" className="font-display text-2xl font-semibold text-white">
              Account &amp; help
            </h2>
            <div className="mt-6 grid gap-8 sm:grid-cols-2">
              <div>
                <h3 className="font-sans text-xs font-semibold uppercase tracking-eyebrow text-accent-300">Your account</h3>
                <ul className="mt-3">
                  {ACCOUNT_LINKS.map((l) => (
                    <li key={l.href}>
                      <Link href={l.href} className="inline-flex min-h-10 items-center text-[0.9375rem] hover:text-white hover:underline hover:underline-offset-4">
                        {l.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="font-sans text-xs font-semibold uppercase tracking-eyebrow text-accent-300">Policies</h3>
                <ul className="mt-3">
                  {POLICY_LINKS.map((l) => (
                    <li key={l.href}>
                      <Link href={l.href} className="inline-flex min-h-10 items-center text-[0.9375rem] hover:text-white hover:underline hover:underline-offset-4">
                        {l.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
