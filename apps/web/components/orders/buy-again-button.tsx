"use client";

import { CheckIcon, RefreshIcon } from "@/components/icons";
import { Button } from "@/components/ui/button";
import { browserApi, errorMessage, goToSignIn } from "@/lib/api-browser";
import { useCart, useSetCartItem } from "@/lib/cart-query";
import { cn } from "@/lib/cn";
import type { CartOut } from "@ai-commerce/contracts";
import Link from "next/link";
import { useState } from "react";

type Outcome = {
  added: { title: string; quantity: number }[];
  unavailable: { title: string; reason: string }[];
};

type State = { kind: "idle" } | { kind: "done"; outcome: Outcome } | { kind: "error"; message: string };

const listFormat = new Intl.ListFormat("en-US", { style: "long", type: "conjunction" });

function summary({ added, unavailable }: Outcome): string {
  const parts: string[] = [];
  if (added.length > 0) {
    const count = added.reduce((n, a) => n + a.quantity, 0);
    parts.push(`Added ${count} ${count === 1 ? "item" : "items"} to your cart.`);
  } else {
    parts.push("Nothing was added to your cart.");
  }
  if (unavailable.length > 0) {
    parts.push(
      `Not available: ${listFormat.format(unavailable.map((u) => `${u.title} (${u.reason.replace(/\.$/, "").toLowerCase()})`))}.`,
    );
  }
  return parts.join(" ");
}

/**
 * "Buy again" for a whole order in the list: reads the order's lines from the API (the list only
 * has a summary), then adds each item still sold, in the quantity bought, on top of what's already
 * in the cart. The cart API decides availability; whatever it refuses is named in the result.
 */
export function BuyAgainButton({ orderId, orderNumber }: { orderId: string; orderNumber: string }) {
  const { data: cart } = useCart();
  const setItem = useSetCartItem();
  const [busy, setBusy] = useState(false);
  const [state, setState] = useState<State>({ kind: "idle" });

  async function buyAgain() {
    setBusy(true);
    setState({ kind: "idle" });
    try {
      const result = await browserApi.GET("/v1/orders/{order_id}", { params: { path: { order_id: orderId } } });
      if (result.response.status === 401) return goToSignIn();
      if (!result.data) throw new Error(errorMessage(result.error, "Couldn't load that order. Please try again."));

      const outcome: Outcome = { added: [], unavailable: [] };
      let latest: CartOut | undefined = cart;
      for (const line of result.data.lines) {
        if (!line.product_id) {
          outcome.unavailable.push({ title: line.product_title, reason: "No longer sold" });
          continue;
        }
        const current = latest?.items.find((i) => i.variant_id === line.variant_id)?.quantity ?? 0;
        try {
          latest = await setItem.mutateAsync({ variantId: line.variant_id, quantity: current + line.quantity });
          outcome.added.push({ title: line.product_title, quantity: line.quantity });
        } catch (e) {
          outcome.unavailable.push({
            title: line.product_title,
            reason: e instanceof Error && e.message ? e.message : "Unavailable",
          });
        }
      }
      setState({ kind: "done", outcome });
    } catch (e) {
      setState({ kind: "error", message: e instanceof Error ? e.message : "Something went wrong. Please try again." });
    } finally {
      setBusy(false);
    }
  }

  const done = state.kind === "done" ? state.outcome : null;
  const allAdded = done !== null && done.unavailable.length === 0 && done.added.length > 0;

  return (
    <div className="relative z-10 flex flex-col items-start gap-1 sm:items-end">
      <Button
        variant={allAdded ? "outline" : "secondary"}
        size="sm"
        loading={busy}
        onClick={buyAgain}
        className={cn(allAdded && "text-success-800 ring-success-200")}
      >
        {busy ? null : allAdded ? <CheckIcon className="size-4" /> : <RefreshIcon className="size-4" />}
        {allAdded ? "Added" : "Buy again"}
        <span className="sr-only"> (order #{orderNumber})</span>
      </Button>
      <div role="status" className="text-xs sm:text-right">
        {done ? (
          <p className={cn("max-w-72", done.unavailable.length > 0 ? "text-ink-soft" : "text-success-700")}>
            {summary(done)}{" "}
            {done.added.length > 0 ? (
              <Link
                href="/cart"
                className="font-semibold text-brand-700 underline decoration-brand-300 underline-offset-4 hover:decoration-brand-700"
              >
                View cart
              </Link>
            ) : null}
          </p>
        ) : null}
      </div>
      {state.kind === "error" ? (
        <p role="alert" className="text-xs font-medium text-danger-700">
          {state.message}
        </p>
      ) : null}
    </div>
  );
}
