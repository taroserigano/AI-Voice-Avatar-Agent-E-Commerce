"use client";

import { Button, ButtonLink } from "@/components/ui/button";
import { Notice } from "@/components/ui/notice";
import { useCart, useRemoveCartItem, useSetCartItem } from "@/lib/cart-query";
import { formatMoney } from "@/lib/format";
import type { CartOut } from "@ai-commerce/contracts";
import Link from "next/link";
import { useState } from "react";

export function CartView({ initialCart }: { initialCart: CartOut }) {
  const { data: cart } = useCart(initialCart);
  const setItem = useSetCartItem();
  const removeItem = useRemoveCartItem();
  const [status, setStatus] = useState<{ tone: "success" | "error"; text: string }>();

  if (!cart) return null;

  async function changeQuantity(variantId: string, title: string, quantity: number) {
    setStatus(undefined);
    try {
      await setItem.mutateAsync({ variantId, quantity });
      setStatus({ tone: "success", text: `Updated ${title} to ${quantity}.` });
    } catch (e) {
      setStatus({ tone: "error", text: e instanceof Error ? e.message : "Couldn't update the cart." });
    }
  }

  async function remove(itemId: string, title: string) {
    setStatus(undefined);
    try {
      await removeItem.mutateAsync(itemId);
      setStatus({ tone: "success", text: `Removed ${title}.` });
    } catch (e) {
      setStatus({ tone: "error", text: e instanceof Error ? e.message : "Couldn't remove the item." });
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold">Your cart</h1>
      <div className="mt-3 min-h-6" aria-live="polite">
        {status ? <Notice tone={status.tone}>{status.text}</Notice> : null}
      </div>
      {cart.warnings.length > 0 ? (
        <Notice tone="warning" title="Some items changed" className="mt-3">
          <ul className="list-disc pl-5">
            {cart.warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </Notice>
      ) : null}

      {cart.items.length === 0 ? (
        <div className="mt-6 rounded-2xl border border-dashed border-stone-300 bg-white p-10 text-center">
          <p className="text-lg font-semibold">Your cart is empty.</p>
          <ButtonLink href="/" variant="secondary" className="mt-4">
            Start shopping
          </ButtonLink>
        </div>
      ) : (
        <div className="mt-4 grid gap-6 lg:grid-cols-[1fr_20rem]">
          <ul aria-label="Cart items" className="divide-y divide-line rounded-2xl border border-line bg-white">
            {cart.items.map((item) => (
              <li key={item.id} className="flex gap-4 p-4">
                {/* eslint-disable-next-line @next/next/no-img-element -- local SVG placeholders */}
                <img src={item.image_path} alt="" width={96} height={96} className="h-24 w-24 rounded-xl bg-stone-100" />
                <div className="flex flex-1 flex-col gap-1">
                  <Link href={`/products/${item.product_id}`} className="font-semibold hover:underline">
                    {item.product_title}
                  </Link>
                  {item.variant_name !== "Standard" ? <p className="text-sm text-muted">{item.variant_name}</p> : null}
                  <p className="text-sm">{formatMoney(item.unit_price_minor)} each</p>
                  {!item.in_stock ? (
                    <p className="text-sm font-medium text-red-800">
                      {item.available === 0 ? "Out of stock" : `Only ${item.available} available`}
                    </p>
                  ) : null}
                  <div className="mt-2 flex flex-wrap items-center gap-3">
                    <label className="text-sm font-medium" htmlFor={`qty-${item.id}`}>
                      Quantity
                    </label>
                    <select
                      id={`qty-${item.id}`}
                      value={item.quantity}
                      disabled={setItem.isPending || item.max_quantity === 0}
                      onChange={(e) => changeQuantity(item.variant_id, item.product_title, Number(e.target.value))}
                      className="min-h-11 rounded-lg border border-stone-400 bg-white px-2"
                    >
                      {Array.from({ length: Math.max(item.max_quantity, item.quantity) }, (_, i) => i + 1).map((n) => (
                        <option key={n} value={n} disabled={n > item.max_quantity}>
                          {n}
                        </option>
                      ))}
                    </select>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => remove(item.id, item.product_title)}
                      disabled={removeItem.isPending}
                      className="underline"
                    >
                      Remove<span className="sr-only"> {item.product_title}</span>
                    </Button>
                  </div>
                </div>
                <p className="font-semibold">{formatMoney(item.line_total_minor)}</p>
              </li>
            ))}
          </ul>
          <aside aria-labelledby="summary" className="h-fit rounded-2xl border border-line bg-white p-5">
            <h2 id="summary" className="text-lg font-bold">
              Order summary
            </h2>
            <dl className="mt-3 space-y-2 text-sm">
              <div className="flex justify-between">
                <dt>Subtotal ({cart.item_count} {cart.item_count === 1 ? "item" : "items"})</dt>
                <dd className="font-semibold">{formatMoney(cart.subtotal_minor, cart.currency)}</dd>
              </div>
              <div className="flex justify-between text-muted">
                <dt>Tax</dt>
                <dd>Calculated at payment</dd>
              </div>
            </dl>
            <Button size="lg" className="mt-5 w-full" disabled aria-describedby="checkout-note">
              Checkout
            </Button>
            <p id="checkout-note" className="mt-2 text-sm text-muted">
              Checkout with Stripe test mode arrives in the next milestone.
            </p>
          </aside>
        </div>
      )}
    </div>
  );
}
