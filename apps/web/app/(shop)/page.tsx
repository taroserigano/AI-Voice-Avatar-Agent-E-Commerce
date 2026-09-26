import {
  ArrowRightIcon,
  ChatIcon,
  DepartmentIcon,
  LockIcon,
  MicIcon,
  ReturnIcon,
  SearchIcon,
  StarIcon,
  type Icon,
} from "@/components/icons";
import { RecentlyViewed } from "@/components/activity/recently-viewed";
import { departmentTint } from "@/components/shop/department-style";
import { ProductGrid } from "@/components/shop/product-card";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button";
import { SectionHeading } from "@/components/ui/section-heading";
import { RatingBadge } from "@/components/ui/stars";
import { WebVitalsReporter } from "@/components/web-vitals";
import { recentlyViewed } from "@/lib/activity";
import { getMe, serverApi, unwrap } from "@/lib/api-server";
import { cn } from "@/lib/cn";
import type { CategoryOut, ProductSummary } from "@ai-commerce/contracts";
import Link from "next/link";

const POPULAR_SEARCHES = ["headphones", "french press", "rain boots", "yoga mat"];

/** Departments whose best-rated product fronts the hero collage, in order. */
const HERO_DEPARTMENTS = ["electronics", "home-kitchen", "clothing-shoes"];

const VALUE_PROPS: { icon: Icon; title: string; body: string; soon?: boolean }[] = [
  {
    icon: ReturnIcon,
    title: "30-day returns",
    body: "Sandbox policy, counted from delivery. Online returns are on the way.",
    soon: true,
  },
  {
    icon: LockIcon,
    title: "Secure checkout",
    body: "Stripe's hosted page in test mode. Card details never reach our servers.",
    soon: true,
  },
  {
    icon: ChatIcon,
    title: "Help by text or voice",
    body: "A shopping assistant for products, orders, and returns.",
    soon: true,
  },
  {
    icon: StarIcon,
    title: "Honest ratings",
    body: "Reviews from shoppers, with sample reviews clearly labeled.",
  },
];

export default async function HomePage() {
  const user = await getMe();
  const api = await serverApi();
  const [categories, featured, rated, viewed] = await Promise.all([
    api.GET("/v1/categories").then(unwrap),
    api.GET("/v1/products", { params: { query: { in_stock: true, sort: "newest", page_size: 8 } } }).then(unwrap),
    // One ranked read of the catalog: the first 8 are "Top rated", and the best product in each
    // department fronts its tile. Facet counts give the per-department totals.
    api.GET("/v1/products", { params: { query: { sort: "top_rated", page_size: 60 } } }).then(unwrap),
    // Optional: a failed activity read just hides "Recently viewed".
    api
      .GET("/v1/activity", { params: { query: { type: ["viewed_product"], limit: 12 } } })
      .then((r) => recentlyViewed(r.data ?? [], 8))
      .catch(() => []),
  ]);

  const topRated = rated.items.slice(0, 8);
  const bestInDepartment = new Map<string, ProductSummary>();
  for (const p of rated.items) if (!bestInDepartment.has(p.category.slug)) bestInDepartment.set(p.category.slug, p);
  const counts = new Map(rated.facets.categories.map((f) => [f.value, f.count]));
  const heroPicks = HERO_DEPARTMENTS.map((slug) => bestInDepartment.get(slug)).filter(
    (p): p is ProductSummary => p !== undefined,
  );
  const firstName = user.display_name.split(" ")[0] ?? user.display_name;

  return (
    <div className="space-y-16 sm:space-y-24">
      <WebVitalsReporter route="home" />

      <Hero firstName={firstName} picks={heroPicks} />

      <section aria-label="Why shop with Serigan Mart" className="-mt-8 sm:-mt-14">
        <ul className="grid gap-px overflow-hidden rounded-3xl border border-line bg-line shadow-xs sm:grid-cols-2 lg:grid-cols-4">
          {VALUE_PROPS.map(({ icon: ItemIcon, title, body, soon }) => (
            <li key={title} className="flex gap-4 bg-raised p-5 sm:block sm:p-6">
              <div className="flex shrink-0 items-start justify-between gap-3">
                <span className="grid size-11 place-items-center rounded-2xl bg-brand-50 text-brand-700 ring-1 ring-inset ring-brand-100">
                  <ItemIcon className="size-5.5" />
                </span>
                {soon ? <Badge tone="accent" className="hidden sm:inline-flex">Coming soon</Badge> : null}
              </div>
              <div className="min-w-0 sm:mt-4">
                <p className="flex flex-wrap items-center gap-x-2 gap-y-1 text-[0.9375rem] font-semibold text-ink">
                  {title}
                  {soon ? <Badge tone="accent" className="sm:hidden">Coming soon</Badge> : null}
                </p>
                <p className="mt-1 text-sm leading-relaxed text-muted">{body}</p>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <RecentlyViewed products={viewed} />

      <section aria-labelledby="departments">
        <SectionHeading
          id="departments"
          eyebrow="Browse"
          title="Shop by department"
          description="Everything for home, work, play, and the great outdoors."
          action={{ href: "/sitemap", label: "Site map", srLabel: "with every product" }}
        />
        <ul className="mt-6 grid auto-rows-[10.5rem] grid-flow-dense grid-cols-2 gap-3 sm:mt-8 sm:auto-rows-[12rem] sm:grid-cols-3 sm:gap-4 lg:grid-cols-4">
          {categories.map((c, i) => (
            <DepartmentTile
              key={c.slug}
              category={c}
              product={bestInDepartment.get(c.slug)}
              count={counts.get(c.slug)}
              featured={i === 0}
            />
          ))}
        </ul>
      </section>

      <section aria-labelledby="featured">
        <SectionHeading
          id="featured"
          eyebrow="Just in"
          title="New and in stock"
          description="Fresh arrivals across every department, ready to order."
          action={{ href: "/search?sort=newest&in_stock=true", label: "See all", srLabel: "new products" }}
        />
        <div className="mt-6 sm:mt-8">
          <ProductGrid products={featured.items} label="New and in stock" />
        </div>
      </section>

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
    </div>
  );
}

function Hero({ firstName, picks }: { firstName: string; picks: ProductSummary[] }) {
  const [a, b, c] = picks;
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
      <div className="grid items-center gap-10 px-6 py-12 sm:px-12 sm:py-16 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)] lg:gap-6 lg:py-16 lg:pl-16 lg:pr-10">
        <div>
          <p className="inline-flex animate-fade-up items-center gap-2 rounded-full bg-white/10 py-1 pl-1.5 pr-3.5 text-xs font-semibold uppercase tracking-eyebrow text-accent-300 ring-1 ring-inset ring-white/15 backdrop-blur-sm">
            <span aria-hidden="true" className="relative flex size-5 items-center justify-center rounded-full bg-accent-400/20">
              <span className="size-2 rounded-full bg-accent-300" />
            </span>
            Welcome back, {firstName}
          </p>
          <h1
            id="hero-title"
            className="mt-6 max-w-xl animate-fade-up font-display text-display font-semibold tracking-[-0.035em] text-white animation-delay-80"
          >
            Everyday essentials,{" "}
            <span className="bg-linear-to-r from-brand-200 via-white to-accent-200 bg-clip-text text-transparent">
              beautifully easy.
            </span>
          </h1>
          <p className="mt-6 max-w-lg animate-fade-up text-lg leading-relaxed text-brand-200 animation-delay-160">
            Electronics, home and kitchen, clothing, toys, and more in one calm, simple store. Online returns and
            the shopping assistant are coming next.
          </p>
          <div className="mt-8 flex animate-fade-up flex-wrap gap-3 animation-delay-240">
            <ButtonLink href="/search" variant="inverse" size="lg" className="max-sm:w-full">
              Start shopping
              <ArrowRightIcon className="size-4.5" />
            </ButtonLink>
            <ButtonLink
              href="/search?sort=top_rated"
              variant="ghost"
              size="lg"
              className="text-white ring-1 ring-inset ring-white/25 hover:bg-white/10 active:bg-white/15 max-sm:w-full"
            >
              See top rated
            </ButtonLink>
          </div>
          <div className="mt-10 animate-fade-up animation-delay-320">
            <p id="popular-searches" className="text-xs font-semibold uppercase tracking-eyebrow text-brand-300">
              Popular searches
            </p>
            <ul aria-labelledby="popular-searches" className="mt-3 flex flex-wrap gap-2">
              {POPULAR_SEARCHES.map((q) => (
                <li key={q}>
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

        {a ? (
          <div aria-hidden="true" className="relative mx-auto aspect-[1.08] w-full max-w-md sm:max-w-lg lg:max-w-none">
            <div className="absolute inset-[12%] rounded-full bg-brand-400/30 blur-3xl" />
            <HeroTile product={a} className="left-[3%] top-[4%] w-[54%] -rotate-6 animate-fade-up animation-delay-160" />
            {b ? (
              <HeroTile product={b} className="right-[2%] top-[14%] w-[42%] rotate-[5deg] animate-fade-up animation-delay-240" />
            ) : null}
            {c ? (
              <HeroTile product={c} className="bottom-[2%] left-[28%] w-[38%] -rotate-2 animate-fade-up animation-delay-320" />
            ) : null}
            <div className="absolute bottom-[14%] right-0 flex max-w-[15rem] animate-fade-up items-center gap-3 rounded-2xl bg-raised/95 p-2.5 pr-4 text-ink shadow-2xl ring-1 ring-black/5 backdrop-blur animation-delay-400 max-sm:scale-90 max-sm:origin-bottom-right">
              {/* eslint-disable-next-line @next/next/no-img-element -- local SVG illustrations */}
              <img src={a.image_path} alt="" width={44} height={44} className="size-11 rounded-xl" />
              <div className="min-w-0">
                <p className="truncate text-xs font-semibold text-ink">{a.title}</p>
                <RatingBadge average={a.rating_average} count={a.rating_count} className="mt-0.5" />
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </section>
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
  product,
  count,
  featured,
}: {
  category: CategoryOut;
  product?: ProductSummary;
  count?: number;
  featured: boolean;
}) {
  const tint = departmentTint(category.slug);
  return (
    <li className={cn(featured && "col-span-2 row-span-2")}>
      <Link
        href={`/c/${category.slug}`}
        className={cn(
          "group relative flex h-full flex-col items-start justify-end overflow-hidden rounded-3xl ring-1 ring-inset shadow-xs transition-[box-shadow,transform] duration-300 ease-smooth hover:-translate-y-1 hover:shadow-lg motion-reduce:hover:translate-y-0",
          tint.surface,
          tint.ring,
        )}
      >
        {product ? (
          // eslint-disable-next-line @next/next/no-img-element -- local SVG illustrations
          <img
            src={product.image_path}
            alt=""
            width={640}
            height={640}
            loading="lazy"
            className={cn(
              "absolute inset-0 size-full object-cover transition-transform duration-700 ease-smooth group-hover:scale-[1.06] motion-reduce:group-hover:scale-100",
              "object-[50%_22%]",
            )}
          />
        ) : (
          <DepartmentIcon
            slug={category.slug}
            className={cn("absolute right-6 top-6 size-16 opacity-60", tint.text)}
          />
        )}
        <span className="pointer-events-none absolute inset-x-0 bottom-0 h-2/3 bg-linear-to-t from-black/10 to-transparent" />
        <span
          aria-hidden="true"
          className="absolute right-3 top-3 grid size-9 translate-y-1 place-items-center rounded-full bg-raised/95 text-ink opacity-0 shadow-sm transition-[opacity,transform] duration-300 ease-smooth group-hover:translate-y-0 group-hover:opacity-100 group-focus-visible:translate-y-0 group-focus-visible:opacity-100"
        >
          <ArrowRightIcon className="size-4" />
        </span>
        <span
          className={cn(
            "relative mt-auto m-2.5 flex items-center gap-2.5 rounded-2xl bg-raised/90 p-2 pr-3 shadow-sm ring-1 ring-black/5 backdrop-blur-md sm:m-3",
            featured && "sm:m-4 sm:gap-3 sm:p-2.5 sm:pr-4",
          )}
        >
          <span className={cn("grid size-9 shrink-0 place-items-center rounded-xl", tint.tile, featured && "sm:size-11")}>
            <DepartmentIcon slug={category.slug} className={cn("size-5", featured && "sm:size-6")} />
          </span>
          <span className="min-w-0">
            <span
              className={cn(
                "block text-sm font-semibold leading-tight text-ink",
                featured && "sm:font-display sm:text-lg",
              )}
            >
              {category.name}
            </span>
            {count ? (
              <span className="mt-0.5 block text-xs text-muted">
                {count} {count === 1 ? "product" : "products"}
              </span>
            ) : null}
          </span>
        </span>
      </Link>
    </li>
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
        {/* eslint-disable-next-line @next/next/no-img-element -- local SVG illustrations */}
        <img
          src="/images/products/serigan-mart-gift-card.svg"
          alt=""
          width={640}
          height={640}
          loading="lazy"
          className="pointer-events-none absolute -bottom-8 right-6 -z-10 w-36 rotate-[8deg] rounded-[1.75rem] shadow-xl ring-4 ring-white/90 sm:right-10 sm:w-52"
        />
        <div className="max-w-xs">
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
          <p className="text-xs font-semibold uppercase tracking-eyebrow text-accent-300">Coming soon</p>
          <h2 className="mt-3 font-display text-2xl font-semibold text-white sm:text-3xl">Help by text or voice.</h2>
          <p className="mt-2 text-base text-brand-200">
            Ask the Serigan Mart assistant about products, orders, and returns, typing or talking. It&apos;s in the works.
          </p>
        </div>
        <p className="text-sm text-brand-300">Until then, your orders live in one place.</p>
        <div className="-mt-6">
          <ButtonLink href="/orders" variant="inverse">
            Orders &amp; returns
          </ButtonLink>
        </div>
      </div>
    </section>
  );
}
