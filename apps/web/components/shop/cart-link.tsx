"use client";

import { BagIcon } from "@/components/icons";
import { useCart } from "@/lib/cart-query";
import type { CartOut } from "@ai-commerce/contracts";
import Link from "next/link";
import { usePathname } from "next/navigation";

export function CartLink({ initialCart }: { initialCart: CartOut }) {
  const { data } = useCart(initialCart);
  const pathname = usePathname();
  const count = data?.item_count ?? 0;
  const shown = count > 99 ? "99+" : String(count);
  return (
    <Link
      href="/cart"
      aria-current={pathname === "/cart" ? "page" : undefined}
      className="group/cart relative inline-flex min-h-11 min-w-11 items-center justify-center gap-2 rounded-full px-2.5 text-sm font-semibold text-ink transition-colors duration-150 hover:bg-sunken aria-[current=page]:bg-brand-50 aria-[current=page]:text-brand-800 sm:px-3.5"
    >
      <span className="relative">
        <BagIcon className="size-6 transition-transform duration-300 ease-spring group-hover/cart:-rotate-6 motion-reduce:group-hover/cart:rotate-0" />
        {count > 0 ? (
          <span
            key={count}
            aria-hidden="true"
            className="absolute -right-2 -top-1.5 grid h-5 min-w-5 animate-pop place-items-center rounded-full bg-brand-600 px-1.5 text-[0.6875rem] font-semibold tabular-nums leading-none text-white shadow-sm ring-2 ring-raised"
          >
            {shown}
          </span>
        ) : null}
      </span>
      <span className="max-sm:sr-only">Cart</span>
      <span className="sr-only" aria-live="polite">
        , {count} {count === 1 ? "item" : "items"}
      </span>
    </Link>
  );
}
