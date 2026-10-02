import { ChevronDownIcon, DepartmentIcon, ShieldCheckIcon } from "@/components/icons";
import { Logo } from "@/components/logo";
import { containerClasses } from "@/components/ui/container";
import type { CategoryOut } from "@ai-commerce/contracts";
import Link from "next/link";

const linkClasses =
  "group inline-flex min-h-11 items-center gap-2.5 rounded-md text-sm text-brand-200 transition-colors duration-150 hover:text-white lg:min-h-9";

type FooterLink = { href: string; label: string };

const SERVICE_LINKS: FooterLink[] = [
  { href: "/help", label: "Help center" },
  { href: "/support", label: "Support (Xena)" },
  { href: "/stores", label: "Stores" },
  { href: "/returns-policy", label: "Returns & refunds" },
  { href: "/help/returns", label: "How returns work" },
  { href: "/help#shipping", label: "Shipping" },
];

const ACCOUNT_LINKS: FooterLink[] = [
  { href: "/orders", label: "Orders & returns" },
  { href: "/activity", label: "Activity" },
  // Lowercase "cart": the header's "Cart" link stays the one obvious cart control.
  { href: "/cart", label: "Your cart" },
  { href: "/search", label: "Search" },
];

const POLICY_LINKS: FooterLink[] = [
  { href: "/privacy", label: "Privacy" },
  { href: "/terms", label: "Terms" },
  { href: "/accessibility", label: "Accessibility" },
  { href: "/sitemap", label: "Site map" },
];

const headingClasses = "font-sans text-xs font-semibold uppercase tracking-eyebrow text-accent-300";

function LinkColumn({ id, title, links }: { id: string; title: string; links: FooterLink[] }) {
  return (
    <div>
      <h2 id={id} className={headingClasses}>
        {title}
      </h2>
      <ul aria-labelledby={id} className="mt-3 lg:mt-4">
        {links.map((l) => (
          <li key={l.href}>
            <Link href={l.href} className={linkClasses}>
              {l.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

function DepartmentLinks({ categories }: { categories: CategoryOut[] }) {
  return (
    <ul className="mt-3 grid grid-cols-2 gap-x-6 lg:mt-4">
      {categories.map((c) => (
        <li key={c.slug}>
          <Link href={`/c/${c.slug}`} className={linkClasses}>
            <DepartmentIcon slug={c.slug} className="size-4 shrink-0 text-brand-300 transition-colors group-hover:text-accent-300" />
            {c.name}
          </Link>
        </li>
      ))}
    </ul>
  );
}

/**
 * Site-wide footer: brand column, customer service, account and policy links, and every
 * department. On phones the department list folds into a disclosure to keep the footer short.
 */
export function Footer({ categories }: { categories: CategoryOut[] }) {
  return (
    <footer className="relative isolate mt-20 overflow-hidden bg-inverse text-brand-200 focus-inverse sm:mt-24">
      {/* soft violet glow + hairline sheen along the top edge (decorative) */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(55%_70%_at_100%_0%,rgb(125_100_239/0.28),transparent_70%),radial-gradient(40%_60%_at_0%_100%,rgb(67_41_149/0.55),transparent_70%)]"
      />
      <div aria-hidden="true" className="absolute inset-x-0 top-0 h-px bg-linear-to-r from-transparent via-brand-400/50 to-transparent" />

      <div
        className={containerClasses(
          "default",
          "grid gap-10 py-12 sm:gap-12 sm:py-16 lg:grid-cols-[minmax(0,17rem)_1fr] lg:gap-14 lg:py-20",
        )}
      >
        <div>
          <Logo inverted />
          <p className="mt-4 max-w-xs text-base leading-relaxed text-brand-200 sm:mt-5">
            Groceries, household basics, and everyday essentials for every room and every errand.
          </p>
          <p className="mt-5 inline-flex items-start gap-2.5 rounded-2xl bg-white/5 px-4 py-3 text-sm leading-relaxed text-brand-200 ring-1 ring-inset ring-white/10 sm:mt-6">
            <ShieldCheckIcon className="mt-0.5 size-5 text-accent-300" />
            <span>
              <strong className="font-semibold text-white">Demo store.</strong> A sandbox with test data and Stripe
              test-mode payments. Nothing ships and no real money moves.
            </span>
          </p>
        </div>

        <nav aria-label="Footer" className="grid grid-cols-2 gap-x-6 gap-y-8 sm:grid-cols-3 sm:gap-y-10 lg:grid-cols-5 lg:gap-x-8">
          <LinkColumn id="footer-service" title="Customer service" links={SERVICE_LINKS} />
          <LinkColumn id="footer-account" title="Your account" links={ACCOUNT_LINKS} />
          <LinkColumn id="footer-policies" title="Policies" links={POLICY_LINKS} />

          {/* Phones: departments fold away. */}
          <details className="group/depts col-span-2 border-t border-white/10 pt-2 sm:hidden">
            <summary className="flex min-h-12 cursor-pointer list-none items-center justify-between gap-3 [&::-webkit-details-marker]:hidden">
              <h2 className={headingClasses}>Shop {categories.length} departments</h2>
              <ChevronDownIcon className="size-5 text-brand-300 transition-transform duration-200 group-open/depts:rotate-180" />
            </summary>
            <DepartmentLinks categories={categories} />
          </details>

          {/* Tablet and up: the full list. */}
          <div className="hidden sm:col-span-3 sm:row-start-1 sm:block lg:col-span-2 lg:col-start-1">
            <h2 id="footer-shop" className={headingClasses}>
              Shop
            </h2>
            <DepartmentLinks categories={categories} />
          </div>
        </nav>
      </div>

      <div className="border-t border-white/10">
        {/* Room at the end for the floating Ask Steph button, so this last line can scroll clear of it. */}
        <div
          className={containerClasses(
            "default",
            "flex flex-col gap-2 pb-22 pt-6 text-xs text-brand-300 sm:flex-row sm:items-center sm:justify-between sm:pb-6 sm:pr-24 lg:pr-24",
          )}
        >
          <p>© Serigan Mart (demo store)</p>
          <p>Product names, prices, and sample reviews are illustrative test data.</p>
        </div>
      </div>
    </footer>
  );
}
