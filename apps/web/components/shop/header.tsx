import { ArrowRightIcon, MapIcon, SearchIcon } from "@/components/icons";
import { Logo } from "@/components/logo";
import { containerClasses } from "@/components/ui/container";
import type { CartOut, CategoryOut, UserOut } from "@ai-commerce/contracts";
import Link from "next/link";
import { AccountMenu } from "./account-menu";
import { CartLink } from "./cart-link";
import { DepartmentNav } from "./department-nav";

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
    // Sticky (with a frosted backdrop) from tablet up; on phones it scrolls away to save height.
    <header className="relative z-40 border-b border-line/80 bg-raised/85 backdrop-blur-xl backdrop-saturate-150 md:sticky md:top-0">
      <div
        className={containerClasses(
          "default",
          "flex flex-wrap items-center gap-x-2 gap-y-3 py-3 md:h-18 md:flex-nowrap md:gap-x-6 md:py-0 lg:gap-x-10",
        )}
      >
        <Logo className="-ml-1 shrink-0 px-1" />
        <form
          action="/search"
          method="get"
          role="search"
          className="order-last w-full md:order-0 md:mx-auto md:max-w-2xl md:flex-1"
        >
          <label htmlFor="site-search" className="sr-only">
            Search products
          </label>
          <div className="group/search relative">
            <SearchIcon className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-muted transition-colors group-focus-within/search:text-brand-600" />
            <input
              id="site-search"
              name="q"
              type="search"
              defaultValue={query}
              placeholder="Search everything at Larkspur"
              autoComplete="off"
              enterKeyHint="search"
              className="h-12 w-full rounded-full border border-line bg-sunken/70 pl-11 pr-14 text-base text-ink shadow-2xs inset-shadow-well transition-[background-color,border-color,box-shadow] duration-200 ease-snappy placeholder:text-muted hover:border-line-strong hover:bg-sunken focus-visible:border-brand-600 focus-visible:bg-raised focus-visible:outline-2 focus-visible:outline-transparent focus-visible:ring-4 focus-visible:ring-brand-500/20 sm:pr-28 [&::-webkit-search-cancel-button]:hidden"
            />
            <button
              type="submit"
              className="absolute right-1.5 top-1/2 inline-flex h-9 min-w-9 -translate-y-1/2 items-center justify-center gap-1.5 rounded-full bg-brand-600 px-2.5 text-sm font-semibold text-white shadow-glow inset-shadow-highlight transition-[background-color,box-shadow] duration-200 ease-snappy before:absolute before:-inset-1 before:content-[''] hover:bg-brand-700 hover:shadow-glow-lg sm:px-4"
            >
              <span className="max-sm:sr-only">Search</span>
              <ArrowRightIcon className="size-4 sm:hidden" />
            </button>
          </div>
        </form>
        <nav aria-label="Account" className="ml-auto flex shrink-0 items-center gap-0.5 md:ml-0 md:gap-1">
          <Link
            href="/stores"
            className="inline-flex min-h-11 min-w-11 items-center justify-center gap-1.5 rounded-full px-3 text-sm font-semibold text-ink transition-colors duration-200 hover:bg-sunken"
          >
            <MapIcon className="size-5 text-muted" />
            <span className="max-md:sr-only">Stores</span>
          </Link>
          <AccountMenu displayName={user.display_name} email={user.email} />
          <CartLink initialCart={cart} />
        </nav>
      </div>
      <DepartmentNav categories={categories.map((c) => ({ slug: c.slug, name: c.name }))} />
    </header>
  );
}
