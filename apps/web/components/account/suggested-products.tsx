"use client";

import { ArrowRightIcon } from "@/components/icons";
import { buttonClasses } from "@/components/ui/button";
import { RatingBadge } from "@/components/ui/stars";
import { cn } from "@/lib/cn";
import { formatMoney } from "@/lib/format";
import { canQuickAdd, meaningfulSize, needsOptionChoice } from "@/lib/product-display";
import type { ProductSummary } from "@ai-commerce/contracts";
import Link from "next/link";
import { AddToCartButton } from "./add-to-cart-button";

/**
 * A short row of products with a one-tap add, or a "Choose options" link for items sold in
 * sizes or colours (the same rule as the product cards: lib/product-display). Items sold in
 * packs add their default pack, which the price line names. The title is the link; the add
 * button is its own control.
 */
export function SuggestedProducts({
  id,
  title,
  description,
  products,
  className,
}: {
  id: string;
  title: string;
  description?: string;
  products: ProductSummary[];
  className?: string;
}) {
  if (products.length === 0) return null;
  return (
    <section aria-labelledby={id} className={className}>
      <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-1">
        <div>
          <h2 id={id} className="font-display text-xl font-semibold text-ink sm:text-2xl">
            {title}
          </h2>
          {description ? <p className="mt-1 text-sm text-muted">{description}</p> : null}
        </div>
      </div>
      <ul className="mt-4 grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        {products.map((p) => {
          const titleId = `${id}-${p.id}`;
          const oneTap = canQuickAdd(p);
          const choice = needsOptionChoice(p);
          const pack = !choice && p.variant_count > 1 ? meaningfulSize(p.default_variant_name) : null;
          return (
            <li
              key={p.id}
              className="flex flex-col rounded-2xl border border-line bg-raised p-2.5 shadow-xs sm:p-3"
            >
              <Link href={`/products/${p.id}`} tabIndex={-1} aria-hidden="true" className="group block overflow-hidden rounded-xl bg-sunken">
                {/* eslint-disable-next-line @next/next/no-img-element -- local SVG illustrations */}
                <img
                  src={p.image_path}
                  alt=""
                  width={640}
                  height={640}
                  loading="lazy"
                  className="aspect-square w-full object-cover transition-transform duration-500 ease-smooth group-hover:scale-[1.04] motion-reduce:group-hover:scale-100"
                />
              </Link>
              <div className="mt-2.5 flex flex-1 flex-col px-0.5">
                <Link
                  id={titleId}
                  href={`/products/${p.id}`}
                  className="line-clamp-2 text-sm font-medium leading-snug text-ink hover:text-brand-700"
                >
                  {p.title}
                </Link>
                <RatingBadge average={p.rating_average} count={p.rating_count} className="mt-1" />
                <p className="mt-1.5 text-base font-semibold tabular-nums text-ink">
                  {choice ? <span className="text-xs font-normal text-muted">From </span> : null}
                  {formatMoney(choice ? p.price_minor : (p.default_price_minor ?? p.price_minor), p.currency)}
                  {p.unit_price ? <span className="ml-1 text-xs font-normal text-muted">{p.unit_price}</span> : null}
                </p>
                {pack ? <p className="text-xs text-muted">{pack}</p> : null}
                <div className="mt-auto pt-3">
                  {oneTap && p.default_variant_id ? (
                    <AddToCartButton
                      variantId={p.default_variant_id}
                      productTitle={pack ? `${p.title}, ${pack}` : p.title}
                      label="Add"
                      className="[&_button]:w-full"
                    />
                  ) : (
                    <Link href={`/products/${p.id}`} className={cn(buttonClasses("outline", "sm"), "w-full")}>
                      {p.in_stock ? "Choose options" : "See details"}
                      <span className="sr-only"> for {p.title}</span>
                      <ArrowRightIcon className="size-4" />
                    </Link>
                  )}
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
