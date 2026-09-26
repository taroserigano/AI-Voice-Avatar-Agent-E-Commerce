import { ChevronRightIcon, DepartmentIcon, InfoIcon, LockIcon, ReturnIcon, type Icon } from "@/components/icons";
import { ProductReviews } from "@/components/reviews/product-reviews";
import { ProductGrid } from "@/components/shop/product-card";
import { SectionHeading } from "@/components/ui/section-heading";
import { Stars } from "@/components/ui/stars";
import { WebVitalsReporter } from "@/components/web-vitals";
import { redirectToSignIn, serverApi, unwrap } from "@/lib/api-server";
import { cn } from "@/lib/cn";
import type { CategoryOut, ProductDetail, ReviewPage } from "@ai-commerce/contracts";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { cache, type ReactNode } from "react";
import { AddToCart } from "./add-to-cart";

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

// Deduped per request: generateMetadata and the page share one product read.
const load = cache(async (id: string) => {
  if (!UUID_RE.test(id)) notFound();
  const api = await serverApi();
  const result = await api.GET("/v1/products/{product_id}", { params: { path: { product_id: id } } });
  if (result.response.status === 404) notFound();
  return unwrap(result);
});

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

/** A few other products from the same department (optional; empty on failure). */
async function loadRelated(product: ProductDetail) {
  const api = await serverApi();
  const result = await api.GET("/v1/products", {
    params: { query: { category: product.category.slug, page_size: 5 } },
  });
  return (result.data?.items ?? []).filter((p) => p.id !== product.id).slice(0, 4);
}

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const product = await load((await params).id);
  return { title: product.title, description: product.description };
}

// Keep the policy meaning exactly as before; only the presentation changed.
function returnPolicy(category: CategoryOut): { title: string; detail: string; tone: "final" | "ok" } {
  if (category.policy_class === "final_sale") {
    return { title: "Final sale", detail: "This item can't be returned.", tone: "final" };
  }
  if (category.policy_class === "inspection") {
    return { title: "30-day returns", detail: "Returnable within 30 days of delivery; refunded after inspection.", tone: "ok" };
  }
  return { title: "30-day returns", detail: "Returnable within 30 days of delivery.", tone: "ok" };
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

export default async function ProductPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [product, reviews] = await Promise.all([load(id), loadReviews(id)]);
  const related = await loadRelated(product);
  const policy = returnPolicy(product.category);

  return (
    <div className="pb-8 pt-2 sm:pt-4">
      <WebVitalsReporter route="product" />

      <nav aria-label="Breadcrumb">
        <ol className="flex items-center gap-x-1.5 text-sm text-muted">
          <li className="flex shrink-0 items-center gap-1.5">
            <Link href="/" className="inline-flex min-h-11 items-center rounded-md hover:text-ink hover:underline hover:underline-offset-4 sm:min-h-8">
              Home
            </Link>
            <ChevronRightIcon className="size-3.5 text-subtle" />
          </li>
          <li className="flex shrink-0 items-center gap-1.5">
            <Link
              href={`/c/${product.category.slug}`}
              className="inline-flex min-h-11 items-center rounded-md hover:text-ink hover:underline hover:underline-offset-4 sm:min-h-8"
            >
              {product.category.name}
            </Link>
            <ChevronRightIcon className="size-3.5 text-subtle" />
          </li>
          <li aria-current="page" className="min-w-0 truncate font-medium text-ink">
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
            <p className="text-xs font-semibold uppercase tracking-eyebrow text-brand-700">{product.brand}</p>
            <h1 className="mt-3 font-display text-3xl font-semibold tracking-tight text-ink sm:text-4xl">{product.title}</h1>
            <div className="mt-2">
              <RatingLink average={product.rating_average} count={product.rating_count} />
            </div>

            <div className="mt-5 rounded-3xl border border-line bg-raised p-5 shadow-sm sm:p-7">
              <AddToCart
                product={product}
                trust={
                  <ul className="mt-6 divide-y divide-line border-t border-line pt-5">
                    <TrustItem
                      icon={ReturnIcon}
                      title={policy.title}
                      className={policy.tone === "final" ? "bg-danger-50 text-danger-700" : undefined}
                    >
                      <span className={policy.tone === "final" ? "font-medium text-danger-700" : undefined}>{policy.detail}</span>
                    </TrustItem>
                    <TrustItem icon={LockIcon} title="Secure checkout">
                      Checkout is handled by Stripe. Larkspur never stores your card number.
                    </TrustItem>
                  </ul>
                }
              />
            </div>
            <p className="mt-4 flex items-start gap-2 px-1 text-xs text-muted">
              <InfoIcon className="mt-px size-3.5 shrink-0 text-brand-600" />
              <span>Sandbox store: checkout uses Stripe test mode. Nothing ships and no real money moves.</span>
            </p>
          </div>
        </div>

        {/* About */}
        <section aria-labelledby="about" className="lg:col-span-7">
          <div className="rounded-3xl border border-line bg-raised p-6 shadow-xs sm:p-8">
            <h2 id="about" className="font-display text-xl font-semibold text-ink sm:text-2xl">
              About this item
            </h2>
            <p className="mt-4 max-w-prose text-base leading-relaxed text-ink-soft">{product.description}</p>
            <dl className="mt-6 grid gap-x-6 gap-y-4 border-t border-line pt-6 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-muted">Brand</dt>
                <dd className="mt-0.5 font-medium text-ink">{product.brand}</dd>
              </div>
              <div>
                <dt className="text-muted">Department</dt>
                <dd className="mt-0.5">
                  <Link
                    href={`/c/${product.category.slug}`}
                    className="font-medium text-brand-700 underline decoration-brand-300 underline-offset-4 hover:decoration-brand-700"
                  >
                    {product.category.name}
                  </Link>
                </dd>
              </div>
              {product.variants.length > 1 ? (
                <div>
                  <dt className="text-muted">Options</dt>
                  <dd className="mt-0.5 font-medium text-ink">{product.variants.map((v) => v.name).join(", ")}</dd>
                </div>
              ) : null}
            </dl>
          </div>
        </section>
      </div>

      <div className="mt-20 sm:mt-28">
        <ProductReviews productId={product.id} productTitle={product.title} initialData={reviews} />
      </div>

      {related.length > 0 ? (
        <section aria-labelledby="related" className="mt-20 sm:mt-28">
          <SectionHeading
            id="related"
            eyebrow="Keep exploring"
            title={`More from ${product.category.name}`}
            action={{ href: `/c/${product.category.slug}`, label: "See all", srLabel: product.category.name }}
          />
          <div className="mt-6 sm:mt-8">
            <ProductGrid products={related} label={`More from ${product.category.name}`} />
          </div>
        </section>
      ) : null}
    </div>
  );
}
