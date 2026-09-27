"use client";

import { CartIcon, CheckIcon, RefreshIcon } from "@/components/icons";
import { Button, type ButtonSize, type ButtonVariant } from "@/components/ui/button";
import { useCart, useSetCartItem } from "@/lib/cart-query";
import { cn } from "@/lib/cn";
import Link from "next/link";
import { useEffect, useState } from "react";

/**
 * Adds one of a variant to the cart (current quantity + 1, so it never overwrites what's there),
 * then says so in words: the button reads "Added" and a polite status names the product.
 * Used for "Buy again" on orders and "Add" on product suggestions.
 */
export function AddToCartButton({
  variantId,
  productTitle,
  label = "Add to cart",
  again = false,
  variant = "secondary",
  size = "sm",
  className,
  showCartLink = false,
}: {
  variantId: string;
  productTitle: string;
  /** Visible label; the product title is appended for screen readers. */
  label?: string;
  /** "Buy again" style icon instead of a cart. */
  again?: boolean;
  variant?: ButtonVariant;
  size?: ButtonSize;
  className?: string;
  /** After adding, offer a "View cart" link next to the button. */
  showCartLink?: boolean;
}) {
  const { data: cart } = useCart();
  const setItem = useSetCartItem();
  const [state, setState] = useState<{ kind: "idle" } | { kind: "added" } | { kind: "error"; message: string }>({
    kind: "idle",
  });

  useEffect(() => {
    if (state.kind !== "added") return;
    const t = window.setTimeout(() => setState({ kind: "idle" }), 4000);
    return () => window.clearTimeout(t);
  }, [state]);

  async function add() {
    setState({ kind: "idle" });
    const current = cart?.items.find((i) => i.variant_id === variantId)?.quantity ?? 0;
    try {
      await setItem.mutateAsync({ variantId, quantity: current + 1 });
      setState({ kind: "added" });
    } catch (e) {
      setState({ kind: "error", message: e instanceof Error ? e.message : "Couldn't add it to your cart." });
    }
  }

  const added = state.kind === "added";
  const Icon = added ? CheckIcon : again ? RefreshIcon : CartIcon;

  return (
    <div className={cn("flex flex-col gap-1", className)}>
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <Button
          variant={added ? "outline" : variant}
          size={size}
          loading={setItem.isPending}
          onClick={add}
          className={cn(added && "text-success-800 ring-success-200")}
        >
          {setItem.isPending ? null : <Icon className="size-4" />}
          {added ? "Added" : label}
          <span className="sr-only"> {productTitle}</span>
        </Button>
        {showCartLink && added ? (
          <Link
            href="/cart"
            className="inline-flex min-h-11 items-center text-sm font-semibold text-brand-700 underline decoration-brand-300 underline-offset-4 hover:decoration-brand-700"
          >
            View cart
          </Link>
        ) : null}
      </div>
      <span role="status" className="sr-only">
        {added ? `Added ${productTitle} to your cart.` : ""}
      </span>
      {state.kind === "error" ? (
        <p role="alert" className="text-xs font-medium text-danger-700">
          {state.message}
        </p>
      ) : null}
    </div>
  );
}
