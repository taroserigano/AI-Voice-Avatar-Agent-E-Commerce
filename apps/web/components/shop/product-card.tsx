import { ArrowRightIcon, StarFilledIcon } from "@/components/icons";
import { QuickAdd } from "@/components/product/quick-add";
import { Badge, badgeClasses } from "@/components/ui/badge";
import { buttonClasses } from "@/components/ui/button";
import { RatingBadge } from "@/components/ui/stars";
import { cn } from "@/lib/cn";
import { formatMoney } from "@/lib/format";
import { canQuickAdd, displayTags, isTopRated, meaningfulSize, needsOptionChoice } from "@/lib/product-display";
import type { ProductSummary, TagOut } from "@ai-commerce/contracts";
import Link from "next/link";

/**
 * Feature tags such as "Organic" or "Gluten-free", as small success-toned chips. With `hrefFor`
 * each chip links somewhere (e.g. the department filtered by that tag); without it they're text.
 * Tags another tag implies ("Low sugar" beside "Sugar free") are left out, and catalog-wide
 * ones (Kosher, Gluten free) come last, so a short `max` keeps the telling ones.
 */
export function TagBadges({
  tags,
  max,
  className,
  hrefFor,
  label = "Features",
}: {
  tags: TagOut[];
  max?: number;
  className?: string;
  hrefFor?: (tag: TagOut) => string;
  label?: string;
}) {
  const shown = displayTags(tags, max);
  if (shown.length === 0) return null;
  return (
    <ul aria-label={label} className={cn("flex flex-wrap gap-1", className)}>
      {shown.map((t) => (
        <li key={t.value}>
          {hrefFor ? (
            <Link
              href={hrefFor(t)}
              className={badgeClasses(
                "success",
                "sm",
                "relative transition-colors duration-150 before:absolute before:-inset-1.5 before:content-[''] hover:bg-success-100 hover:underline hover:underline-offset-2",
              )}
            >
              {t.label}
            </Link>
          ) : (
            <Badge tone="success">{t.label}</Badge>
          )}
        </li>
      ))}
    </ul>
  );
}

/**
 * Product card. The title is the one link (stretched over the whole card with ::after), so the
 * card is clickable everywhere without nesting the quick-add buttons inside a link. Brand, size,
 * rating, price and stock are the link's description. `idPrefix` keeps ids unique when a product
 * appears in two grids.
 */
export function ProductCard({
  product,
  priority = false,
  idPrefix = "product",
  rank,
  quickAdd = true,
}: {
  product: ProductSummary;
  priority?: boolean;
  idPrefix?: string;
  /** Position in a ranked list ("#1"), shown instead of the "Top rated" badge. */
  rank?: number;
  /**
   * Show the Add button / stepper, or "Choose options" for products sold in sizes or colors
   * (quick add never picks a shoe size or a color for the shopper).
   */
  quickAdd?: boolean;
}) {
  const base = `${idPrefix}-${product.id}`;
  const multiVariant = product.variant_count > 1;
  const choose = quickAdd && product.in_stock && needsOptionChoice(product);
  const canAdd = quickAdd && canQuickAdd(product);
  // The size line names the pack Add would add; a product sold in sizes has no one size.
  const size = needsOptionChoice(product) ? null : meaningfulSize(product.default_variant_name);
  // "From" the lowest price when there's a choice to make; else the price of what Add adds.
  const price = needsOptionChoice(product) ? product.price_minor : (product.default_price_minor ?? product.price_minor);
  return (
    <li className="group">
      <div className="relative -m-2 flex h-[calc(100%+1rem)] flex-col rounded-3xl p-2 transition-[background-color,box-shadow,transform] duration-300 ease-smooth has-[a:focus-visible]:outline-2 has-[a:focus-visible]:outline-offset-2 has-[a:focus-visible]:outline-focus hover:-translate-y-1 hover:bg-raised hover:shadow-lg motion-reduce:hover:translate-y-0">
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
        <div className="flex flex-1 flex-col px-1.5 pb-1 pt-3.5">
          <p id={`${base}-brand`} className="mb-1 truncate text-xs font-semibold uppercase tracking-eyebrow text-muted">
            {product.brand}
          </p>
          <h3 className="line-clamp-2 font-sans text-[0.9375rem] font-medium leading-snug text-ink">
            <Link
              href={`/products/${product.id}`}
              aria-describedby={`${base}-brand ${base}-meta`}
              className="outline-none transition-colors duration-150 after:absolute after:inset-0 after:rounded-3xl after:content-[''] group-hover:text-brand-700"
            >
              {product.title}
            </Link>
          </h3>
          <div id={`${base}-meta`} className="contents">
            {size || product.unit_price ? (
              <p className="mt-1 truncate text-xs text-muted">
                {size}
                {size && product.unit_price ? <span aria-hidden="true"> · </span> : null}
                {product.unit_price ? <span className="sr-only">, </span> : null}
                {product.unit_price}
              </p>
            ) : null}
            <RatingBadge average={product.rating_average} count={product.rating_count} className="mt-1.5" />
            <TagBadges tags={product.tags} max={3} className="mt-2" />
            <div className="mt-auto flex flex-wrap items-baseline justify-between gap-x-2 gap-y-0.5 pt-3">
              <p className="whitespace-nowrap tabular-nums text-ink">
                {multiVariant ? <span className="mr-1 text-xs font-medium text-muted">From</span> : null}
                <span className="text-lg font-semibold">{formatMoney(price, product.currency)}</span>
              </p>
              {!product.in_stock ? (
                <p className="inline-flex items-center gap-1.5 whitespace-nowrap text-xs font-medium text-danger-700">
                  <span aria-hidden="true" className="size-1.5 rounded-full bg-danger-600" />
                  Out of stock
                </p>
              ) : choose ? (
                <span className="sr-only">In stock. Choose options on the product page.</span>
              ) : !canAdd ? (
                <p className="inline-flex items-center gap-1.5 whitespace-nowrap text-xs font-medium text-success-700">
                  <span aria-hidden="true" className="size-1.5 rounded-full bg-success-600" />
                  In stock
                </p>
              ) : null}
            </div>
          </div>
          {canAdd && product.default_variant_id ? (
            <QuickAdd
              variantId={product.default_variant_id}
              productTitle={product.title}
              variantName={multiVariant ? product.default_variant_name : null}
              className="mt-2.5"
            />
          ) : choose ? (
            // Not a second link: the title link already covers the card, so this is its visible
            // call to action (clicks pass through to it), and the link's description says why.
            <span
              aria-hidden="true"
              className={buttonClasses(
                "outline",
                "sm",
                "pointer-events-none mt-2.5 h-10 w-full group-hover:bg-neutral-50 group-hover:ring-neutral-400",
              )}
            >
              Choose options
              <ArrowRightIcon className="size-4" />
            </span>
          ) : null}
        </div>
      </div>
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
  quickAdd = true,
}: {
  products: ProductSummary[];
  label: string;
  className?: string;
  /** Number the cards (#1, #2…) for ranked lists such as "Top rated". */
  ranked?: boolean;
  quickAdd?: boolean;
}) {
  const idPrefix = `pg-${slug(label) || "grid"}`;
  return (
    <ul
      aria-label={label}
      className={cn("grid grid-cols-2 gap-x-4 gap-y-8 sm:grid-cols-3 lg:grid-cols-4 lg:gap-x-6 lg:gap-y-10", className)}
    >
      {products.map((p, i) => (
        <ProductCard
          key={p.id}
          product={p}
          priority={i < 4}
          idPrefix={idPrefix}
          rank={ranked ? i + 1 : undefined}
          quickAdd={quickAdd}
        />
      ))}
    </ul>
  );
}
