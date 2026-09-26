import { Logo } from "@/components/logo";
import type { CartOut, CategoryOut, UserOut } from "@ai-commerce/contracts";
import Link from "next/link";
import { CartLink } from "./cart-link";
import { SignOutButton } from "./sign-out-button";

export function Header({
  user,
  categories,
  cart,
  query,
}: {
  user: UserOut;
  categories: CategoryOut[];
  cart: CartOut;
  query?: string;
}) {
  return (
    <header className="bg-brand-700 text-white">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-6 gap-y-3 px-4 py-3">
        <Logo inverted />
        <form action="/search" method="get" role="search" className="order-last flex w-full flex-1 md:order-none md:w-auto">
          <label htmlFor="site-search" className="sr-only">
            Search products
          </label>
          <input
            id="site-search"
            name="q"
            type="search"
            defaultValue={query}
            placeholder="Search everything at Larkspur"
            className="min-h-11 w-full rounded-l-full border-0 bg-white px-5 text-ink placeholder:text-stone-500"
          />
          <button
            type="submit"
            className="min-h-11 rounded-r-full bg-accent-400 px-5 font-semibold text-ink hover:bg-amber-300"
          >
            Search
          </button>
        </form>
        <nav aria-label="Account" className="ml-auto flex items-center gap-1">
          <Link href="/stores" className="flex min-h-11 items-center rounded-full px-3 font-semibold hover:bg-brand-900">
            Stores
          </Link>
          <details className="relative">
            <summary className="flex min-h-11 cursor-pointer list-none items-center rounded-full px-3 font-semibold hover:bg-brand-900">
              <span className="sr-only">Account menu for </span>
              Hi, {user.display_name.split(" ")[0]}
            </summary>
            <div className="absolute right-0 z-20 mt-2 w-48 rounded-xl border border-line bg-white p-2 text-ink shadow-lg">
              <Link href="/orders" className="block rounded-lg px-3 py-2 hover:bg-stone-100">
                Orders &amp; returns
              </Link>
              <SignOutButton className="block w-full rounded-lg px-3 py-2 text-left hover:bg-stone-100" />
            </div>
          </details>
          <CartLink initialCart={cart} />
        </nav>
      </div>
      <nav aria-label="Departments" className="bg-brand-800">
        <ul className="mx-auto flex max-w-7xl gap-1 overflow-x-auto px-4 py-1 text-sm">
          {categories.map((c) => (
            <li key={c.slug}>
              <Link
                href={`/c/${c.slug}`}
                className="inline-flex min-h-10 items-center whitespace-nowrap rounded-full px-3 hover:bg-brand-900"
              >
                {c.name}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </header>
  );
}
