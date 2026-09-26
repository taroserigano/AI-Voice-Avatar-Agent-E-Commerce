"use client";

import { CartIcon, CheckIcon } from "@/components/icons";
import { Button, ButtonLink } from "@/components/ui/button";
import { PillSelect } from "@/components/reviews/pill-select";
import { Notice } from "@/components/ui/notice";
import { CART_KEY, useSetCartItem } from "@/lib/cart-query";
import { cn } from "@/lib/cn";
import { formatMoney } from "@/lib/format";
import type { CartOut, ProductDetail } from "@ai-commerce/contracts";
import { useQueryClient } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";

/** Variant attribute key → a friendlier legend ("color" → "Color"). */
function optionLabel(product: ProductDetail): string {
  const keys = new Set(product.variants.flatMap((v) => Object.keys(v.attributes)));
  const [key] = keys;
  if (keys.size === 1 && key) {
    return key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, " ");
  }
  return "Option";
}

function StockStatus({ inStock, available }: { inStock: boolean; available: number }) {
  const low = inStock && available <= 5;
  return (
    <p
      className={cn(
        "inline-flex items-center gap-2 text-sm font-semibold",
        !inStock ? "text-danger-700" : low ? "text-warning-700" : "text-success-700",
      )}
    >
      <span className="relative flex size-2.5" aria-hidden="true">
        {inStock && !low ? (
          <span className="absolute inline-flex size-full animate-ping rounded-full bg-success-600 opacity-40 motion-reduce:hidden" />
        ) : null}
        <span
          className={cn(
            "relative inline-flex size-2.5 rounded-full",
            !inStock ? "bg-danger-600" : low ? "bg-warning-600" : "bg-success-600",
          )}
        />
      </span>
      {inStock ? (low ? `Only ${available} left in stock` : "In stock") : "Out of stock"}
    </p>
  );
}

/**
 * Price, stock, option chips, quantity, and Add to cart. `trust` renders between the result
 * message and the price-freshness note (server-rendered policy copy).
 */
export function AddToCart({ product, trust }: { product: ProductDetail; trust?: ReactNode }) {
  const firstInStock = product.variants.find((v) => v.in_stock) ?? product.variants[0];
  const [variantId, setVariantId] = useState(firstInStock?.id ?? "");
  const [quantity, setQuantity] = useState(1);
  const [message, setMessage] = useState<{ tone: "success" | "error"; text: string }>();
  const setItem = useSetCartItem();
  const client = useQueryClient();

  const variant = product.variants.find((v) => v.id === variantId) ?? firstInStock;
  if (!variant) return null;
  const maxQty = Math.min(10, variant.available);
  const prices = new Set(product.variants.map((v) => v.price_minor));

  async function add() {
    if (!variant) return;
    setMessage(undefined);
    // PUT sets the line quantity, so add on top of what's already in the cart.
    const cart = client.getQueryData<CartOut>(CART_KEY);
    const existing = cart?.items.find((i) => i.variant_id === variant.id)?.quantity ?? 0;
    try {
      await setItem.mutateAsync({ variantId: variant.id, quantity: Math.min(existing + quantity, maxQty) });
      setMessage({ tone: "success", text: `Added to cart: ${product.title}${product.variants.length > 1 ? ` (${variant.name})` : ""}.` });
    } catch (e) {
      setMessage({ tone: "error", text: e instanceof Error ? e.message : "Couldn't add to cart." });
    }
  }

  return (
    <div>
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-2">
        <p className="font-display text-4xl font-semibold tabular-nums tracking-tight text-ink">
          {formatMoney(variant.price_minor, variant.currency)}
          {prices.size > 1 ? <span className="sr-only"> for {variant.name}</span> : null}
        </p>
        <StockStatus inStock={variant.in_stock} available={variant.available} />
      </div>

      {product.variants.length > 1 ? (
        <fieldset className="mt-7">
          <legend className="text-sm font-semibold text-ink">
            {optionLabel(product)}: <span className="font-normal text-muted">{variant.name}</span>
          </legend>
          <div className="mt-3 flex flex-wrap gap-2">
            {product.variants.map((v) => (
              <label
                key={v.id}
                className={cn(
                  "group relative flex min-h-11 cursor-pointer select-none items-center gap-2 rounded-full bg-raised px-4 text-sm font-medium text-ink",
                  "ring-1 ring-inset transition-[box-shadow,background-color,color] duration-150 ease-snappy",
                  "has-checked:bg-brand-50 has-checked:text-brand-900 has-checked:ring-2 has-checked:ring-brand-600",
                  "has-focus-visible:outline-2 has-focus-visible:outline-offset-2 has-focus-visible:outline-focus",
                  v.in_stock
                    ? "ring-line-strong hover:ring-neutral-500"
                    : "text-muted ring-line-strong [background-image:repeating-linear-gradient(135deg,transparent_0_6px,var(--color-neutral-100)_6px_7px)]",
                )}
              >
                <input
                  type="radio"
                  name="variant"
                  value={v.id}
                  checked={v.id === variant.id}
                  onChange={() => {
                    setVariantId(v.id);
                    setQuantity(1);
                    setMessage(undefined);
                  }}
                  className="sr-only"
                />
                <CheckIcon className="hidden size-4 text-brand-700 group-has-checked:block" />
                <span className={v.in_stock ? undefined : "line-through decoration-neutral-400"}>{v.name}</span>
                {!v.in_stock ? <span className="text-xs">(out of stock)</span> : null}
              </label>
            ))}
          </div>
        </fieldset>
      ) : null}

      {variant.in_stock ? (
        <div className="mt-7 flex items-end gap-3">
          <div className="w-24 shrink-0">
            <label htmlFor="quantity" className="block text-sm font-semibold text-ink">
              Quantity
            </label>
            <PillSelect
              id="quantity"
              value={quantity}
              onChange={(e) => setQuantity(Number(e.target.value))}
              wrapperClassName="mt-2"
              className="min-h-13 pl-5 tabular-nums"
            >
              {Array.from({ length: maxQty }, (_, i) => i + 1).map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </PillSelect>
          </div>
          <Button size="lg" onClick={add} loading={setItem.isPending} className="min-w-0 flex-1">
            {setItem.isPending ? null : <CartIcon className="size-5" />}
            {setItem.isPending ? "Adding…" : "Add to cart"}
          </Button>
        </div>
      ) : (
        <p className="mt-7 rounded-2xl bg-sunken px-5 py-4 text-sm text-ink-soft">
          {product.variants.length > 1
            ? `This option is out of stock right now. ${product.variants.some((v) => v.in_stock) ? "Try another option above." : "Check back soon."}`
            : "This item is out of stock right now. Check back soon."}
        </p>
      )}

      <div aria-live="polite" className="empty:hidden [&:not(:empty)]:mt-4">
        {message ? (
          <Notice
            tone={message.tone}
            className="animate-fade-in"
            action={
              message.tone === "success" ? (
                <ButtonLink href="/cart" variant="outline" size="sm">
                  View cart
                </ButtonLink>
              ) : undefined
            }
          >
            {message.text}
          </Notice>
        ) : null}
      </div>

      {trust}

      <p className="mt-5 text-xs text-muted">
        Price and stock checked{" "}
        {/* Server and browser may be in different time zones; the browser's rendering wins. */}
        <time dateTime={product.as_of} suppressHydrationWarning>
          {new Date(product.as_of).toLocaleTimeString("en-US")}
        </time>
        . The final price is confirmed at checkout.
      </p>
    </div>
  );
}
