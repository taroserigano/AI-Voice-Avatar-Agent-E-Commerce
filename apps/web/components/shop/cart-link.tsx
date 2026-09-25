"use client";

import { useCart } from "@/lib/cart-query";
import type { CartOut } from "@ai-commerce/contracts";
import Link from "next/link";

export function CartLink({ initialCart }: { initialCart: CartOut }) {
  const { data } = useCart(initialCart);
  const count = data?.item_count ?? 0;
  return (
    <Link
      href="/cart"
      className="relative inline-flex min-h-11 items-center gap-2 rounded-full px-3 font-semibold text-white hover:bg-brand-900"
    >
      <svg aria-hidden="true" viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M3 4h2l2.4 11.2a2 2 0 0 0 2 1.6h7.7a2 2 0 0 0 2-1.5L21 8H6.2" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="10" cy="20" r="1.5" />
        <circle cx="17" cy="20" r="1.5" />
      </svg>
      <span>Cart</span>
      <span
        className="min-w-6 rounded-full bg-accent-400 px-1.5 text-center text-sm font-bold text-ink"
        aria-live="polite"
      >
        <span className="sr-only">, </span>
        {count}
        <span className="sr-only"> {count === 1 ? "item" : "items"}</span>
      </span>
    </Link>
  );
}
