import { StarFilledIcon } from "@/components/icons";
import { Badge } from "@/components/ui/badge";
import { RatingBadge } from "@/components/ui/stars";
import { cn } from "@/lib/cn";
import { formatMoney } from "@/lib/format";
import type { ProductSummary } from "@ai-commerce/contracts";
import Link from "next/link";

/** A shopper favourite: a high average from more than a couple of reviews. */
function isTopRated(p: ProductSummary) {
  return p.rating_average != null && p.rating_average >= 4.7 && p.rating_count >= 3;
}

/**
 * Whole-card link. The accessible name is the product title; brand, rating, price and stock are
 * read as the description. `idPrefix` keeps ids unique when a product appears in two grids.
 */
export function ProductCard({
  product,
  priority = false,
  idPrefix = "product",
  rank,
}: {
  product: ProductSummary;
  priority?: boolean;
  idPrefix?: string;
  /** Position in a ranked list ("#1"), shown instead of the "Top rated" badge. */
  rank?: number;
}) {
  const base = `${idPrefix}-${product.id}`;
  const multiVariant = product.variant_count > 1;
  return (
    <li className="group relative">
      <Link
        href={`/products/${product.id}`}
        aria-labelledby={`${base}-title`}
        aria-describedby={`${base}-meta`}
        className="-m-2 flex h-[calc(100%+1rem)] flex-col rounded-3xl p-2 transition-[background-color,box-shadow,transform] duration-300 ease-smooth hover:-translate-y-1 hover:bg-raised hover:shadow-lg motion-reduce:hover:translate-y-0"
      >
        <div className="relative shrink-0 overflow-hidden rounded-2xl bg-sunken ring-1 ring-inset ring-line/60">
          {/* eslint-disable-next-line @next/next/no-img-element -- local SVG illustrations */}
          <img
            src={product.image_path}
            alt=""
            width={640}
            height={640}
            loading={priority ? "eager" : "lazy"}
            decoding="async"
            className={cn(
              "aspect-square w-full object-cover transition-transform duration-500 ease-smooth group-hover:scale-[1.05] motion-reduce:group-hover:scale-100",
              !product.in_stock && "opacity-60 grayscale-35",
            )}
          />
          <div className="absolute inset-x-2.5 top-2.5 flex flex-wrap gap-1.5">
            {!product.in_stock ? (
              <Badge tone="neutral" dot className="bg-raised/95 shadow-xs backdrop-blur">
                Out of stock
              </Badge>
            ) : rank ? (
              <span className="grid h-7 min-w-7 place-items-center rounded-full bg-ink px-2 font-display text-sm font-semibold tabular-nums text-white shadow-sm">
                <span className="sr-only">Number </span>
                {rank}
              </span>
            ) : isTopRated(product) ? (
              <Badge tone="accent" className="bg-raised/95 shadow-xs backdrop-blur">
                <StarFilledIcon className="text-star" />
                Top rated
              </Badge>
            ) : null}
          </div>
        </div>
        <div className="flex flex-1 flex-col px-1.5 pb-2 pt-3.5">
          <h3
            id={`${base}-title`}
            className="order-2 line-clamp-2 font-sans text-[0.9375rem] font-medium leading-snug text-ink transition-colors duration-150 group-hover:text-brand-700"
          >
            {product.title}
          </h3>
          <div id={`${base}-meta`} className="order-1 contents">
            <p className="order-1 mb-1 truncate text-xs font-semibold uppercase tracking-eyebrow text-muted">
              {product.brand}
            </p>
            <RatingBadge
              average={product.rating_average}
              count={product.rating_count}
              className="order-3 mt-1.5"
            />
            <div className="order-4 mt-auto flex flex-wrap items-center justify-between gap-x-2 gap-y-0.5 pt-3">
              <p className="whitespace-nowrap tabular-nums text-ink">
                {multiVariant ? <span className="mr-1 text-xs font-medium text-muted">From</span> : null}
                <span className="text-lg font-semibold">{formatMoney(product.price_minor, product.currency)}</span>
              </p>
              <p
                className={cn(
                  "inline-flex items-center gap-1.5 whitespace-nowrap text-xs font-medium",
                  product.in_stock ? "text-success-700" : "text-danger-700",
                )}
              >
                <span
                  aria-hidden="true"
                  className={cn("size-1.5 rounded-full", product.in_stock ? "bg-success-600" : "bg-danger-600")}
                />
                {product.in_stock ? "In stock" : "Out of stock"}
              </p>
            </div>
          </div>
        </div>
      </Link>
    </li>
  );
}

function slug(label: string) {
  return label
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 40);
}

export function ProductGrid({
  products,
  label,
  className,
  ranked = false,
}: {
  products: ProductSummary[];
  label: string;
  className?: string;
  /** Number the cards (#1, #2…) for ranked lists such as "Top rated". */
  ranked?: boolean;
}) {
  const idPrefix = `pg-${slug(label) || "grid"}`;
  return (
    <ul
      aria-label={label}
      className={cn("grid grid-cols-2 gap-x-4 gap-y-8 sm:grid-cols-3 lg:grid-cols-4 lg:gap-x-6 lg:gap-y-10", className)}
    >
      {products.map((p, i) => (
        <ProductCard key={p.id} product={p} priority={i < 4} idPrefix={idPrefix} rank={ranked ? i + 1 : undefined} />
      ))}
    </ul>
  );
}
