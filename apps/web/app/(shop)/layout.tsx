import { SessionGuard } from "@/components/session-guard";
import { Header } from "@/components/shop/header";
import { getAuthConfig, getMe, serverApi, unwrap } from "@/lib/api-server";
import Link from "next/link";

export default async function ShopLayout({ children }: { children: React.ReactNode }) {
  // getMe() redirects to sign-in if the session is missing, expired, or revoked.
  const user = await getMe();
  const api = await serverApi();
  const [categories, cart, config] = await Promise.all([
    api.GET("/v1/categories").then(unwrap),
    api.GET("/v1/cart").then(unwrap),
    getAuthConfig(),
  ]);

  return (
    <div className="flex min-h-screen flex-col">
      <SessionGuard />
      {config.development_sign_in ? (
        <p className="bg-amber-100 px-4 py-1.5 text-center text-sm text-amber-950">
          <strong>Sandbox store:</strong> development sign-in, test data, and Stripe test-mode payments.
          Nothing ships and no real money moves.
        </p>
      ) : null}
      <Header user={user} categories={categories} cart={cart} />
      <main id="main" className="mx-auto w-full max-w-7xl flex-1 px-4 py-6">
        {children}
      </main>
      <footer className="border-t border-line bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap gap-x-6 gap-y-2 px-4 py-6 text-sm text-muted">
          <span>© Larkspur (demo store)</span>
          <Link className="underline underline-offset-2 hover:text-ink" href="/privacy">
            Privacy
          </Link>
          <Link className="underline underline-offset-2 hover:text-ink" href="/terms">
            Terms
          </Link>
          <Link className="underline underline-offset-2 hover:text-ink" href="/accessibility">
            Accessibility
          </Link>
        </div>
      </footer>
    </div>
  );
}
