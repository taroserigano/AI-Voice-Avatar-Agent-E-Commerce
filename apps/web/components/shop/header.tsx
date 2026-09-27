import { HeadsetIcon, MapIcon } from "@/components/icons";
import { Logo } from "@/components/logo";
import { containerClasses } from "@/components/ui/container";
import type { CartOut, CategoryOut, UserOut } from "@ai-commerce/contracts";
import Link from "next/link";
import { Suspense } from "react";
import { AccountMenu } from "./account-menu";
import { CartLink } from "./cart-link";
import { DepartmentNav } from "./department-nav";
import { HeaderSearch, HeaderSearchForm } from "./header-search";

const iconLink =
  "inline-flex min-h-11 min-w-11 items-center justify-center gap-1.5 rounded-full px-3 text-sm font-semibold text-ink transition-colors duration-200 hover:bg-sunken";

export function Header({
  user,
  categories,
  cart,
  query,
}: {
  user: UserOut;
  categories: CategoryOut[];
  cart: CartOut;
  /** Optional: the header reads the current search from the URL itself. */
  query?: string;
}) {
  const searchClasses = "order-last w-full md:order-0 md:mx-auto md:max-w-2xl md:flex-1";
  return (
    // Sticky with a frosted backdrop. On phones it's two compact rows (logo, account, cart; then
    // search) above the department rail.
    <header className="sticky top-0 z-40 border-b border-line/80 bg-raised/85 backdrop-blur-xl backdrop-saturate-150">
      <div
        className={containerClasses(
          "default",
          "flex flex-wrap items-center gap-x-1 gap-y-1.5 pb-2 pt-1.5 md:h-18 md:flex-nowrap md:gap-x-6 md:py-0 lg:gap-x-10",
        )}
      >
        <Logo className="-ml-1 shrink-0 px-1" />
        <Suspense fallback={<HeaderSearchForm query={query} className={searchClasses} />}>
          <HeaderSearch className={searchClasses} />
        </Suspense>
        <nav aria-label="Account" className="ml-auto flex shrink-0 items-center gap-0.5 md:ml-0 md:gap-1">
          {/* On phones these two live in the account menu to keep the top row short. */}
          <Link href="/stores" className={`${iconLink} max-sm:hidden`}>
            <MapIcon className="size-5 text-muted" />
            <span className="max-md:sr-only">Stores</span>
          </Link>
          <Link href="/support" className={`${iconLink} max-sm:hidden`}>
            <HeadsetIcon className="size-5 text-muted" />
            <span className="max-md:sr-only">Support</span>
          </Link>
          <AccountMenu displayName={user.display_name} email={user.email} />
          <CartLink initialCart={cart} />
        </nav>
      </div>
      <DepartmentNav categories={categories.map((c) => ({ slug: c.slug, name: c.name }))} />
    </header>
  );
}
