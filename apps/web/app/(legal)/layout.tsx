import { ArrowLeftIcon, EyeIcon, NotebookIcon, PackageIcon, ReturnIcon, ShieldCheckIcon } from "@/components/icons";
import { Logo } from "@/components/logo";
import { buttonClasses } from "@/components/ui/button";
import { containerClasses } from "@/components/ui/container";
import { SESSION_COOKIE } from "@/lib/api-server";
import { cookies } from "next/headers";
import Link from "next/link";

/**
 * Public legal pages. Each page wraps its content in `data-doc="<slug>"`; the sidebar uses
 * `:has()` to highlight the current document without needing a client component.
 */
const DOCS = [
  {
    slug: "returns-policy",
    href: "/returns-policy",
    label: "Returns & refunds",
    Icon: ReturnIcon,
    current: "group-has-[[data-doc=returns-policy]]/legal:bg-raised group-has-[[data-doc=returns-policy]]/legal:text-brand-800 group-has-[[data-doc=returns-policy]]/legal:shadow-sm group-has-[[data-doc=returns-policy]]/legal:ring-line",
  },
  {
    slug: "privacy",
    href: "/privacy",
    label: "Privacy",
    Icon: ShieldCheckIcon,
    current: "group-has-[[data-doc=privacy]]/legal:bg-raised group-has-[[data-doc=privacy]]/legal:text-brand-800 group-has-[[data-doc=privacy]]/legal:shadow-sm group-has-[[data-doc=privacy]]/legal:ring-line",
  },
  {
    slug: "terms",
    href: "/terms",
    label: "Terms",
    Icon: NotebookIcon,
    current: "group-has-[[data-doc=terms]]/legal:bg-raised group-has-[[data-doc=terms]]/legal:text-brand-800 group-has-[[data-doc=terms]]/legal:shadow-sm group-has-[[data-doc=terms]]/legal:ring-line",
  },
  {
    slug: "accessibility",
    href: "/accessibility",
    label: "Accessibility",
    Icon: EyeIcon,
    current: "group-has-[[data-doc=accessibility]]/legal:bg-raised group-has-[[data-doc=accessibility]]/legal:text-brand-800 group-has-[[data-doc=accessibility]]/legal:shadow-sm group-has-[[data-doc=accessibility]]/legal:ring-line",
  },
] as const;

const footerLink =
  "inline-flex min-h-11 items-center font-medium text-brand-700 underline decoration-brand-300 underline-offset-4 hover:decoration-brand-700";

export default async function LegalLayout({ children }: { children: React.ReactNode }) {
  // The pages stay public. The session cookie only swaps the header and footer links; it isn't
  // verified here (the store checks it on the next page), and nothing private is shown.
  const signedIn = Boolean((await cookies()).get(SESSION_COOKIE)?.value);
  return (
    <div className="group/legal relative flex min-h-screen flex-col bg-canvas">
      <header className="sticky top-0 z-40 border-b border-line bg-raised/85 backdrop-blur-xl backdrop-saturate-150">
        <div className={containerClasses("default", "flex h-16 items-center justify-between gap-4")}>
          <Logo />
          {signedIn ? (
            <nav aria-label="Store" className="flex items-center gap-1 sm:gap-2">
              <Link href="/orders" className={buttonClasses("ghost", "sm", "max-sm:hidden")}>
                <PackageIcon className="size-4" />
                Orders &amp; returns
              </Link>
              <Link href="/" className={buttonClasses("outline", "sm")}>
                <ArrowLeftIcon className="size-4" />
                Back to the store
              </Link>
            </nav>
          ) : (
            <Link href="/sign-in" className={buttonClasses("outline", "sm")}>
              Sign in
            </Link>
          )}
        </div>
      </header>

      {/* soft brand wash behind the title area */}
      <div aria-hidden="true" className="pointer-events-none absolute inset-x-0 top-16 h-72 bg-mesh-light opacity-70 mask-[linear-gradient(to_bottom,black,transparent)]" />

      <div className={containerClasses("default", "relative flex-1 pb-20 pt-8 sm:pt-14 lg:grid lg:grid-cols-[13rem_minmax(0,1fr)] lg:gap-14")}>
        <nav aria-label="Legal documents" className="lg:sticky lg:top-28 lg:self-start">
          <p className="hidden text-xs font-semibold uppercase tracking-eyebrow text-muted lg:block">Legal</p>
          <ul className="-mx-1 flex gap-1 overflow-x-auto p-1 scrollbar-none lg:mx-0 lg:mt-3 lg:flex-col lg:p-0">
            {DOCS.map(({ slug, href, label, Icon, current }) => (
              <li key={slug}>
                <Link
                  href={href}
                  className={`flex min-h-11 items-center gap-2.5 whitespace-nowrap rounded-full px-4 text-sm font-medium text-ink-soft ring-1 ring-transparent transition-colors hover:bg-raised hover:text-ink lg:rounded-xl lg:px-3 ${current}`}
                >
                  <Icon className="size-4.5 shrink-0" />
                  {label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        <main id="main" className="mt-8 min-w-0 lg:mt-0">
          {children}
        </main>
      </div>

      <footer className="border-t border-line bg-raised">
        <div className={containerClasses("default", "flex flex-wrap items-center justify-between gap-4 py-6 text-sm text-muted")}>
          <p>© Larkspur (demo store). A portfolio demonstration, not a real store.</p>
          {signedIn ? (
            <p className="flex flex-wrap gap-x-5">
              <Link href="/" className={footerLink}>
                Back to the store
              </Link>
              <Link href="/help" className={footerLink}>
                Help center
              </Link>
            </p>
          ) : (
            <Link href="/sign-in" className={footerLink}>
              Sign in to shop
            </Link>
          )}
        </div>
      </footer>
    </div>
  );
}
