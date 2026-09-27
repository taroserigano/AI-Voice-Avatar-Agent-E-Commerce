"use client";

import { TruckIcon } from "@/components/icons";
import { useCart } from "@/lib/cart-query";
import { deliveryWindow, formatMoney, formatShortDate, isoDate } from "@/lib/format";
import { useState } from "react";

/** Standard shipping policy: $5.99, free at $35 after discounts (the cart reports the live numbers). */
const DEFAULT_THRESHOLD_MINOR = 3500;

/**
 * Delivery estimate and free-shipping progress for the buy box. The dates are an estimate
 * (2–5 business days from today, weekends skipped) computed in the shopper's own time zone.
 */
export function DeliveryInfo() {
  const { data: cart } = useCart();
  // Read the clock once per mount; the server and browser may disagree near midnight.
  const [today] = useState(() => new Date());
  const { start, end } = deliveryWindow(today);
  const threshold = cart?.free_shipping_threshold_minor || DEFAULT_THRESHOLD_MINOR;
  const remaining = cart?.free_shipping_remaining_minor ?? threshold;
  const hasItems = (cart?.item_count ?? 0) > 0;

  return (
    <li className="flex gap-3.5 py-4 first:pt-0 last:pb-0">
      <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-700">
        <TruckIcon className="size-5" />
      </span>
      <div className="min-w-0 text-sm">
        <p className="font-semibold text-ink">
          Arrives{" "}
          <time dateTime={isoDate(start)} suppressHydrationWarning>
            {formatShortDate(start)}
          </time>{" "}
          –{" "}
          <time dateTime={isoDate(end)} suppressHydrationWarning>
            {formatShortDate(end)}
          </time>
        </p>
        <p className="mt-0.5 text-muted">
          Estimated with standard shipping. Free shipping on orders of {formatMoney(threshold)} or more
          {hasItems ? (
            remaining > 0 ? (
              <>
                {" "}
                (you&apos;re <span className="font-semibold text-ink">{formatMoney(remaining)}</span> away).
              </>
            ) : (
              <>
                . <span className="font-semibold text-success-700">Your cart qualifies.</span>
              </>
            )
          ) : (
            "; otherwise $5.99."
          )}
        </p>
      </div>
    </li>
  );
}
