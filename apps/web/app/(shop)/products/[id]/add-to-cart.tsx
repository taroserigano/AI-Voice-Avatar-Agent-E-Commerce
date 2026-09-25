"use client";

import { Button, ButtonLink } from "@/components/ui/button";
import { Notice } from "@/components/ui/notice";
import { useSetCartItem } from "@/lib/cart-query";
import { formatMoney } from "@/lib/format";
import type { ProductDetail } from "@ai-commerce/contracts";
import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { CART_KEY } from "@/lib/cart-query";
import type { CartOut } from "@ai-commerce/contracts";

export function AddToCart({ product }: { product: ProductDetail }) {
  const firstInStock = product.variants.find((v) => v.in_stock) ?? product.variants[0];
  const [variantId, setVariantId] = useState(firstInStock?.id ?? "");
  const [quantity, setQuantity] = useState(1);
  const [message, setMessage] = useState<{ tone: "success" | "error"; text: string }>();
  const setItem = useSetCartItem();
  const client = useQueryClient();

  const variant = product.variants.find((v) => v.id === variantId) ?? firstInStock;
  if (!variant) return null;
  const maxQty = Math.min(10, variant.available);

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
    <div className="mt-4">
      <p className="text-3xl font-bold">{formatMoney(variant.price_minor, variant.currency)}</p>
      <p className={`mt-1 font-medium ${variant.in_stock ? "text-emerald-800" : "text-red-800"}`}>
        {variant.in_stock
          ? variant.available <= 5
            ? `Only ${variant.available} left in stock`
            : "In stock"
          : "Out of stock"}
      </p>

      {product.variants.length > 1 ? (
        <fieldset className="mt-5">
          <legend className="font-semibold">Option: {variant.name}</legend>
          <div className="mt-2 flex flex-wrap gap-2">
            {product.variants.map((v) => (
              <label
                key={v.id}
                className={`flex min-h-11 cursor-pointer items-center rounded-full border px-4 text-sm font-medium has-[:checked]:border-brand-700 has-[:checked]:bg-brand-50 has-[:focus-visible]:outline has-[:focus-visible]:outline-3 has-[:focus-visible]:outline-brand-600 ${v.in_stock ? "border-stone-400" : "border-dashed border-stone-300 text-muted"}`}
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
                {v.name}
                {!v.in_stock ? <span className="ml-1">(out of stock)</span> : null}
              </label>
            ))}
          </div>
        </fieldset>
      ) : null}

      {variant.in_stock ? (
        <div className="mt-5 flex flex-wrap items-end gap-3">
          <div>
            <label htmlFor="quantity" className="block text-sm font-semibold">
              Quantity
            </label>
            <select
              id="quantity"
              value={quantity}
              onChange={(e) => setQuantity(Number(e.target.value))}
              className="mt-1 min-h-11 rounded-lg border border-stone-400 bg-white px-3"
            >
              {Array.from({ length: maxQty }, (_, i) => i + 1).map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </div>
          <Button size="lg" onClick={add} disabled={setItem.isPending}>
            {setItem.isPending ? "Adding…" : "Add to cart"}
          </Button>
        </div>
      ) : null}

      <div className="mt-4 min-h-12">
        {message ? (
          <Notice tone={message.tone}>
            {message.text}{" "}
            {message.tone === "success" ? (
              <ButtonLink href="/cart" variant="ghost" size="sm" className="ml-1 underline">
                View cart
              </ButtonLink>
            ) : null}
          </Notice>
        ) : null}
      </div>
      <p className="text-xs text-muted">
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
