import { ChevronRightIcon, DepartmentIcon, InfoIcon, ReturnIcon, type Icon } from "@/components/icons";
import { DeliveryInfo } from "@/components/product/delivery-info";
import { ProductReviews } from "@/components/reviews/product-reviews";
import { ProductGrid, TagBadges } from "@/components/shop/product-card";
import { SectionHeading } from "@/components/ui/section-heading";
import { Stars } from "@/components/ui/stars";
import { WebVitalsReporter } from "@/components/web-vitals";
import { redirectToSignIn, serverApi } from "@/lib/api-server";
import { cn } from "@/lib/cn";
import type { CategoryOut, ProductDetail, ProductSummary, ReviewPage } from "@ai-commerce/contracts";
import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";
import { AddToCart } from "./add-to-cart";
import { loadProduct, UUID_RE } from "./load-product";
import { ProductFacts } from "./product-facts";

// The layout already gated the route on this read (a real 404 for unknown ids); it's deduped per
// request, so generateMetadata and the page reuse it.
const load = loadProduct;

/** First page of reviews for a fast first paint. A failure here shouldn't take down the page. */
async function loadReviews(id: string): Promise<ReviewPage | undefined> {
  if (!UUID_RE.test(id)) return undefined;
  const api = await serverApi();
  const result = await api.GET("/v1/products/{product_id}/reviews", {
    params: { path: { product_id: id }, query: { sort: "newest", page: 1, page_size: 10 } },
  });
  if (result.response.status === 401) return redirectToSignIn();
  return result.data;
}

/** "usb-c-charger" -> "Usb c charger": a last resort when the API has no label. */
function humanize(slug: string) {
  const words = slug.replace(/-/g, " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}

/** "USB-C charger" -> "USB-C chargers", "Headphones" -> "headphones", "TV" -> "TVs". */
function pluralType(label: string): string {
  const [firstWord = ""] = label.split(" ");
  // Keep acronyms ("TV", "USB-C", "SSD") as written; lowercase ordinary words mid-sentence.
  const cased = /[A-Z].*[A-Z]/.test(firstWord) ? label : label.charAt(0).toLowerCase() + label.slice(1);
  if (/s$/i.test(cased)) return cased;
  if (/(x|ch|sh)$/i.test(cased)) return `${cased}es`;
  if (/[^aeiou]y$/i.test(cased)) return `${cased.slice(0, -1)}ies`;
  return `${cased}s`;
}

type Related = { typeLabel: string; similar: ProductSummary[]; fromBrand: ProductSummary[] };

/**
 * "Similar <type>" (same product type in this department, featured order) and "More from
 * <brand>". Optional: empty on failure. Also resolves the shopper-facing type label.
 */
async function loadRelated(product: ProductDetail): Promise<Related> {
  const api = await serverApi();
  const [sameType, sameBrand] = await Promise.all([
    api
      .GET("/v1/products", {
        params: { query: { category: product.category.slug, product_type: [product.product_type], page_size: 5 } },
      })
      .then((r) => r.data)
      .catch(() => undefined),
    api
      .GET("/v1/products", { params: { query: { brand: [product.brand], page_size: 9 } } })
      .then((r) => r.data)
      .catch(() => undefined),
  ]);
  const similar = (sameType?.items ?? []).filter((p) => p.id !== product.id).slice(0, 4);
  const shown = new Set([product.id, ...similar.map((p) => p.id)]);
  const fromBrand = (sameBrand?.items ?? []).filter((p) => !shown.has(p.id)).slice(0, 4);
  const typeLabel =
    product.type_label ||
    sameType?.items.find((p) => p.type_label)?.type_label ||
    sameType?.facets.product_types.find((f) => f.value === product.product_type)?.label ||
    humanize(product.product_type);
  return { typeLabel, similar, fromBrand };
}

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const product = await load((await params).id);
  return { title: product.title, description: product.description };
}

// Keep the policy meaning exactly as before; only the presentation changed.
// `section` is the matching part of the return policy (/returns-policy#…).
function returnPolicy(category: CategoryOut): { title: string; detail: string; tone: "final" | "ok"; section: string } {
  if (category.policy_class === "final_sale") {
    return { title: "Final sale", detail: "This item can't be returned.", tone: "final", section: "rr-3-1" };
  }
  if (category.policy_class === "inspection") {
    return {
      title: "30-day returns",
      detail: "Returnable within 30 days of delivery; refunded after inspection.",
      tone: "ok",
      section: "rr-11-3",
    };
  }
  if (category.policy_class === "perishable") {
    return {
      title: "Freshness guarantee",
      detail: "Fresh food isn't sent back. If it arrives damaged or spoiled, tell us within 7 days of delivery for a refund.",
      tone: "ok",
      section: "rr-2-2",
    };
  }
  return { title: "30-day returns", detail: "Returnable within 30 days of delivery. Return shipping is free.", tone: "ok", section: "rr-2-1" };
}

function TrustItem({ icon: IconCmp, title, children, className }: { icon: Icon; title: string; children: ReactNode; className?: string }) {
  return (
    <li className="flex gap-3.5 py-4 first:pt-0 last:pb-0">
      <span className={cn("grid size-10 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-700", className)}>
        <IconCmp className="size-5" />
      </span>
      <div className="min-w-0 text-sm">
        <p className="font-semibold text-ink">{title}</p>
        <p className="mt-0.5 text-muted">{children}</p>
      </div>
    </li>
  );
}

function RatingLink({ average, count }: { average: number | null; count: number }) {
  if (!count || average == null) {
    return (
      <a
        href="#reviews"
        className="group inline-flex min-h-11 items-center gap-2 text-sm font-medium text-brand-700 underline decoration-brand-300 underline-offset-4 hover:decoration-brand-700"
      >
        <Stars rating={0} size="md" label="" />
        No reviews yet — be the first
      </a>
    );
  }
  const reviews = count === 1 ? "review" : "reviews";
  return (
    <a
      href="#reviews"
      className="group -mx-2 inline-flex min-h-11 items-center gap-2.5 rounded-full px-2 text-sm transition-colors hover:bg-sunken"
    >
      <Stars rating={average} size="md" label="" />
      <span className="font-semibold tabular-nums text-ink">{average.toFixed(1)}</span>
      <span aria-hidden="true" className="text-line-strong">
        ·
      </span>
      <span className="font-medium text-brand-700 underline decoration-brand-300 underline-offset-4 group-hover:decoration-brand-700">
        {count.toLocaleString("en-US")} {reviews}
      </span>
      <span className="sr-only">, rated {average.toFixed(1)} out of 5. Go to ratings and reviews</span>
    </a>
  );
}

const crumbLink =
  "inline-flex min-h-11 items-center rounded-md hover:text-ink hover:underline hover:underline-offset-4 sm:min-h-8";

export default async function ProductPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const productP = load(id);
  // Related products need the product, but not the reviews: fetch them alongside the reviews.
  const [product, reviews, related] = await Promise.all([productP, loadReviews(id), productP.then(loadRelated)]);
  const policy = returnPolicy(product.category);
  const typeHref = `/c/${product.category.slug}?product_type=${encodeURIComponent(product.product_type)}`;
  const brandHref = `/search?brand=${encodeURIComponent(product.brand)}`;
  const similarTitle = `Similar ${pluralType(related.typeLabel)}`;
  const brandTitle = `More from ${product.brand}`;

  return (
    // Room at the bottom on phones for the sticky Add to cart bar.
    <div className="pb-28 pt-2 sm:pt-4 lg:pb-8">
      <WebVitalsReporter route="product" />

      <nav aria-label="Breadcrumb">
        <ol className="flex items-center gap-x-1.5 text-sm text-muted">
          <li className="flex shrink-0 items-center gap-1.5">
            <Link href="/" className={crumbLink}>
              Home
            </Link>
            <ChevronRightIcon className="size-3.5 text-subtle" />
          </li>
          <li className="flex min-w-0 shrink items-center gap-1.5">
            <Link href={`/c/${product.category.slug}`} className={cn(crumbLink, "truncate")}>
              {product.category.name}
            </Link>
            <ChevronRightIcon className="size-3.5 shrink-0 text-subtle" />
          </li>
          <li className="flex min-w-0 shrink items-center gap-1.5">
            <Link href={typeHref} className={cn(crumbLink, "truncate")}>
              {related.typeLabel}
            </Link>
            <ChevronRightIcon className="size-3.5 shrink-0 text-subtle max-sm:hidden" />
          </li>
          <li aria-current="page" className="min-w-0 truncate font-medium text-ink max-sm:sr-only">
            {product.title}
          </li>
        </ol>
      </nav>

      <div className="mt-4 grid gap-8 sm:mt-6 lg:grid-cols-12 lg:gap-x-12 xl:gap-x-16">
        {/* Gallery */}
        <div className="lg:col-span-7">
          <figure className="group relative overflow-hidden rounded-3xl bg-sunken shadow-xs ring-1 ring-line">
            {/* eslint-disable-next-line @next/next/no-img-element -- local SVG illustrations */}
            <img
              src={product.image_path}
              alt={`${product.title} (illustration)`}
              width={640}
              height={640}
              fetchPriority="high"
              className="aspect-square w-full object-cover transition-transform duration-700 ease-smooth group-hover:scale-[1.04] motion-reduce:group-hover:scale-100"
            />
            <figcaption className="pointer-events-none absolute left-4 top-4 inline-flex items-center gap-1.5 rounded-full bg-raised/85 px-3 py-1.5 text-xs font-semibold text-ink-soft shadow-sm backdrop-blur-md">
              <DepartmentIcon slug={product.category.slug} className="size-3.5 text-brand-600" />
              {product.category.name}
            </figcaption>
          </figure>
        </div>

        {/* Buy box: sticky beside the gallery on large screens */}
        <div className="lg:col-span-5 lg:row-span-2">
          <div className="lg:sticky lg:top-36">
            <Link
              href={brandHref}
              className="inline-flex min-h-6 items-center text-xs font-semibold uppercase tracking-eyebrow text-brand-700 hover:text-brand-900 hover:underline hover:underline-offset-4"
            >
              <span className="sr-only">Shop more from </span>
              {product.brand}
            </Link>
            <h1 className="mt-2 font-display text-3xl font-semibold tracking-tight text-ink sm:text-4xl">{product.title}</h1>
            <div className="mt-2">
              <RatingLink average={product.rating_average} count={product.rating_count} />
            </div>
            <TagBadges
              tags={product.tags}
              className="mt-3 gap-1.5"
              hrefFor={(t) => `/c/${product.category.slug}?tag=${encodeURIComponent(t.value)}`}
            />

            <div className="mt-5 rounded-3xl border border-line bg-raised p-5 shadow-sm sm:p-7">
              <AddToCart
                product={product}
                trust={
                  <ul className="mt-6 divide-y divide-line border-t border-line pt-5">
                    <DeliveryInfo />
                    <TrustItem
                      icon={ReturnIcon}
                      title={policy.title}
                      className={policy.tone === "final" ? "bg-danger-50 text-danger-700" : undefined}
                    >
                      <span className={policy.tone === "final" ? "font-medium text-danger-700" : undefined}>{policy.detail}</span>{" "}
                      <Link
                        href={`/returns-policy#${policy.section}`}
                        className="whitespace-nowrap font-medium text-brand-700 underline decoration-brand-300 underline-offset-4 hover:decoration-brand-700"
                      >
                        Return policy
                      </Link>
                    </TrustItem>
                  </ul>
                }
              />
            </div>
            <p className="mt-4 flex items-start gap-2 px-1 text-xs text-muted">
              <InfoIcon className="mt-px size-3.5 shrink-0 text-brand-600" />
              <span>Demo store: checkout isn&apos;t open yet, so nothing ships and no money moves.</span>
            </p>
          </div>
        </div>

        {/* About */}
        <section aria-labelledby="about" className="lg:col-span-7">
          <div className="rounded-3xl border border-line bg-raised p-6 shadow-xs sm:p-8">
            <h2 id="about" className="font-display text-xl font-semibold text-ink sm:text-2xl">
              About this item
            </h2>
            <section aria-labelledby="details" className="mt-5">
              <h3 id="details" className="text-lg font-semibold text-ink">
                Details
              </h3>
              <p className="mt-2 max-w-prose text-base leading-relaxed text-ink-soft">{product.description}</p>
            </section>
            <ProductFacts product={product} typeLabel={related.typeLabel} />
          </div>
        </section>
      </div>

      <div className="mt-20 sm:mt-28">
        <ProductReviews productId={product.id} productTitle={product.title} initialData={reviews} />
      </div>

      {related.similar.length > 0 ? (
        <section aria-labelledby="similar" className="mt-20 sm:mt-28">
          <SectionHeading
            id="similar"
            eyebrow="Compare"
            title={similarTitle}
            action={{ href: typeHref, label: "See all", srLabel: pluralType(related.typeLabel) }}
          />
          <div className="mt-6 sm:mt-8">
            <ProductGrid products={related.similar} label={similarTitle} />
          </div>
        </section>
      ) : null}

      {related.fromBrand.length > 0 ? (
        <section aria-labelledby="from-brand" className="mt-16 sm:mt-20">
          <SectionHeading
            id="from-brand"
            eyebrow="Same brand"
            title={brandTitle}
            action={{ href: brandHref, label: "See all", srLabel: `from ${product.brand}` }}
          />
          <div className="mt-6 sm:mt-8">
            <ProductGrid products={related.fromBrand} label={brandTitle} />
          </div>
        </section>
      ) : null}
    </div>
  );
}
