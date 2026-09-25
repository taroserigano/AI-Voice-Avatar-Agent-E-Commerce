import { Logo } from "@/components/logo";
import { getAuthConfig } from "@/lib/api-server";
import Link from "next/link";

export default async function AuthLayout({ children }: { children: React.ReactNode }) {
  const config = await getAuthConfig();
  return (
    <div className="flex min-h-screen flex-col lg:flex-row">
      <aside className="bg-brand-800 px-6 py-8 text-white lg:flex lg:w-[44%] lg:flex-col lg:justify-between lg:px-12 lg:py-12">
        <Logo inverted />
        <div className="mt-8 max-w-md lg:mt-0">
          <h2 className="text-3xl font-extrabold leading-tight lg:text-4xl">
            Everyday essentials, and a helper that actually helps.
          </h2>
          <p className="mt-4 text-brand-100">
            Shop headphones to hiking socks, then track orders and start returns by typing or
            just asking out loud. Sign in or create an account to start browsing.
          </p>
        </div>
        <p className="mt-8 hidden text-sm text-brand-100 lg:block">
          A portfolio demo store. Payments run in Stripe test mode; no real charges.
        </p>
      </aside>

      <main id="main" className="flex flex-1 flex-col items-center justify-center px-4 py-10">
        <div className="w-full max-w-md">
          {config.development_sign_in ? (
            <div
              className="mb-6 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-950"
              role="note"
              aria-label="Development sign-in"
            >
              <p className="font-semibold">Development sign-in</p>
              <p className="mt-1">
                Local test accounts only. Try <code className="font-mono">alice@example.com</code> /{" "}
                <code className="font-mono">alice-dev-password</code> or{" "}
                <code className="font-mono">bob@example.com</code> /{" "}
                <code className="font-mono">bob-dev-password</code>.
              </p>
            </div>
          ) : null}
          {children}
          <nav aria-label="Legal" className="mt-10 flex flex-wrap gap-x-4 gap-y-2 text-sm text-muted">
            <Link className="underline underline-offset-2 hover:text-ink" href="/privacy">
              Privacy
            </Link>
            <Link className="underline underline-offset-2 hover:text-ink" href="/terms">
              Terms
            </Link>
            <Link className="underline underline-offset-2 hover:text-ink" href="/accessibility">
              Accessibility
            </Link>
          </nav>
        </div>
      </main>
    </div>
  );
}
