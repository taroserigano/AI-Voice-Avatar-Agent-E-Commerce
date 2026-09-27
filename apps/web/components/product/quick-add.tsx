"use client";

import { MinusIcon, PlusIcon } from "@/components/icons";
import { useCart, useSetCartItem } from "@/lib/cart-query";
import { cn } from "@/lib/cn";
import { useEffect, useRef, useState } from "react";

/** Line limit when the cart hasn't told us one yet (the API caps a line at 10). */
const FALLBACK_MAX = 10;

/**
 * "Add" on a product card. Once the item is in the cart it becomes a − qty + stepper that edits
 * that cart line. It adds the product's default option (the cheapest in-stock one), which the
 * card shows by name; cards only offer it when that's not a choice to make for the shopper
 * (a pack size, not a shoe size or a color: `canQuickAdd` in lib/product-display). Focus
 * follows the control that replaces the one you pressed.
 */
export function QuickAdd({
  variantId,
  productTitle,
  variantName,
  className,
}: {
  variantId: string;
  productTitle: string;
  /** Shown to screen readers so "Add" says which size goes in the cart. */
  variantName?: string | null;
  className?: string;
}) {
  const { data: cart } = useCart();
  const setItem = useSetCartItem();
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const addRef = useRef<HTMLButtonElement>(null);
  const plusRef = useRef<HTMLButtonElement>(null);
  const focusAfter = useRef<"add" | "plus" | null>(null);

  const line = cart?.items.find((i) => i.variant_id === variantId);
  const quantity = line?.quantity ?? 0;
  const max = line?.max_quantity || FALLBACK_MAX;
  const name = variantName ? `${productTitle}, ${variantName}` : productTitle;

  // Move focus once the swapped-in control exists (Add ⇄ stepper).
  useEffect(() => {
    if (focusAfter.current === "plus" && quantity > 0) plusRef.current?.focus();
    if (focusAfter.current === "add" && quantity === 0) addRef.current?.focus();
    focusAfter.current = null;
  }, [quantity]);

  async function setQuantity(next: number) {
    if (setItem.isPending) return; // aria-disabled, not disabled, so focus stays put meanwhile
    setError("");
    const hadFocus = !!document.activeElement?.closest("[data-quick-add]");
    try {
      const updated = await setItem.mutateAsync({ variantId, quantity: next });
      const now = updated.items.find((i) => i.variant_id === variantId)?.quantity ?? 0;
      // Only when one control replaces the other does focus need a new home.
      if (hadFocus && (now === 0) !== (quantity === 0)) focusAfter.current = now > 0 ? "plus" : "add";
      setStatus(now > 0 ? `${now} in cart: ${name}` : `Removed from cart: ${name}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't update your cart.");
    }
  }

  const busy = setItem.isPending;

  return (
    <div data-quick-add className={cn("relative z-10", className)}>
      {quantity === 0 ? (
        <button
          ref={addRef}
          type="button"
          onClick={() => setQuantity(1)}
          aria-disabled={busy || undefined}
          aria-label={`Add ${name} to cart`}
          className="inline-flex h-10 w-full items-center justify-center gap-1.5 rounded-full bg-brand-600 px-4 text-sm font-semibold text-white shadow-xs transition-[background-color,transform] duration-150 ease-snappy hover:bg-brand-700 active:scale-[0.97] aria-disabled:opacity-70 motion-reduce:active:scale-100"
        >
          <PlusIcon className="size-4" />
          {busy ? "Adding…" : "Add"}
        </button>
      ) : (
        <div
          role="group"
          // Not "Quantity…": that word is the PDP's quantity picker label.
          aria-label={`${name}, in your cart`}
          aria-busy={busy || undefined}
          className="flex h-10 w-full items-center justify-between rounded-full bg-brand-50 p-0.5 ring-1 ring-inset ring-brand-200"
        >
          <button
            type="button"
            onClick={() => setQuantity(quantity - 1)}
            aria-disabled={busy || undefined}
            aria-label={quantity === 1 ? `Remove ${name} from cart` : `Remove one ${name}`}
            className="grid size-9 place-items-center rounded-full bg-raised text-brand-800 shadow-xs transition-colors hover:bg-brand-100 aria-disabled:opacity-60"
          >
            <MinusIcon className="size-4" />
          </button>
          <span className="min-w-0 text-sm font-semibold tabular-nums text-brand-900">
            {quantity}
            <span className="sr-only"> in cart</span>
          </span>
          <button
            ref={plusRef}
            type="button"
            onClick={() => setQuantity(quantity + 1)}
            disabled={quantity >= max}
            aria-disabled={busy || undefined}
            aria-label={`Add one more ${name}`}
            className="grid size-9 place-items-center rounded-full bg-brand-600 text-white shadow-xs transition-colors hover:bg-brand-700 disabled:opacity-40 aria-disabled:opacity-60"
          >
            <PlusIcon className="size-4" />
          </button>
        </div>
      )}
      <span className="sr-only" aria-live="polite">
        {status}
      </span>
      {error ? (
        <p role="alert" className="mt-1.5 text-xs font-medium text-danger-700">
          {error}
        </p>
      ) : null}
    </div>
  );
}
