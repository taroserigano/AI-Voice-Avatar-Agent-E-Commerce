import { DepartmentIcon, ShieldCheckIcon } from "@/components/icons";
import { Logo } from "@/components/logo";
import { containerClasses } from "@/components/ui/container";
import type { CategoryOut } from "@ai-commerce/contracts";
import Link from "next/link";

const linkClasses =
  "group inline-flex min-h-11 items-center gap-2.5 rounded-md text-sm text-brand-200 transition-colors duration-150 hover:text-white lg:min-h-9";

const ACCOUNT_LINKS = [
  { href: "/orders", label: "Orders & returns" },
  { href: "/activity", label: "Activity" },
  // Lowercase "cart": the header's "Cart" link stays the one obvious cart control.
  { href: "/cart", label: "Your cart" },
  { href: "/search", label: "Search" },
] as const;

const HELP_LINKS = [
  { href: "/help/returns", label: "How returns work" },
  { href: "/privacy", label: "Privacy" },
  { href: "/terms", label: "Terms" },
  { href: "/accessibility", label: "Accessibility" },
  { href: "/sitemap", label: "Site map" },
] as const;

function ColumnHeading({ id, children }: { id: string; children: React.ReactNode }) {
  return (
    <h2 id={id} className="font-sans text-xs font-semibold uppercase tracking-eyebrow text-accent-300">
      {children}
    </h2>
  );
}

/** Site-wide footer: brand column plus a sitemap of every department and account/policy page. */
export function Footer({ categories }: { categories: CategoryOut[] }) {
  return (
    <footer className="relative isolate mt-20 overflow-hidden bg-inverse text-brand-200 focus-inverse sm:mt-24">
      {/* soft violet glow + hairline sheen along the top edge (decorative) */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(55%_70%_at_100%_0%,rgb(125_100_239/0.28),transparent_70%),radial-gradient(40%_60%_at_0%_100%,rgb(67_41_149/0.55),transparent_70%)]"
      />
      <div aria-hidden="true" className="absolute inset-x-0 top-0 h-px bg-linear-to-r from-transparent via-brand-400/50 to-transparent" />

      <div className={containerClasses("default", "grid gap-12 py-14 sm:py-16 lg:grid-cols-[minmax(0,20rem)_1fr] lg:gap-16 lg:py-20")}>
        <div>
          <Logo inverted />
          <p className="mt-5 max-w-xs text-base leading-relaxed text-brand-200">
            Everyday essentials for every room, every season, and every errand.
          </p>
          <p className="mt-6 inline-flex items-start gap-2.5 rounded-2xl bg-white/5 px-4 py-3 text-sm leading-relaxed text-brand-200 ring-1 ring-inset ring-white/10">
            <ShieldCheckIcon className="mt-0.5 size-5 text-accent-300" />
            <span>
              <strong className="font-semibold text-white">Demo store.</strong> A sandbox with test data and Stripe
              test-mode payments. Nothing ships and no real money moves.
            </span>
          </p>
        </div>

        <nav aria-label="Site map" className="grid grid-cols-2 gap-x-6 gap-y-10 sm:grid-cols-4 lg:gap-x-10">
          <div className="col-span-2">
            <ColumnHeading id="footer-shop">Shop</ColumnHeading>
            <ul className="mt-4 grid grid-cols-2 gap-x-6">
              {categories.map((c) => (
                <li key={c.slug}>
                  <Link href={`/c/${c.slug}`} className={linkClasses}>
                    <DepartmentIcon slug={c.slug} className="size-4 text-brand-300 transition-colors group-hover:text-accent-300" />
                    {c.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <ColumnHeading id="footer-account">Your account</ColumnHeading>
            <ul className="mt-4">
              {ACCOUNT_LINKS.map((l) => (
                <li key={l.href}>
                  <Link href={l.href} className={linkClasses}>
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <ColumnHeading id="footer-help">Help &amp; policies</ColumnHeading>
            <ul className="mt-4">
              {HELP_LINKS.map((l) => (
                <li key={l.href}>
                  <Link href={l.href} className={linkClasses}>
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </nav>
      </div>

      <div className="border-t border-white/10">
        <div
          className={containerClasses(
            "default",
            "flex flex-col gap-2 py-6 text-xs text-brand-300 sm:flex-row sm:items-center sm:justify-between",
          )}
        >
          <p>© Larkspur (demo store)</p>
          <p>Product names, prices, and sample reviews are illustrative test data.</p>
        </div>
      </div>
    </footer>
  );
}
