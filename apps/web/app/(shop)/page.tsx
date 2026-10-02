import { RecentlyViewed } from "@/components/activity/recently-viewed";
import { OpenStephButton } from "@/components/assistant/open-steph";
import {
  ArrowRightIcon,
  ChatIcon,
  DepartmentIcon,
  MapIcon,
  MicIcon,
  ReturnIcon,
  SearchIcon,
  TagIcon,
  TruckIcon,
  type Icon,
} from "@/components/icons";
import { LogoMark } from "@/components/logo";
import { departmentTint } from "@/components/shop/department-style";
import { ProductGrid } from "@/components/shop/product-card";
import { HomeSectionsSkeleton } from "@/components/shop/page-skeletons";
import { ButtonLink } from "@/components/ui/button";
import { SectionHeading } from "@/components/ui/section-heading";
import { RatingBadge } from "@/components/ui/stars";
import { WebVitalsReporter } from "@/components/web-vitals";
import { recentlyViewed } from "@/lib/activity";
import { getMe, serverApi, unwrap } from "@/lib/api-server";
import { cn } from "@/lib/cn";
import type { CategoryOut, ProductSummary } from "@ai-commerce/contracts";
import Link from "next/link";
import { Suspense, type ReactNode } from "react";

/** What people actually shop for here: mostly groceries and household basics, plus a few favorites. */
const POPULAR_SEARCHES = ["milk", "yogurt", "eggs", "coffee", "bread", "paper towels", "headphones"];

/**
 * Product types that front the hero collage, grocery first. Each tile shows the best-rated product
 * of that type, and the art is that type's own illustration, so the picture always matches the name.
 */
const HERO_TYPES = ["apples", "milk", "headphones"];

/**
 * Art for each department tile, chosen so the picture (and the name printed on type art) fits the
 * department. Departments not listed fall back to their best-rated product's image.
 */
const DEPARTMENT_ART: Record<string, string> = {
  "dairy-eggs": "/images/types/milk.svg",
  produce: "/images/types/apples.svg",
  "meat-seafood": "/images/types/salmon.svg",
  bakery: "/images/types/bread.svg",
  frozen: "/images/types/ice-cream.svg",
  pantry: "/images/types/honey.svg",
  snacks: "/images/types/chips.svg",
  beverages: "/images/types/juice.svg",
  household: "/images/types/dish-soap.svg",
  "health-wellness": "/images/types/multivitamin.svg",
  baby: "/images/types/baby-wash.svg",
  pet: "/images/types/dog-food.svg",
  electronics: "/images/products/sonora-arc-wireless-headphones.svg",
  "home-kitchen": "/images/products/kettleworth-french-press.svg",
  "clothing-shoes": "/images/products/stridewell-rain-boots.svg",
  outdoor: "/images/products/summit-forge-2p-tent.svg",
  sports: "/images/products/tempo-yoga-mat.svg",
  toys: "/images/products/pebble-pine-plush-otter.svg",
  beauty: "/images/products/verdant-botanicals-face-moisturizer.svg",
  office: "/images/products/quillmark-dotted-notebook.svg",
  "gift-cards": "/images/products/serigan-mart-gift-card.svg",
};

/** Diet tags for "Shop by diet", in display order. Only tags the catalog actually has are shown. */
const DIET_TAGS = [
  "gluten-free",
  "vegan",
  "dairy-free",
  "keto",
  "organic",
  "sugar-free",
  "high-protein",
  "plant-based",
  "lactose-free",
  "low-sodium",
];

/** Everything here is true today (see content/policies and the stores page). */
const TRUST_ITEMS: { icon: Icon; title: string; body: string; href: string }[] = [
  {
    icon: TruckIcon,
    title: "Free shipping over $35",
    body: "Otherwise $5.99. Most orders arrive in 2–5 business days.",
    href: "/help#shipping",
  },
  {
    icon: ReturnIcon,
    title: "30-day returns, free return shipping",
    body: "Start online, see your exact refund, and confirm it yourself.",
    href: "/help/returns",
  },
  {
    icon: ChatIcon,
    title: "Help from Steph and Xena, any time",
    body: "Steph helps you shop. Xena handles returns by voice or text.",
    href: "/help",
  },
  {
    icon: MapIcon,
    title: "10 stores around Dallas–Fort Worth",
    body: "Hours, directions, and return drop-off at every store.",
    href: "/stores",
  },
];

/**
 * The hero and the trust row render right away (the name comes from the layout's cached read);
 * the collage and the catalog sections stream in behind skeletons, so opening the home page is
 * instant even though it reads a lot of the catalog.
 */
export default async function HomePage() {
  const user = await getMe();
  const firstName = user.display_name.split(" ")[0] ?? user.display_name;

  return (
    <div className="space-y-16 sm:space-y-24">
      <WebVitalsReporter route="home" />

      <Hero
        firstName={firstName}
        collage={
          <Suspense fallback={<CollageFrame />}>
            <HeroCollage />
          </Suspense>
        }
      />

      <section aria-label="Why shop with Serigan Mart" className="-mt-8 sm:-mt-14">
        <ul className="grid gap-px overflow-hidden rounded-3xl border border-line bg-line shadow-xs sm:grid-cols-2 lg:grid-cols-4">
          {TRUST_ITEMS.map(({ icon: ItemIcon, title, body, href }) => (
            <li key={title} className="bg-raised">
              <Link
                href={href}
                className="group flex h-full gap-4 p-5 transition-colors duration-150 hover:bg-sunken/60 sm:block sm:p-6"
              >
                <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-brand-50 text-brand-700 ring-1 ring-inset ring-brand-100">
                  <ItemIcon className="size-5.5" />
                </span>
                <span className="block min-w-0 sm:mt-4">
                  <span className="block text-[0.9375rem] font-semibold text-ink group-hover:text-brand-800">
                    {title}
                  </span>
                  <span className="mt-1 block text-sm leading-relaxed text-muted">{body}</span>
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      <Suspense fallback={<HomeSectionsSkeleton />}>
        <HomeSections />
      </Suspense>
    </div>
  );
}

/** Everything below the trust row: one batch of catalog reads. */
async function HomeSections() {
  const api = await serverApi();
  const [categories, featured, rated, underFive, viewed] = await Promise.all([
    api.GET("/v1/categories").then(unwrap),
    // The default order with no query is "featured": well-reviewed, in stock, and varied. Read a
    // wide page so there's a pick from most departments.
    api.GET("/v1/products", { params: { query: { in_stock: true, page_size: 60 } } }).then(unwrap),
    // One ranked read of the catalog: the first 8 are "Top rated", and the best product in each
    // department fronts its tile. Its facets give per-department totals and diet tag counts.
    api.GET("/v1/products", { params: { query: { sort: "top_rated", page_size: 60 } } }).then(unwrap),
    // Only the total matters here.
    api
      .GET("/v1/products", { params: { query: { max_price: 500, in_stock: true, page_size: 1 } } })
      .then((r) => r.data?.total ?? null)
      .catch(() => null),
    // Optional: a failed activity read just hides "Recently viewed".
    api
      .GET("/v1/activity", { params: { query: { type: ["viewed_product"], limit: 20 } } })
      .then((r) => recentlyViewed(r.data ?? [], 8))
      .catch(() => []),
  ]);

  const topRated = rated.items.slice(0, 8);
  const bestInDepartment = firstPerDepartment(rated.items);
  const freshPicks = [...firstPerDepartment(featured.items).values()].slice(0, 8);
  const counts = new Map(rated.facets.categories.map((f) => [f.value, f.count]));
  const tagFacets = new Map(rated.facets.tags.map((f) => [f.value, f]));
  const diets = DIET_TAGS.flatMap((value) => {
    const facet = tagFacets.get(value);
    return facet && facet.count > 0 ? [facet] : [];
  });

  return (
    <>
      <RecentlyViewed products={viewed} />

      <section aria-labelledby="departments">
        <SectionHeading
          id="departments"
          eyebrow="Browse"
          title="Shop by department"
          description="Fresh food, pantry staples, and household basics, plus everything for home, work, and play."
          action={{ href: "/sitemap#departments", label: "All departments", srLabel: "on the site map" }}
        />
        <ul className="mt-6 grid auto-rows-44 grid-flow-dense grid-cols-2 gap-3 sm:mt-8 sm:auto-rows-50 sm:grid-cols-3 sm:gap-4 lg:grid-cols-4">
          {categories.map((c, i) => (
            <DepartmentTile
              key={c.slug}
              category={c}
              image={DEPARTMENT_ART[c.slug] ?? bestInDepartment.get(c.slug)?.image_path}
              count={counts.get(c.slug)}
              featured={i === 0}
            />
          ))}
        </ul>
      </section>

      {freshPicks.length > 0 ? (
        <section aria-labelledby="fresh-picks">
          <SectionHeading
            id="fresh-picks"
            eyebrow="Featured"
            title="Fresh picks from every department"
            description="Well-reviewed and in stock: one favorite from each of eight aisles."
            action={{ href: "/search?in_stock=true", label: "See all", srLabel: "featured products" }}
          />
          <div className="mt-6 sm:mt-8">
            <ProductGrid products={freshPicks} label="Fresh picks from every department" />
          </div>
        </section>
      ) : null}

      <ShopByDiet diets={diets} underFive={underFive} />

      {topRated.length > 0 ? (
        <section
          aria-labelledby="top-rated"
          className="relative isolate overflow-hidden rounded-4xl bg-mesh-light px-4 py-10 sm:px-10 sm:py-14"
        >
          <SectionHeading
            id="top-rated"
            eyebrow="Loved by shoppers"
            title="Top rated"
            description="The highest-rated picks right now. Ratings include clearly labeled sample reviews."
            action={{ href: "/search?sort=top_rated", label: "See all", srLabel: "top rated products" }}
          />
          <div className="mt-6 sm:mt-8">
            <ProductGrid products={topRated} label="Top rated" ranked />
          </div>
        </section>
      ) : null}

      <PromoRow />
    </>
  );
}

/** The first product per department, keeping the list's order. */
function firstPerDepartment(items: ProductSummary[]): Map<string, ProductSummary> {
  const out = new Map<string, ProductSummary>();
  for (const p of items) if (!out.has(p.category.slug)) out.set(p.category.slug, p);
  return out;
}

/**
 * On phones the hero is just the greeting, one line of copy, the two buttons, and a single
 * scrolling row of popular searches: the product collage starts at sm, so departments and
 * products come up within the first screen or so.
 */
function Hero({ firstName, collage }: { firstName: string; collage: ReactNode }) {
  return (
    <section
      aria-labelledby="hero-title"
      className="relative isolate overflow-hidden rounded-3xl bg-mesh-dark text-white shadow-xl focus-inverse sm:rounded-4xl"
    >
      {/* decorative dot grid fading out toward the text */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(rgb(255_255_255/0.14)_1px,transparent_1px)] bg-size-[22px_22px] [mask-image:radial-gradient(70%_80%_at_85%_30%,black,transparent_75%)]"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-24 -top-24 -z-10 size-[28rem] rounded-full bg-brand-500/30 blur-3xl"
      />
      <div className="grid items-center gap-10 px-5 pb-6 pt-7 sm:px-12 sm:py-16 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)] lg:gap-6 lg:py-16 lg:pl-16 lg:pr-10">
        <div className="min-w-0">
          <p className="inline-flex animate-fade-up items-center gap-2 rounded-full bg-white/10 py-1 pl-1.5 pr-3.5 text-xs font-semibold uppercase tracking-eyebrow text-accent-300 ring-1 ring-inset ring-white/15 backdrop-blur-sm">
            <span aria-hidden="true" className="relative flex size-5 items-center justify-center rounded-full bg-accent-400/20">
              <span className="size-2 rounded-full bg-accent-300" />
            </span>
            Welcome back, {firstName}
          </p>
          <h1
            id="hero-title"
            className="mt-4 max-w-xl animate-fade-up font-display text-[2.25rem] font-semibold leading-[1.05] tracking-[-0.035em] text-white animation-delay-80 sm:mt-6 sm:text-display"
          >
            Everyday essentials,{" "}
            <span className="bg-linear-to-r from-brand-200 via-white to-accent-200 bg-clip-text text-transparent">
              beautifully easy.
            </span>
          </h1>
          <p className="mt-3 max-w-lg animate-fade-up text-base leading-relaxed text-brand-200 animation-delay-160 sm:mt-6 sm:text-lg">
            <span className="sm:hidden">Groceries, household basics, and more. Ask Steph when you need a hand.</span>
            <span className="max-sm:hidden">
              Fresh food, pantry staples, and household basics, plus electronics, home, clothing, toys, and more. Ask
              Steph when you need a hand, and return anything online in a few taps.
            </span>
          </p>
          <div className="mt-5 grid animate-fade-up grid-cols-2 gap-2 animation-delay-240 sm:mt-8 sm:flex sm:flex-wrap sm:gap-3">
            <ButtonLink href="/search" variant="inverse" size="lg" className="max-sm:px-4">
              Start shopping
              <ArrowRightIcon className="size-4.5 max-sm:hidden" />
            </ButtonLink>
            <ButtonLink
              href="/c/produce"
              variant="ghost"
              size="lg"
              className="text-white ring-1 ring-inset ring-white/25 hover:bg-white/10 active:bg-white/15 max-sm:px-4"
            >
              <span className="sm:hidden">Fresh produce</span>
              <span className="max-sm:hidden">Shop fresh produce</span>
            </ButtonLink>
          </div>
          <div className="mt-5 animate-fade-up animation-delay-320 sm:mt-10">
            <p id="popular-searches" className="text-xs font-semibold uppercase tracking-eyebrow text-brand-300">
              Popular searches
            </p>
            {/* One sideways-scrolling row on phones; wraps from sm up. */}
            <ul
              aria-labelledby="popular-searches"
              className="-mx-5 mt-3 flex gap-2 overflow-x-auto px-5 py-1 scrollbar-none sm:mx-0 sm:flex-wrap sm:overflow-visible sm:px-0 sm:py-0"
            >
              {POPULAR_SEARCHES.map((q) => (
                <li key={q} className="shrink-0">
                  <Link
                    href={`/search?q=${encodeURIComponent(q)}`}
                    className="relative inline-flex h-9 items-center gap-1.5 rounded-full bg-white/8 px-3.5 text-sm font-medium text-white ring-1 ring-inset ring-white/15 transition-colors duration-150 before:absolute before:inset-x-0 before:-inset-y-1 before:content-[''] hover:bg-white/15 hover:ring-white/30"
                  >
                    <SearchIcon className="size-3.5 text-brand-200" />
                    {q}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {collage}
      </div>
    </section>
  );
}

/** The collage's box, kept while its products load so the hero doesn't change size. Not on phones. */
function CollageFrame({ children }: { children?: ReactNode }) {
  return (
    <div
      aria-hidden="true"
      className="relative mx-auto aspect-[1.08] w-full max-w-md max-sm:hidden sm:max-w-lg lg:max-w-none"
    >
      {children}
    </div>
  );
}

/** Three tiles, each the best-rated product of a hero type. Optional: a failed read leaves a tile out. */
async function HeroCollage() {
  const api = await serverApi();
  const picks = await Promise.all(
    HERO_TYPES.map((type) =>
      api
        .GET("/v1/products", {
          params: { query: { product_type: [type], in_stock: true, sort: "top_rated", page_size: 1 } },
        })
        .then((r) => r.data?.items[0])
        .catch(() => undefined),
    ),
  );
  const [a, b, c] = picks.filter((p): p is ProductSummary => p !== undefined);
  if (!a) return null;
  return (
    <CollageFrame>
      <div className="absolute inset-[12%] rounded-full bg-brand-400/30 blur-3xl" />
      <HeroTile product={a} className="left-[3%] top-[4%] w-[54%] -rotate-6 animate-fade-up animation-delay-160" />
      {b ? (
        <HeroTile product={b} className="right-[2%] top-[14%] w-[42%] rotate-[5deg] animate-fade-up animation-delay-240" />
      ) : null}
      {c ? (
        <HeroTile product={c} className="bottom-[2%] left-[28%] w-[38%] -rotate-2 animate-fade-up animation-delay-320" />
      ) : null}
      <div className="absolute bottom-[14%] right-0 flex max-w-[15rem] animate-fade-up items-center gap-3 rounded-2xl bg-raised/95 p-2.5 pr-4 text-ink shadow-2xl ring-1 ring-black/5 backdrop-blur animation-delay-400">
        {/* eslint-disable-next-line @next/next/no-img-element -- local SVG illustrations */}
        <img src={a.image_path} alt="" width={44} height={44} className="size-11 rounded-xl" />
        <div className="min-w-0">
          <p className="truncate text-xs font-semibold text-ink">{a.title}</p>
          <RatingBadge average={a.rating_average} count={a.rating_count} className="mt-0.5" />
        </div>
      </div>
    </CollageFrame>
  );
}

function HeroTile({ product, className }: { product: ProductSummary; className?: string }) {
  return (
    <div
      className={cn(
        "absolute overflow-hidden rounded-[1.75rem] bg-white shadow-2xl ring-1 ring-white/30 transition-transform duration-500 ease-smooth",
        className,
      )}
    >
      {/* eslint-disable-next-line @next/next/no-img-element -- local SVG illustrations */}
      <img src={product.image_path} alt="" width={640} height={640} className="aspect-square w-full" />
    </div>
  );
}

function DepartmentTile({
  category,
  image,
  count,
  featured,
}: {
  category: CategoryOut;
  image?: string;
  count?: number;
  featured: boolean;
}) {
  const tint = departmentTint(category.slug);
  return (
    <li className={cn(featured && "col-span-2 row-span-2")}>
      <Link
        href={`/c/${category.slug}`}
        className={cn(
          "group relative flex h-full flex-col overflow-hidden rounded-3xl ring-1 ring-inset shadow-xs transition-[box-shadow,transform] duration-300 ease-smooth hover:-translate-y-1 hover:shadow-lg motion-reduce:hover:translate-y-0",
          tint.surface,
          tint.ring,
        )}
      >
        {/* The art sits whole above the label band: square, centered, never cropped. */}
        <span className="relative block min-h-0 flex-1">
          {image ? (
            // eslint-disable-next-line @next/next/no-img-element -- local SVG illustrations
            <img
              src={image}
              alt=""
              width={640}
              height={640}
              loading="lazy"
              className={cn(
                "absolute bottom-0 left-1/2 top-2.5 aspect-square h-[calc(100%-0.625rem)] w-auto max-w-none -translate-x-1/2 rounded-2xl shadow-sm ring-1 ring-black/5 transition-transform duration-500 ease-smooth group-hover:scale-[1.03] motion-reduce:group-hover:scale-100 sm:top-3 sm:h-[calc(100%-0.75rem)]",
                featured && "sm:top-4 sm:h-[calc(100%-1rem)]",
              )}
            />
          ) : (
            <span className="absolute inset-0 grid place-items-center">
              <DepartmentIcon slug={category.slug} className={cn("size-14 opacity-70", tint.text)} />
            </span>
          )}
        </span>
        <span
          aria-hidden="true"
          className="absolute right-3 top-3 grid size-9 translate-y-1 place-items-center rounded-full bg-raised/95 text-ink opacity-0 shadow-sm transition-[opacity,transform] duration-300 ease-smooth group-hover:translate-y-0 group-hover:opacity-100 group-focus-visible:translate-y-0 group-focus-visible:opacity-100"
        >
          <ArrowRightIcon className="size-4" />
        </span>
        <span
          className={cn(
            "relative m-2 flex items-center gap-2 rounded-2xl bg-raised/90 p-1.5 pr-2.5 shadow-sm ring-1 ring-black/5 sm:m-3 sm:gap-2.5 sm:p-2 sm:pr-3",
            featured && "sm:m-4 sm:gap-3 sm:p-2.5 sm:pr-4",
          )}
        >
          <span className={cn("grid size-8 shrink-0 place-items-center rounded-xl sm:size-9", tint.tile, featured && "sm:size-11")}>
            <DepartmentIcon slug={category.slug} className={cn("size-5", featured && "sm:size-6")} />
          </span>
          <span className="min-w-0">
            <span
              className={cn(
                "line-clamp-2 text-sm font-semibold leading-tight text-ink",
                featured && "sm:font-display sm:text-lg",
              )}
            >
              {category.name}
            </span>
            {count ? (
              <span className="mt-0.5 block text-xs text-muted">
                {count.toLocaleString("en-US")} {count === 1 ? "product" : "products"}
              </span>
            ) : null}
          </span>
        </span>
      </Link>
    </li>
  );
}

function ShopByDiet({
  diets,
  underFive,
}: {
  diets: { value: string; label: string; count: number }[];
  underFive: number | null;
}) {
  if (diets.length === 0 && !underFive) return null;
  return (
    <section aria-labelledby="shop-by-diet" className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_20rem] lg:gap-6">
      <div className="rounded-3xl border border-line bg-raised p-6 shadow-xs sm:p-8">
        <SectionHeading
          id="shop-by-diet"
          eyebrow="Eat your way"
          title="Shop by diet"
          size="sm"
          description="Every label follows a written definition."
          action={{ href: "/help#labels", label: "What labels mean" }}
        />
        <ul className="mt-6 flex flex-wrap gap-2">
          {diets.map((d) => (
            <li key={d.value}>
              <Link
                href={`/search?tag=${encodeURIComponent(d.value)}`}
                className="group inline-flex min-h-11 items-center gap-2 rounded-full bg-sunken px-4 text-sm font-semibold text-ink ring-1 ring-inset ring-line transition-colors duration-150 hover:bg-brand-50 hover:text-brand-800 hover:ring-brand-200"
              >
                {d.label}
                <span className="text-xs font-medium tabular-nums text-muted group-hover:text-brand-700">
                  {d.count.toLocaleString("en-US")}
                  <span className="sr-only"> products</span>
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </div>

      {underFive ? (
        <Link
          href="/search?max_price=5&in_stock=true&sort=price_asc"
          className="group relative isolate flex flex-col justify-between gap-6 overflow-hidden rounded-3xl bg-accent-50 p-6 ring-1 ring-inset ring-accent-100 transition-shadow duration-300 hover:shadow-lg sm:p-8"
        >
          <div
            aria-hidden="true"
            className="absolute -bottom-12 -right-12 -z-10 size-48 rounded-full bg-accent-200/60 blur-2xl"
          />
          <span className="grid size-11 place-items-center rounded-2xl bg-raised text-accent-800 shadow-xs">
            <TagIcon className="size-5.5" />
          </span>
          <span>
            <span className="block text-xs font-semibold uppercase tracking-eyebrow text-accent-800">Small prices</span>
            <span className="mt-2 block font-display text-2xl font-semibold text-ink">Under $5</span>
            <span className="mt-1 block text-sm text-ink-soft">
              {underFive.toLocaleString("en-US")} in-stock items, from yogurt cups to snacks and spices.
            </span>
          </span>
          <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-accent-800">
            Shop under $5
            <ArrowRightIcon className="size-4 transition-transform duration-200 ease-snappy group-hover:translate-x-0.5" />
          </span>
        </Link>
      ) : null}
    </section>
  );
}

/** A drawn gift card (decorative), so the promo never depends on a product image loading. */
function GiftCardArt({ className }: { className?: string }) {
  return (
    <div aria-hidden="true" className={cn("pointer-events-none", className)}>
      <div className="relative">
        <div className="absolute inset-0 translate-x-4 translate-y-3 rotate-10 rounded-2xl bg-accent-300 shadow-lg" />
        <div className="relative aspect-[1.586] overflow-hidden rounded-2xl bg-linear-to-br from-brand-500 via-brand-600 to-brand-800 p-4 shadow-xl ring-1 ring-white/20">
          <div className="absolute -right-10 -top-12 size-36 rounded-full bg-white/10" />
          <div className="absolute -bottom-14 -left-8 size-36 rounded-full bg-accent-300/25" />
          {/* ribbon */}
          <div className="absolute inset-y-0 right-[28%] w-3 bg-accent-300/90" />
          <div className="absolute right-[calc(28%-0.5rem)] top-[38%] size-7 rounded-full bg-accent-200 ring-4 ring-accent-300/60" />
          <LogoMark inverted className="relative size-7" />
          <p className="absolute bottom-3 left-4 font-display text-lg font-semibold tracking-[-0.03em] text-white">
            Serigan Mart
          </p>
          <p className="absolute left-4 top-[42%] text-[0.625rem] font-semibold uppercase tracking-eyebrow text-brand-100">
            Gift card
          </p>
        </div>
      </div>
    </div>
  );
}

function PromoRow() {
  return (
    <section aria-label="More from Serigan Mart" className="grid gap-4 lg:grid-cols-2 lg:gap-6">
      <div className="relative isolate flex min-h-64 flex-col justify-between gap-8 overflow-hidden rounded-3xl bg-accent-50 p-7 ring-1 ring-inset ring-accent-100 sm:p-10">
        <div
          aria-hidden="true"
          className="absolute -bottom-10 -right-10 -z-10 size-56 rounded-full bg-accent-200/60 blur-2xl"
        />
        <GiftCardArt className="absolute -bottom-5 -right-3 -z-10 w-36 -rotate-6 sm:bottom-8 sm:right-10 sm:w-56" />
        <div className="max-w-60 sm:max-w-xs">
          <p className="text-xs font-semibold uppercase tracking-eyebrow text-accent-800">Gift cards</p>
          <h2 className="mt-3 font-display text-2xl font-semibold text-ink sm:text-3xl">Give them the choice.</h2>
          <p className="mt-2 text-base text-ink-soft">Serigan Mart gift cards, good for everything in the store.</p>
        </div>
        <div>
          <ButtonLink href="/c/gift-cards" variant="outline">
            Shop gift cards
            <ArrowRightIcon className="size-4" />
          </ButtonLink>
        </div>
      </div>

      <div className="relative isolate flex min-h-64 flex-col justify-between gap-8 overflow-hidden rounded-3xl bg-inverse p-7 text-white focus-inverse sm:p-10">
        <div
          aria-hidden="true"
          className="absolute inset-0 -z-10 bg-[radial-gradient(60%_90%_at_100%_100%,rgb(125_100_239/0.45),transparent_70%)]"
        />
        <div aria-hidden="true" className="absolute right-10 top-10 hidden gap-2 sm:flex">
          <span className="grid size-12 place-items-center rounded-2xl bg-white/10 text-accent-300 ring-1 ring-inset ring-white/15">
            <ChatIcon className="size-6" />
          </span>
          <span className="grid size-12 translate-y-4 place-items-center rounded-2xl bg-white/10 text-brand-200 ring-1 ring-inset ring-white/15">
            <MicIcon className="size-6" />
          </span>
        </div>
        <div className="max-w-sm">
          <p className="text-xs font-semibold uppercase tracking-eyebrow text-accent-300">Help by text or voice</p>
          <h2 className="mt-3 font-display text-2xl font-semibold text-white sm:text-3xl">Ask Steph. Talk to Xena.</h2>
          <p className="mt-2 text-base text-brand-200">
            Steph finds products down to the diet label, checks your orders, and answers policy questions. Xena
            handles returns and refunds by voice or text, and starts a return only when you confirm.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <OpenStephButton variant="inverse" className="max-sm:w-full">
            Ask Steph
          </OpenStephButton>
          <ButtonLink
            href="/support"
            variant="ghost"
            className="text-white ring-1 ring-inset ring-white/25 hover:bg-white/10 active:bg-white/15 max-sm:w-full"
          >
            <MicIcon className="size-4.5" />
            Talk to Xena
          </ButtonLink>
        </div>
      </div>
    </section>
  );
}
