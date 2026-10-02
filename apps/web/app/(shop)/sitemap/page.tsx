import { ArrowRightIcon, ChevronDownIcon, DepartmentIcon, SitemapIcon } from "@/components/icons";
import { departmentTint } from "@/components/shop/department-style";
import { serverApi, unwrap } from "@/lib/api-server";
import { cn } from "@/lib/cn";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Site map" };

const SHOP_LINKS = [
  { href: "/", label: "Home" },
  { href: "/search", label: "All products" },
  { href: "/search?sort=top_rated", label: "Top rated" },
  { href: "/search?sort=newest", label: "Newest arrivals" },
  { href: "/search?max_price=5&in_stock=true&sort=price_asc", label: "Under $5" },
] as const;

const ACCOUNT_LINKS = [
  { href: "/orders", label: "Orders & returns" },
  { href: "/activity", label: "Activity" },
  { href: "/cart", label: "Your cart" },
  { href: "/search", label: "Search" },
] as const;

const HELP_LINKS = [
  { href: "/help", label: "Help center" },
  { href: "/support", label: "Support (Xena)" },
  { href: "/stores", label: "Stores" },
  { href: "/help/returns", label: "How returns work" },
  { href: "/help#shipping", label: "Shipping and delivery" },
  { href: "/help#labels", label: "What product labels mean" },
] as const;

const POLICY_LINKS = [
  { href: "/returns-policy", label: "Return & refund policy" },
  { href: "/privacy", label: "Privacy" },
  { href: "/terms", label: "Terms" },
  { href: "/accessibility", label: "Accessibility" },
] as const;

type Facet = { value: string; label: string; count: number };

export default async function SitemapPage() {
  const api = await serverApi();
  const [categories, catalog] = await Promise.all([
    api.GET("/v1/categories").then(unwrap),
    // Only the facets matter: the total and a real count for every department.
    api.GET("/v1/products", { params: { query: { page_size: 1 } } }).then(unwrap),
  ]);
  // Each department's product types, from its facets. A failed read just lists no types.
  const typesByCategory = new Map<string, Facet[]>(
    await Promise.all(
      categories.map(async (c): Promise<[string, Facet[]]> => {
        const types = await api
          .GET("/v1/products", { params: { query: { category: c.slug, page_size: 1 } } })
          .then((r) => r.data?.facets.product_types ?? [])
          .catch(() => []);
        return [c.slug, [...types].sort((a, b) => a.label.localeCompare(b.label))];
      }),
    ),
  );
  const counts = new Map(catalog.facets.categories.map((f) => [f.value, f.count]));

  return (
    <div>
      <header className="relative isolate overflow-hidden rounded-3xl bg-mesh-light px-6 py-10 sm:rounded-4xl sm:px-12 sm:py-14">
        <span className="grid size-12 place-items-center rounded-2xl bg-raised text-brand-600 shadow-md">
          <SitemapIcon className="size-6" />
        </span>
        <h1 className="mt-6 font-display text-4xl font-semibold text-ink sm:text-5xl">Site map</h1>
        <p className="mt-4 max-w-2xl text-lg text-muted">
          Every department and the kinds of products in it, plus help, account, and policy pages, all in one place.
        </p>
        <dl className="mt-8 flex flex-wrap gap-x-10 gap-y-4">
          <div>
            <dt className="text-xs font-semibold uppercase tracking-eyebrow text-brand-700">Departments</dt>
            <dd className="mt-1 font-display text-3xl font-semibold tabular-nums text-ink">{categories.length}</dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase tracking-eyebrow text-brand-700">Products</dt>
            <dd className="mt-1 font-display text-3xl font-semibold tabular-nums text-ink">
              {catalog.total.toLocaleString("en-US")}
            </dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase tracking-eyebrow text-brand-700">Stores</dt>
            <dd className="mt-1 font-display text-3xl font-semibold tabular-nums text-ink">10</dd>
          </div>
        </dl>
      </header>

      <div className="mt-12 lg:grid lg:grid-cols-[15rem_minmax(0,1fr)] lg:items-start lg:gap-14">
        <nav aria-label="Site map sections" className="hidden lg:sticky lg:top-36 lg:block">
          <p className="text-xs font-semibold uppercase tracking-eyebrow text-muted">On this page</p>
          <ul className="mt-3 max-h-[calc(100vh-11rem)] space-y-0.5 overflow-y-auto border-l border-line">
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
                href="#help-and-account"
                className="-ml-px flex min-h-9 items-center border-l-2 border-transparent pl-4 text-sm text-muted transition-colors duration-150 hover:border-brand-600 hover:text-ink"
              >
                Help, account &amp; policies
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
              {[...SHOP_LINKS, { href: "/stores", label: "Stores" }, { href: "/help", label: "Help center" }].map((l) => (
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

          <div id="departments" className="scroll-mt-40 space-y-6">
            <h2 className="sr-only">Departments</h2>
            {categories.map((c) => {
              const count = counts.get(c.slug) ?? 0;
              const types = typesByCategory.get(c.slug) ?? [];
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
                        <h3 id={`dept-${c.slug}-heading`} className="font-display text-2xl font-semibold text-ink">
                          {c.name}
                        </h3>
                        <p className="text-sm text-muted">
                          {count.toLocaleString("en-US")} {count === 1 ? "product" : "products"}
                          {types.length > 1 ? (
                            <>
                              {" "}
                              <span aria-hidden="true">·</span> {types.length} kinds
                            </>
                          ) : null}
                        </p>
                      </div>
                    </div>
                    <Link
                      href={`/c/${c.slug}`}
                      className="group inline-flex min-h-11 items-center gap-1.5 rounded-full px-3 text-sm font-semibold text-brand-700 transition-colors hover:bg-brand-50 hover:text-brand-900"
                    >
                      Shop all<span className="sr-only"> {c.name}</span>
                      <ArrowRightIcon className="size-4 transition-transform duration-200 ease-snappy group-hover:translate-x-0.5" />
                    </Link>
                  </div>
                  {types.length > 1 ? (
                    // On phones the kinds fold behind a disclosure so the page isn't 18,000px of
                    // links; from sm up the summary hides and the list always shows.
                    <details className="group mt-5 border-t border-line pt-2 sm:mt-6 sm:pt-5 sm:details-content:[content-visibility:visible]">
                      <summary className="flex min-h-11 list-none items-center rounded-lg justify-between gap-2 text-sm font-semibold text-brand-700 hover:text-brand-900 sm:hidden">
                        Browse {types.length} kinds<span className="sr-only"> of {c.name}</span>
                        <ChevronDownIcon className="size-4.5 transition-transform duration-200 group-open:rotate-180 motion-reduce:transition-none" />
                      </summary>
                      <ul
                        aria-label={`Kinds of products in ${c.name}`}
                        className="mt-1 grid grid-cols-2 gap-x-6 pb-1 sm:mt-0 sm:grid-cols-3 sm:pb-0 xl:grid-cols-4"
                      >
                        {types.map((t) => (
                          <li key={t.value} className="min-w-0">
                            <Link
                              href={`/c/${c.slug}?product_type=${encodeURIComponent(t.value)}`}
                              className="group/type flex min-h-10 items-baseline gap-1.5 py-1.5 text-[0.9375rem] leading-snug text-ink transition-colors duration-150 hover:text-brand-700"
                            >
                              <span className="underline decoration-transparent underline-offset-4 transition-colors group-hover/type:decoration-brand-300">
                                {t.label}
                              </span>
                              <span className="text-xs tabular-nums text-muted">
                                {t.count}
                                <span className="sr-only"> {t.count === 1 ? "product" : "products"}</span>
                              </span>
                            </Link>
                          </li>
                        ))}
                      </ul>
                    </details>
                  ) : null}
                </section>
              );
            })}
          </div>

          <section
            id="help-and-account"
            aria-labelledby="help-and-account-heading"
            className="scroll-mt-40 rounded-3xl bg-inverse p-6 text-brand-200 focus-inverse sm:p-8"
          >
            <h2 id="help-and-account-heading" className="font-display text-2xl font-semibold text-white">
              Help, account &amp; policies
            </h2>
            <div className="mt-6 grid gap-8 sm:grid-cols-3">
              <LinkList title="Help & support" links={HELP_LINKS} />
              <LinkList title="Your account" links={ACCOUNT_LINKS} />
              <LinkList title="Policies" links={POLICY_LINKS} />
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

function LinkList({ title, links }: { title: string; links: readonly { href: string; label: string }[] }) {
  return (
    <div>
      <h3 className="font-sans text-xs font-semibold uppercase tracking-eyebrow text-accent-300">{title}</h3>
      <ul className="mt-3">
        {links.map((l) => (
          <li key={l.href}>
            <Link
              href={l.href}
              className="inline-flex min-h-10 items-center text-[0.9375rem] hover:text-white hover:underline hover:underline-offset-4"
            >
              {l.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
